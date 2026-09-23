"""Mutable game state for one level (Phase 5 slice).

Maze is frozen for the level; GameState is mutated sixty times a
second by core/rules.py, which is the only writer. The renderer
reads it and never mutates it.
"""

from dataclasses import dataclass, field

from pacman.core.entity import Entity, EntityKind
from pacman.maze.layout import MazeLayout
from pacman.maze.model import Cell, Maze


@dataclass(frozen=True)
class ScoringRules:
    """Points awarded for each edible event.

    Built once per game from Config so that core never imports
    data: Config stays behind the composition boundary.

    Attributes:
        pacgum: Points for one ordinary pacgum.
        super_pacgum: Points for one super-pacgum.
        ghost: Points for one edible ghost (used from Phase 6).
    """

    pacgum: int
    super_pacgum: int
    ghost: int


@dataclass
class GameState:
    """Everything that changes during one level.

    Attributes:
        maze: Current level's maze, shared read-only.
        player: The player entity.
        pacgums: Remaining ordinary pacgums, shrink as eaten.
        super_pacgums: Remaining super-pacgums.
        score: Current score, never decreases (REQ-101).
    """

    maze: Maze
    player: Entity
    pacgums: set[Cell] = field(default_factory=set)
    super_pacgums: set[Cell] = field(default_factory=set)
    score: int = 0


def new_game_state(maze: Maze, layout: MazeLayout) -> GameState:
    """Build the starting state for one level.

    Args:
        maze: A normalised maze.
        layout: Where everything starts on it.

    Returns:
        A state with the player standing at the layout start,
        copied pacgum sets, and a zero score.
    """
    return GameState(
        maze=maze,
        player=Entity.standing_at(
            EntityKind.PLAYER, layout.player_start
        ),
        pacgums=set(layout.pacgums),
        super_pacgums=set(layout.super_pacgums),
        score=0,
    )
