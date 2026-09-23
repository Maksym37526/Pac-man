"""Tests for pacman.maze.normalize."""

import pytest

from pacman.maze.adapter import make_maze
from pacman.maze.fake import (
    BLOCK_IN_CENTRE_5X5,
    OPEN_3X3,
    POCKET_5X5,
    open_grid,
)
from pacman.maze.model import Cell
from pacman.maze.normalize import reachable_from


def test_open_grid_is_fully_reachable() -> None:
    """Nothing is cut off in a grid with no interior walls."""
    raw = make_maze(OPEN_3X3)
    assert reachable_from(raw, Cell(0, 0)) == set(raw.passages)


def test_pocket_is_not_reached() -> None:
    """Cells walled off from the rest do not appear in the result."""
    raw = make_maze(POCKET_5X5)
    reached = reachable_from(raw, Cell(0, 0))
    assert set(raw.passages) - reached == {Cell(3, 4), Cell(4, 4)}


def test_pocket_reaches_only_itself() -> None:
    """Starting inside the pocket reaches the pocket and nothing else."""
    raw = make_maze(POCKET_5X5)
    assert reachable_from(raw, Cell(3, 4)) == {Cell(3, 4), Cell(4, 4)}


def test_blocks_are_never_reached() -> None:
    """A solid cell is not part of the reachable set."""
    raw = make_maze(BLOCK_IN_CENTRE_5X5)
    assert Cell(2, 2) not in reachable_from(raw, Cell(0, 0))


def test_start_on_a_block_reaches_nothing() -> None:
    """A start cell that is not a passage yields an empty set."""
    raw = make_maze(BLOCK_IN_CENTRE_5X5)
    assert reachable_from(raw, Cell(2, 2)) == set()


def test_start_outside_the_grid_reaches_nothing() -> None:
    """A start cell outside the grid yields an empty set."""
    raw = make_maze(OPEN_3X3)
    assert reachable_from(raw, Cell(99, 99)) == set()


def test_reachability_is_symmetric() -> None:
    """If A reaches B, then B reaches A: passages are two-way."""
    raw = make_maze(open_grid(5, 4))
    from_corner = reachable_from(raw, Cell(0, 0))
    from_far = reachable_from(raw, Cell(4, 3))
    assert from_corner == from_far


@pytest.mark.parametrize("width", [15, 21, 31, 41, 51])
def test_real_package_mazes_are_connected(width: int) -> None:
    """Every maze the package produces is one connected area."""
    generator = pytest.importorskip("mazegenerator")
    grid = generator.MazeGenerator(
        size=(width, 21), perfect=False, seed=42
    ).maze
    raw = make_maze(grid)
    assert reachable_from(raw, Cell(0, 0)) == set(raw.passages)
