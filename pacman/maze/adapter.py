# from collections.abc import Iterable
from contextlib import redirect_stdout
from io import StringIO
from typing import Final
from dataclasses import dataclass

from mazegenerator import MazeGenerator as RealMazeGenerator

from pacman.errors import MazeError
from pacman.log import get_logger
from pacman.maze.model import Cell, Direction, step
from pacman.maze.source import (
    ALL_WALLS,
    WALL_E,
    WALL_N,
    WALL_S,
    WALL_W,
    MazeSource,
    MazeSourceFactory,
)
logger = get_logger(__name__)


@dataclass(frozen=True)
class RawMaze:
    """A decoded maze, before any normalisation has been applied.

    This is the adapter's output: the generator's bit masks have already
    been translated into Cell and Direction, so nothing downstream needs
    to know how the package encodes walls.

    It is deliberately not a Maze. Maze promises a walkable centre and
    four walkable corners, and those promises can only be made after the
    normalisation step has run a flood fill and picked fallbacks. What is
    here is exactly what the grid said, with no guarantees:

    - cells may be unreachable from one another
    - the geometric centre may be a solid block
    - a corner may be a solid block

    Attributes:
        width: Number of columns, read from the grid itself rather than
            from the size that was requested.
        height: Number of rows, read the same way.
        passages: For every non-block cell, the directions open from it.
        blocks: Cells whose four walls are all closed.
    """

    width: int
    height: int
    passages: dict[Cell, frozenset[Direction]]
    blocks: frozenset[Cell]


_BIT_BY_DIRECTION: Final[dict[Direction, int]] = {
    Direction.UP: WALL_N,
    Direction.RIGHT: WALL_E,
    Direction.DOWN: WALL_S,
    Direction.LEFT: WALL_W,
}


def make_maze(grid: list[list[int]]) -> RawMaze:
    """Decode a raw generator grid into the internal representation.

    This is the only place in the project where the package's wall
    encoding is interpreted, and the only place where the two index
    orders meet: the grid is read as ``grid[row][col]`` while cells are
    built as ``Cell(col, row)``.

    Dimensions come from the grid itself. The size passed to the
    generator is a request, not a guarantee: the package can return a
    grid whose shape does not match it.

    Args:
        grid: Raw grid of wall bit masks, indexed row first.

    Returns:
        The decoded maze, without any normalisation guarantees.

    Raises:
        MazeError: If the grid has no rows, has rows of zero width, or
            has rows of differing length.
    """
    if len(grid) == 0:
        raise MazeError("Grid cannot be empty")
    if len(grid[0]) == 0:
        raise MazeError("First row cannot be empty")
    height = len(grid)
    width = len(grid[0])
    for index, line in enumerate(grid):
        if len(line) != width:
            raise MazeError(
                f"row {index} has length {len(line)}, expected {width}")
    passages: dict[Cell, frozenset[Direction]] = {}
    blocks: set[Cell] = set()
    for row in range(height):
        for col in range(width):
            cell = grid[row][col]
            cell_pos = Cell(col, row)
            if cell == ALL_WALLS:
                blocks.add(cell_pos)
            else:
                open_bits = [
                    direction
                    for direction, bit_mask in _BIT_BY_DIRECTION.items()
                    if (cell & bit_mask) == 0
                ]
                valid_direct = []
                for direction in open_bits:
                    next_cell = step(cell_pos, direction)
                    if (
                        0 <= next_cell.col < width
                        and 0 <= next_cell.row < height
                    ):
                        valid_direct.append(direction)
                passages[cell_pos] = frozenset(valid_direct)
    return RawMaze(width, height, passages, frozenset(blocks))


def call_generator(
    size: tuple[int, int],
    seed: int,
    factory: MazeSourceFactory = RealMazeGenerator,
) -> list[list[int]]:
    """ Call the package's generator and return the raw grid."""
    if seed < 1:
        raise MazeError(f"seed {seed} must be >= 1")
    buffer = StringIO()
    try:
        with redirect_stdout(buffer):
            source: MazeSource = factory(size=size, perfect=False, seed=seed)
            raw_grid = source.maze
        return raw_grid
    except Exception as e:
        raise MazeError(
            f"The maze generation failed for size {size}, seed {seed}."
        ) from e
    finally:
        output = buffer.getvalue()
        if output:
            logger.warning("Maze generator produced output:\n%s", output)


def generate_maze(
    size: tuple[int, int],
    seed: int,
    factory: MazeSourceFactory = RealMazeGenerator,
) -> RawMaze:
    """Generate a maze and decode it into the internal representation.

    Args:
        size: Requested grid size as (width, height). Treated as a
            request, not a guarantee.
        seed: Must be >= 1. The package treats 0 and negative values
            as "seed from system entropy", which makes the maze
            irreproducible.
        factory: The package's generator class, or a fake for testing.

    Returns:
        The decoded maze, without any normalisation guarantees.

    Raises:
        MazeError: If the package fails to generate a grid, or if the
            grid is malformed.
    """
    raw_grid = call_generator(size=size, seed=seed, factory=factory)
    return make_maze(raw_grid)
