"""Hand-built maze grids standing in for the external generator.

Everything here speaks the generator's raw format: a list of rows of
wall bit masks, exactly what MazeSource.maze returns. Nothing in this
module imports the internal Maze model, because a fake that spoke the
model would leave the adapter's bit decoding untested: an error made
twice, once when encoding and once when decoding, would cancel out and
the test would still pass.

The fakes also cover situations the real package never produces —
ragged grids, unreachable pockets, outright failure — so the adapter's
error paths can be exercised at all.
"""

from collections.abc import Collection, Iterable, Sequence

from pacman.maze.source import (
    ALL_WALLS,
    WALL_E,
    WALL_N,
    WALL_S,
    WALL_W,
    MazeSource,
)

RawCell = tuple[int, int]
"""A (col, row) position, deliberately not the model's Cell type."""

Connection = tuple[RawCell, RawCell]
"""Two orthogonally adjacent cells with an open passage between them."""

_BIT_BY_OFFSET: dict[RawCell, int] = {
    (0, -1): WALL_N,
    (1, 0): WALL_E,
    (0, 1): WALL_S,
    (-1, 0): WALL_W,
}


def _open_between(
    grid: list[list[int]], first: RawCell, second: RawCell
) -> None:
    """Clear the wall on both sides of the edge joining two cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    for cell in (first, second):
        col, row = cell
        if not (0 <= col < width and 0 <= row < height):
            raise ValueError(
                f"cell {cell} is outside the {width}x{height} grid"
            )
    offset = (second[0] - first[0], second[1] - first[1])
    if offset not in _BIT_BY_OFFSET:
        raise ValueError(f"cells {first} and {second} are not neighbours")
    back = (-offset[0], -offset[1])
    grid[first[1]][first[0]] &= ~_BIT_BY_OFFSET[offset]
    grid[second[1]][second[0]] &= ~_BIT_BY_OFFSET[back]


def build_grid(
    width: int,
    height: int,
    connections: Iterable[Connection],
    blocks: Collection[RawCell] = (),
) -> list[list[int]]:
    """Build a raw grid from a list of open passages.

    Every cell starts fully walled; each connection clears one wall bit
    on both of the two cells it joins, so an asymmetric wall cannot be
    produced by construction.

    Args:
        width: Number of columns.
        height: Number of rows.
        connections: Pairs of orthogonally adjacent cells to join.
        blocks: Cells meant to stay solid.

    Returns:
        A grid of wall bit masks, indexed grid[row][col].

    Raises:
        ValueError: On a non-positive size, a cell outside the grid, a
            pair that is not adjacent, or a cell left fully walled
            without being declared a block.
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"size {width}x{height} must be positive")
    grid = [[ALL_WALLS] * width for _ in range(height)]
    for first, second in connections:
        _open_between(grid, first, second)
    solid = frozenset(blocks)
    for col, row in solid:
        if not (0 <= col < width and 0 <= row < height):
            raise ValueError(f"block {(col, row)} is outside the grid")
        grid[row][col] = ALL_WALLS
    for row in range(height):
        for col in range(width):
            if grid[row][col] == ALL_WALLS and (col, row) not in solid:
                raise ValueError(
                    f"cell {(col, row)} is fully walled but is not listed "
                    "as a block; a decoder cannot tell the two apart"
                )
    return grid


def grid_connections(
    width: int, height: int, skip: Collection[RawCell] = ()
) -> list[Connection]:
    """Every adjacent pair in a grid, minus any pair touching ``skip``.

    Args:
        width: Number of columns.
        height: Number of rows.
        skip: Cells to leave unconnected, typically future blocks.

    Returns:
        Connections joining the whole grid into one open area.
    """
    excluded = frozenset(skip)
    pairs: list[Connection] = []
    for row in range(height):
        for col in range(width):
            if (col, row) in excluded:
                continue
            for dcol, drow in ((1, 0), (0, 1)):
                other = (col + dcol, row + drow)
                if other[0] >= width or other[1] >= height:
                    continue
                if other in excluded:
                    continue
                pairs.append(((col, row), other))
    return pairs


def open_grid(width: int, height: int) -> list[list[int]]:
    """A fully open grid: walls only around the outside."""
    return build_grid(width, height, grid_connections(width, height))


OPEN_3X3: list[list[int]] = open_grid(3, 3)
"""Smallest useful grid: every interior edge open, border closed."""

WALL_BETWEEN_3X3: list[list[int]] = build_grid(
    3,
    3,
    [
        pair
        for pair in grid_connections(3, 3)
        if pair != ((1, 1), (2, 1))
    ],
)
"""Open 3x3 with one known wall: (1, 1) is closed towards the east."""

BLOCK_IN_CENTRE_5X5: list[list[int]] = build_grid(
    5, 5, grid_connections(5, 5, skip=[(2, 2)]), blocks=[(2, 2)]
)
"""Open 5x5 whose centre cell is solid, as the '42' logo blocks are."""

POCKET_5X5: list[list[int]] = build_grid(
    5,
    5,
    [
        pair
        for pair in grid_connections(5, 5)
        if (3, 4) not in pair and (4, 4) not in pair
    ]
    + [((3, 4), (4, 4))],
)
"""Open 5x5 with (3, 4) and (4, 4) joined only to each other.

A pocket needs at least two cells: a single fully walled cell would
read back as ALL_WALLS, which the decoder treats as a solid block.
"""

RAGGED: list[list[int]] = [[0, 0, 0], [0, 0], [0, 0, 0]]
"""Rows of unequal length. The real package never returns this."""

EMPTY: list[list[int]] = []
"""No rows at all. The real package never returns this either."""


class FakeMazeSource:
    """A MazeSource returning a grid prepared in advance."""

    def __init__(self, grid: list[list[int]]) -> None:
        """Store the grid this source hands out.

        Args:
            grid: Raw grid in the generator's format.
        """
        self._grid = grid

    @property
    def maze(self) -> list[list[int]]:
        """The stored grid."""
        return self._grid


class FakeFactory:
    """A MazeSourceFactory handing out one fixed grid.

    The arguments of the last call are recorded, so a test can assert
    that the adapter passed ``perfect=False`` and a usable seed.
    """

    def __init__(self, grid: list[list[int]]) -> None:
        """Store the grid every call will return.

        Args:
            grid: Raw grid in the generator's format.
        """
        self._grid = grid
        self.calls: list[tuple[tuple[int, int], bool, int]] = []

    def __call__(
        self, *, size: tuple[int, int], perfect: bool, seed: int
    ) -> MazeSource:
        """Record the arguments and return the stored grid."""
        self.calls.append((size, perfect, seed))
        return FakeMazeSource(self._grid)


class OpenGridFactory:
    """A MazeSourceFactory building an open grid of the requested size."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        self.calls: list[tuple[tuple[int, int], bool, int]] = []

    def __call__(
        self, *, size: tuple[int, int], perfect: bool, seed: int
    ) -> MazeSource:
        """Build and return an open grid matching ``size``."""
        self.calls.append((size, perfect, seed))
        width, height = size
        return FakeMazeSource(open_grid(width, height))


class FailingFactory:
    """A MazeSourceFactory that raises instead of generating.

    The default error is one the real package actually raises on bad
    arguments, so the adapter's handling is exercised realistically.
    """

    def __init__(self, error: Exception | None = None) -> None:
        """Store the error to raise.

        Args:
            error: Exception to raise; defaults to an IndexError.
        """
        self._error = error or IndexError("list index out of range")

    def __call__(
        self, *, size: tuple[int, int], perfect: bool, seed: int
    ) -> MazeSource:
        """Always raise the stored error."""
        raise self._error


def as_rows(grid: Sequence[Sequence[int]]) -> str:
    """Render a grid as aligned numbers, for readable test failures."""
    return "\n".join(" ".join(f"{value:2d}" for value in row)
                     for row in grid)


class NoisyFactory:
    """A factory that prints to stdout, as the real package does."""

    def __init__(self, grid: list[list[int]], message: str) -> None:
        """Store the grid and the message to print."""
        self._grid = grid
        self._message = message

    def __call__(
        self, *, size: tuple[int, int], perfect: bool, seed: int
    ) -> MazeSource:
        """Print the message, then return the stored grid."""
        print(self._message)
        return FakeMazeSource(self._grid)


# For render only!

from pacman.maze.model import Cell, Direction, Maze

def tiny_maze() -> Maze:
    """3x3 open maze, centre cell blocked — enough to exercise walls + blocks."""
    width, height = 3, 3
    all_cells = [Cell(c, r) for r in range(height) for c in range(width)]
    passages: dict[Cell, frozenset[Direction]] = {}
    for cell in all_cells:
        if cell == Cell(1, 1):
            continue  # blocked centre — no passages entry
        open_dirs = set()
        for d in Direction:
            neighbour = Cell(cell.col + d.vector_x, cell.row + d.vector_y)
            in_bounds = 0 <= neighbour.col < width and 0 <= neighbour.row < height
            if in_bounds and neighbour != Cell(1, 1):
                open_dirs.add(d)
        passages[cell] = frozenset(open_dirs)
    return Maze(
        width=width,
        height=height,
        passages=passages,
        blocks=frozenset({Cell(1, 1)}),
        centre=Cell(0, 0),
        corners=(Cell(0, 0), Cell(2, 0), Cell(0, 2), Cell(2, 2)),
    )