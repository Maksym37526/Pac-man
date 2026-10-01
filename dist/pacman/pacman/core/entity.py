"""Moving entities: the player and (from Phase 6) ghosts.

Per D1 in the module contracts, an entity holds the cell it moves
into, the cell it moves out of, and a progress value from 0.0 to 1.0
along that transition. Every game event fires at commit time.
"""

from dataclasses import dataclass
from enum import Enum, auto

from pacman.maze.model import Cell, Direction


class EntityKind(Enum):
    """Who an entity is."""

    PLAYER = auto()
    GHOST_1 = auto()
    GHOST_2 = auto()
    GHOST_3 = auto()
    GHOST_4 = auto()


class EntityMode(Enum):
    """What state an entity is in."""

    NORMAL = auto()
    FRIGHTENED = auto()
    EATEN = auto()


GHOST_KINDS: tuple[EntityKind, EntityKind, EntityKind, EntityKind] = (
    EntityKind.GHOST_1,
    EntityKind.GHOST_2,
    EntityKind.GHOST_3,
    EntityKind.GHOST_4,
)
"""The four ghost identities, in corner order (see MazeLayout)."""


@dataclass
class Entity:
    """One moving thing on the maze.

    A standing entity has ``cell == prev_cell``, ``progress == 0.0``
    and ``direction is None``. The renderer interpolates between
    ``prev_cell`` and ``cell`` using ``progress``, so equal cells
    render exactly at ``cell`` with no special case.

    Attributes:
        kind: Who this entity is.
        cell: The cell being moved into.
        prev_cell: The cell being moved out of.
        progress: How far along the transition, 0.0 to 1.0.
        direction: Current travel direction, None when standing.
        next_direction: Desired turn at the next cell boundary.
        home: Where this entity respawns (player: centre,
            ghost: its own corner).
        mode: Current entity mode.
        mode_timer: Seconds left in the current mode, used
            only for EATEN ghosts.
    """

    kind: EntityKind
    cell: Cell
    prev_cell: Cell
    progress: float
    direction: Direction | None
    next_direction: Direction | None
    home: Cell
    mode: EntityMode = EntityMode.NORMAL
    mode_timer: float = 0.0

    @classmethod
    def standing_at(cls, kind: EntityKind, cell: Cell) -> "Entity":
        """Create a standing entity at a cell.

        The entity starts at its own home: both the player and
        every ghost begin the level where they respawn.

        Args:
            kind: Who this entity is.
            cell: The cell to stand on, also stored as home.

        Returns:
            A motionless entity with no direction set.
        """
        return cls(
            kind=kind,
            cell=cell,
            prev_cell=cell,
            progress=0.0,
            direction=None,
            next_direction=None,
            home=cell,
        )

    def place_at_home(self) -> None:
        """Put the entity back at home, standing still.

        Keeps kind, home and mode: the caller sets the mode
        (and timer) that the respawn requires.
        """
        self.cell = self.home
        self.prev_cell = self.home
        self.progress = 0.0
        self.direction = None
        self.next_direction = None
