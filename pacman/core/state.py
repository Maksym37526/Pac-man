"""Mutable game state for one level (Phase 6 slice).

Maze is frozen for the level; GameState is mutated sixty times a
second by core/rules.py, which is the only writer. The renderer
reads it and never mutates it.
"""

from dataclasses import dataclass, field

from pacman.core.entity import GHOST_KINDS, Entity, EntityKind
from pacman.maze.layout import MazeLayout
from pacman.maze.model import Cell, Maze


@dataclass
class GameState:
    """Everything that changes during one level.

    Attributes:
        maze: Current level's maze, shared read-only.
        player: The player entity.
        ghosts: Exactly four ghost entities.
        pacgums: Remaining ordinary pacgums, shrink as eaten.
        super_pacgums: Remaining super-pacgums.
        score: Current score, never decreases (REQ-101).
        lives: Remaining lives, from the config.
        frightened_remaining: Seconds of the edible state left,
            0.0 when inactive.
    """

    maze: Maze
    player: Entity
    ghosts: list[Entity] = field(default_factory=list)
    pacgums: set[Cell] = field(default_factory=set)
    super_pacgums: set[Cell] = field(default_factory=set)
    score: int = 0
    lives: int = 3
    frightened_remaining: float = 0.0


def new_game_state(
    maze: Maze, layout: MazeLayout, lives: int = 3
) -> GameState:
    """Build the starting state for one level.

    Args:
        maze: A normalised maze.
        layout: Where everything starts on it.
        lives: Player lives, from the config.

    Returns:
        A state with the player at the layout start, one ghost
        per corner (each ghost's home is its own corner), copied
        pacgum sets, a zero score and a cold fright timer.
    """
    ghosts = [
        Entity(
            kind=kind,
            cell=corner,
            prev_cell=corner,
            progress=0.0,
            direction=None,
            next_direction=None,
            home=corner,
        )
        for kind, corner in zip(
            GHOST_KINDS, layout.ghost_starts, strict=True
        )
    ]
    return GameState(
        maze=maze,
        player=Entity.standing_at(
            EntityKind.PLAYER, layout.player_start
        ),
        ghosts=ghosts,
        pacgums=set(layout.pacgums),
        super_pacgums=set(layout.super_pacgums),
        score=0,
        lives=lives,
        frightened_remaining=0.0,
    )
