"""View-model for the renderer: core's GameState plus run-level data.

The renderer needs more than core.state.GameState carries today:
progress through the levels, the level timer and the active cheat
toggles. Those live outside core (composition layer / ui), so they are
bundled here next to the core state instead of being copied into it.

The core state is held by reference, never duplicated: tick() mutates
it and the renderer reads the very same object, so there is no second
copy to keep in sync. When core takes over a field below, delete it
here and read it through ``core`` instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pacman.core.state import GameState
from pacman.ui.cheats import CheatState


@dataclass
class RenderGameState:
    """Everything draw_game needs for one frame.

    Attributes:
        core: The real game state, mutated only by core.rules.tick().
        level_index: Zero-based number of the current level.
        level_count: Total number of levels in the run.
        time_remaining: Seconds left on the level timer.
        cheats: Cheat toggles currently active (display only for now).
    """

    core: GameState
    level_index: int = 0
    level_count: int = 1
    time_remaining: float = 90.0
    cheats: CheatState = field(default_factory=CheatState)