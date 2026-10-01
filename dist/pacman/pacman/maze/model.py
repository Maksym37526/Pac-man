from enum import Enum
from typing import NamedTuple
from dataclasses import dataclass


class Direction(Enum):
    """Represents a direction in the maze."""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def vector_x(self) -> int:
        return self.value[0]

    @property
    def vector_y(self) -> int:
        return self.value[1]

    @property
    def opposite(self) -> "Direction":
        """The direction facing the other way."""
        return Direction((-self.vector_x, -self.vector_y))


class Cell(NamedTuple):
    """Represents a cell in the maze."""
    col: int
    row: int


def step(cell: Cell, direction: Direction) -> Cell:
    return Cell(cell.col + direction.vector_x, cell.row + direction.vector_y)


@dataclass(frozen=True)
class Maze:
    """One level's maze, immutable for the lifetime of that level.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        passages: For every walkable cell, the directions open from it.
            Blocked cells are absent from this mapping.
        blocks: Cells that are solid and cannot be entered.
        centre: Player start cell; guaranteed walkable.
        corners: Top-left, top-right, bottom-left, bottom-right;
            each guaranteed walkable.
    """

    width: int
    height: int
    passages: dict[Cell, frozenset[Direction]]
    blocks: frozenset[Cell]
    centre: Cell
    corners: tuple[Cell, Cell, Cell, Cell]

    @property
    def walkable_cells(self) -> frozenset[Cell]:
        """Every cell that is not a solid block."""
        return frozenset(self.passages)

    def is_valid(self, cell: Cell) -> bool:
        """Whether the cell lies inside the grid."""
        return 0 <= cell.col < self.width and 0 <= cell.row < self.height

    def is_blocked(self, cell: Cell) -> bool:
        """Whether the cell is solid, or outside the maze."""
        return not self.is_valid(cell) or cell not in self.passages

    def is_wall_between(self, cell: Cell, direction: Direction) -> bool:
        """Whether movement out of ``cell`` is blocked in ``direction``."""
        return direction not in self.passages.get(cell, frozenset())

    def walkable_neighbours(
        self, cell: Cell
    ) -> list[tuple[Direction, Cell]]:
        """Every direction leading out of ``cell`` and the cell it reaches."""
        return [
            (direction, step(cell, direction))
            for direction in self.passages.get(cell, frozenset())
        ]
