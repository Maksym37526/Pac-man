"""Tests for the raw grid decoder in pacman.maze.adapter."""

import pytest

from pacman.errors import MazeError
from pacman.maze.adapter import make_maze
from pacman.maze.fake import (
    BLOCK_IN_CENTRE_5X5,
    EMPTY,
    OPEN_3X3,
    RAGGED,
    WALL_BETWEEN_3X3,
    open_grid,
)
from pacman.maze.model import Cell, Direction, step
from pacman.maze.source import ALL_WALLS


def test_open_grid_decodes_every_cell() -> None:
    """An open 3x3 has nine walkable cells and no blocks."""
    raw = make_maze(OPEN_3X3)
    assert (raw.width, raw.height) == (3, 3)
    assert len(raw.passages) == 9
    assert raw.blocks == frozenset()


def test_open_centre_is_open_on_all_sides() -> None:
    """The middle cell of an open grid has all four directions."""
    raw = make_maze(OPEN_3X3)
    assert raw.passages[Cell(1, 1)] == frozenset(Direction)


def test_border_walls_are_kept() -> None:
    """The top-left corner can only go east and south."""
    raw = make_maze(OPEN_3X3)
    assert raw.passages[Cell(0, 0)] == frozenset(
        {Direction.RIGHT, Direction.DOWN}
    )


def test_known_wall_is_decoded() -> None:
    """The wall built into WALL_BETWEEN_3X3 closes (1, 1) to the east."""
    raw = make_maze(WALL_BETWEEN_3X3)
    assert Direction.RIGHT not in raw.passages[Cell(1, 1)]


def test_known_wall_is_decoded_symmetrically() -> None:
    """The same wall closes (2, 1) to the west."""
    raw = make_maze(WALL_BETWEEN_3X3)
    assert Direction.LEFT not in raw.passages[Cell(2, 1)]


def test_block_is_recognised() -> None:
    """A fully walled cell becomes a block, not a passage."""
    raw = make_maze(BLOCK_IN_CENTRE_5X5)
    assert raw.blocks == frozenset({Cell(2, 2)})
    assert Cell(2, 2) not in raw.passages


def test_every_cell_is_either_passage_or_block() -> None:
    """Passages and blocks together account for the whole grid."""
    raw = make_maze(BLOCK_IN_CENTRE_5X5)
    assert len(raw.passages) + len(raw.blocks) == raw.width * raw.height


def test_empty_grid_is_rejected() -> None:
    """A grid with no rows raises, with something to read."""
    with pytest.raises(MazeError) as info:
        make_maze(EMPTY)
    assert str(info.value) != ""


def test_zero_width_grid_is_rejected() -> None:
    """A grid whose rows have no columns raises."""
    with pytest.raises(MazeError):
        make_maze([[]])


def test_ragged_grid_is_rejected() -> None:
    """Rows of differing length raise, naming the offending row."""
    with pytest.raises(MazeError, match="row 1"):
        make_maze(RAGGED)


def test_dimensions_come_from_the_grid() -> None:
    """Width and height are read from the grid, not assumed square."""
    raw = make_maze(open_grid(7, 3))
    assert (raw.width, raw.height) == (7, 3)


def test_no_direction_leaves_the_grid() -> None:
    """Open directions never point at a cell outside the grid.

    The crafted grid opens the north and west sides of (0, 0), which the
    real package never does. The decoder must drop them.
    """
    raw = make_maze([[0, 2], [4, 6]])
    for cell, directions in raw.passages.items():
        for direction in directions:
            neighbour = step(cell, direction)
            assert 0 <= neighbour.col < raw.width
            assert 0 <= neighbour.row < raw.height


@pytest.mark.parametrize("width", [15, 21, 31, 41, 51])
def test_real_package_decodes(width: int) -> None:
    """Every width the config allows decodes without loss."""
    generator = pytest.importorskip("mazegenerator")
    grid = generator.MazeGenerator(
        size=(width, 21), perfect=False, seed=42
    ).maze
    raw = make_maze(grid)
    assert raw.width == width
    assert len(raw.passages) + len(raw.blocks) == raw.width * raw.height
    assert len(raw.blocks) == 18
    for cell, directions in raw.passages.items():
        for direction in directions:
            neighbour = step(cell, direction)
            assert 0 <= neighbour.col < raw.width
            assert 0 <= neighbour.row < raw.height


def test_decoding_matches_an_independent_reading() -> None:
    """A second, separately written reading of the grid agrees.

    Written without reusing the adapter's mapping, so a mistake made
    once in the adapter cannot be repeated here and cancel itself out.
    """
    grid = open_grid(5, 4)
    height = len(grid)
    width = len(grid[0])
    expected: dict[Cell, set[str]] = {}
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == ALL_WALLS:
                continue
            names = set()
            if not value & 1 and row > 0:
                names.add("UP")
            if not value & 2 and col < width - 1:
                names.add("RIGHT")
            if not value & 4 and row < height - 1:
                names.add("DOWN")
            if not value & 8 and col > 0:
                names.add("LEFT")
            expected[Cell(col, row)] = names
    raw = make_maze(grid)
    actual = {
        cell: {d.name for d in directions}
        for cell, directions in raw.passages.items()
    }
    assert actual == expected
