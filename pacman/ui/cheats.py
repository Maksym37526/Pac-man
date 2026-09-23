"""Cheat mode: activation and state, for peer review (subject VI.5).

The five suggested cheats from the subject: invincibility, level skip,
ghost freeze, extra lives, increased speed. Toggling state lives here
(B's side) because core doesn't carry a CheatState yet, even though
the contract's GameState already reserves a `cheats` field for it.
Once core grows real cheat *effects* (actual invincibility during
collision checks, actual speed change in movement, etc.), this
becomes the source that feeds core's CheatState instead of a
UI-only toggle with no game effect.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class CheatKind(Enum):
    """The five cheats from subject VI.5."""
    INVINCIBILITY = auto()
    GHOST_FREEZE = auto()
    INCREASED_SPEED = auto()


CHEAT_LABELS: dict[CheatKind, str] = {
    CheatKind.INVINCIBILITY: "Invincible",
    CheatKind.GHOST_FREEZE: "Ghosts Frozen",
    CheatKind.INCREASED_SPEED: "Speed Up",
}


@dataclass
class CheatState:
    """Which toggleable cheats are currently active.

    Level skip and extra lives are one-shot actions, not toggles —
    they don't belong in this set (there's nothing to display as
    "active" afterwards). Handled separately, see toggle_cheat's
    caller in the integration loop.

    Attributes:
        active: The set of currently-toggled-on cheats.
    """
    active: set[CheatKind] = field(default_factory=set)

    def toggle(self, kind: CheatKind) -> None:
        """Flip one cheat on or off."""
        if kind in self.active:
            self.active.discard(kind)
        else:
            self.active.add(kind)

    def is_active(self, kind: CheatKind) -> bool:
        """Whether a given cheat is currently on."""
        return kind in self.active