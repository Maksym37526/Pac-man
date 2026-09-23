"""Temporary stand-in for the full GameState the renderer needs.

Entity, EntityKind and EntityMode come from pacman.core.entity.

core.state.GameState itself is still incomplete (Phase 5 slice: no
ghosts, lives, level tracking, or timers — see pacman/core/state.py).
RenderGameState wraps the real GameState (the single object tick()
mutates) instead of duplicating its fields, and adds only what core
doesn't carry yet. Once core.state.GameState grows those fields
(ghosts in Phase 6, lives/level/timer later), delete this wrapper and
have the renderer consume core.state.GameState directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pacman.core.entity import Entity, EntityKind, EntityMode
from pacman.core.state import GameState as CoreGameState, new_game_state
from pacman.maze.layout import MazeLayout
from pacman.maze.model import Direction, Maze

__all__ = ["Entity", "EntityKind", "EntityMode", "RenderGameState", "tiny_game_state"]


@dataclass
class RenderGameState:
    """Extends core.state.GameState with fields core doesn't track yet.

    Attributes:
        core: The real state — the single object tick() mutates.
            maze/player/pacgums/super_pacgums/score are read through
            this, never duplicated here.
        ghosts: Ghost entities. Empty until core Phase 6 lands them.
        lives: Remaining lives. Not tracked by core yet.
        level_index: 0-based. Not tracked by core yet.
        level_count: Total levels. Not tracked by core yet.
        time_remaining: Seconds left on this level. Not tracked by core yet.
        frightened_remaining: Seconds of edible state left. Not tracked by core yet.
    """
    core: CoreGameState
    ghosts: list[Entity] = field(default_factory=list)
    lives: int = 3
    level_index: int = 0
    level_count: int = 1
    time_remaining: float = 90.0
    frightened_remaining: float = 0.0


def tiny_game_state(maze: Maze) -> RenderGameState:
    """A minimal RenderGameState for manual/smoke testing draw_game.

    Builds a real core.state.GameState via new_game_state, so the
    same object that tick() would mutate is what the renderer reads.
    The layout is built directly, not via gen_layout, since the test
    doesn't need randomised pacgum placement — every remaining
    walkable cell becomes a pacgum, deterministically.

    Args:
        maze: The maze this state is built around.

    Returns:
        A RenderGameState with no pacgums eaten yet.
    """
    super_pacgums = frozenset(maze.corners)
    excluded = {maze.centre} | super_pacgums
    layout = MazeLayout(
        player_start=maze.centre,
        ghost_starts=maze.corners,
        super_pacgums=super_pacgums,
        pacgums=frozenset(maze.walkable_cells - excluded),
    )
    core_state = new_game_state(maze, layout)

    ghost_kinds = (EntityKind.GHOST_1, EntityKind.GHOST_2, EntityKind.GHOST_3, EntityKind.GHOST_4)
    ghosts = []
    for kind, corner in zip(ghost_kinds, layout.ghost_starts):
        ghost = Entity.standing_at(kind, corner)
        ghost.direction = Direction.UP
        ghosts.append(ghost)

    return RenderGameState(core=core_state, ghosts=ghosts)