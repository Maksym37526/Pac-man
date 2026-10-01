"""View-model for the renderer: core's GameState plus UI-only data.

The renderer needs core's GameState plus the cheat toggles, which
live outside core (composition layer / ui). The core state is held
by reference, never duplicated: tick() mutates it and the renderer
reads the very same object, so there is no second copy to keep in
sync. Level progress and the timer live in core (GameState) and
are read through it, never copied here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pacman.core.cheats import CheatState
from pacman.core.state import GameState


@dataclass
class RenderGameState:
    """Everything draw_game needs for one frame.

    Attributes:
        core: The real game state, mutated only by core.rules.tick().
        cheats: Cheat toggles currently active (display only for now).
    """

    core: GameState
    cheats: CheatState = field(default_factory=CheatState)
