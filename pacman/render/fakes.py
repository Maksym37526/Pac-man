"""Temporary stand-ins for GameState and Entity from module_contracts.md.

These live in render/, not core/, because GameState and Entity are
owned by workstream A (core/systems) per the contract's ownership
table. This module exists only so B (render/UI) is not blocked while
core/ is still empty. Delete this module once the real types land in
pacman.core and repoint imports there.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from pacman.maze.model import Cell, Direction, Maze


class EntityMode(Enum):
    """Behavioural state of a moving entity."""
    NORMAL = auto()
    FRIGHTENED = auto()
    EATEN = auto()
    RESPAWNING = auto()


class EntityKind(Enum):
    """Which entity this is, for sprite selection."""
    PLAYER = auto()
    GHOST_1 = auto()
    GHOST_2 = auto()
    GHOST_3 = auto()
    GHOST_4 = auto()


@dataclass(frozen=True)
class Entity:
    """A moving entity's renderable state.

    The renderer computes the world position by interpolating between
    ``prev_cell`` and ``cell`` using ``progress``, then converts to
    screen coordinates. It needs nothing else from this type.

    Attributes:
        kind: Which entity this is.
        cell: The cell this entity is moving towards (or occupies, if progress is 0).
        prev_cell: The cell this entity is moving away from.
        direction: Current facing/movement direction.
        progress: Fraction travelled from prev_cell to cell, 0.0 to 1.0.
        mode: Current behavioural state.
    """
    kind: EntityKind
    cell: Cell
    prev_cell: Cell
    direction: Direction
    progress: float
    mode: EntityMode


@dataclass(frozen=True)
class GameState:
    """The single object the renderer reads. The renderer never mutates it.

    Attributes:
        maze: Current level's maze.
        player: The player entity.
        ghosts: Exactly 4 ghost entities.
        pacgums: Remaining ordinary pacgums.
        super_pacgums: Remaining power pellets.
        score: Never decreases.
        lives: Remaining lives.
        level_index: 0-based; the HUD displays level_index + 1.
        level_count: Total number of levels.
        time_remaining: Seconds left on this level, pause-compensated.
        frightened_remaining: Seconds left of the edible state; 0.0 when inactive.
    """
    maze: Maze
    player: Entity
    ghosts: list[Entity]
    pacgums: set[Cell]
    super_pacgums: set[Cell]
    score: int
    lives: int
    level_index: int
    level_count: int
    time_remaining: float
    frightened_remaining: float


def tiny_game_state(maze: Maze) -> GameState:
    """A minimal GameState for manual/smoke testing draw_game.

    Args:
        maze: The maze this state is built around; the player and
            ghosts are placed at its centre and corners.

    Returns:
        A GameState with no pacgums eaten yet, mid-game score/lives.
    """
    player = Entity(
        kind=EntityKind.PLAYER,
        cell=maze.centre,
        prev_cell=maze.centre,
        direction=Direction.RIGHT,
        progress=0.0,
        mode=EntityMode.NORMAL,
    )
    ghost_kinds = (EntityKind.GHOST_1, EntityKind.GHOST_2, EntityKind.GHOST_3, EntityKind.GHOST_4)
    ghosts = [
        Entity(
            kind=kind,
            cell=corner,
            prev_cell=corner,
            direction=Direction.UP,
            progress=0.0,
            mode=EntityMode.NORMAL,
        )
        for kind, corner in zip(ghost_kinds, maze.corners)
    ]
    return GameState(
        maze=maze,
        player=player,
        ghosts=ghosts,
        pacgums=maze.walkable_cells - {maze.centre},
        super_pacgums=set(maze.corners),
        score=0,
        lives=3,
        level_index=0,
        level_count=1,
        time_remaining=90.0,
        frightened_remaining=0.0,
    )