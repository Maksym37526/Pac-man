"""Temporary stand-in for the fields core.state.GameState doesn't have yet.

Entity, EntityKind, EntityMode, GHOST_KINDS come from pacman.core.entity.
core.state.GameState now carries maze/player/ghosts/pacgums/
super_pacgums/score/lives/frightened_remaining directly (Phase 6) —
RenderGameState only adds what's still missing: level tracking,
the level timer, and our cheat toggles.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pacman.core.entity import Entity, EntityKind, EntityMode, GHOST_KINDS
from pacman.core.state import GameState as CoreGameState
from pacman.ui.cheats import CheatState

__all__ = ["Entity", "EntityKind", "EntityMode", "GHOST_KINDS", "RenderGameState"]


@dataclass
class RenderGameState:
    """Extends core.state.GameState with fields core doesn't track yet.

    Attributes:
        core: The real state — the single object tick() mutates.
            maze/player/ghosts/pacgums/super_pacgums/score/lives/
            frightened_remaining are read through this.
        level_index: 0-based. Not tracked by core yet.
        level_count: Total levels. Not tracked by core yet.
        time_remaining: Seconds left on this level. Not tracked by core yet.
        cheats: Active UI-side cheat toggles (no gameplay effect yet).
    """
    core: CoreGameState
    level_index: int = 0
    level_count: int = 1
    time_remaining: float = 90.0
    cheats: CheatState = field(default_factory=CheatState)