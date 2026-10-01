"""Cheat mode for reviewers (Phase 10).

Cheats are chosen by requirement, not by habit: every command
exists so the reviewer can reach something unreachable in five
minutes of honest play (see the REQ-098 mapping in the
requirements matrix). Two kinds, never mixed:

- toggles (CheatState): enabled, invincible, fast. State that
  lives across ticks and shows in the HUD.
- one-shot commands (CheatCommand): SKIP_LEVEL, CLEAR_LEVEL,
  START_FRIGHT, LOSE_LIFE. Done once, leaving only events.

Frozen state on purpose: flipping a toggle builds a new
instance via replace, exactly like GameSettings. B can read
session.cheats for the indicator without any way to corrupt it.
"""

from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Final

from pacman.core.settings import GameSettings

CHEAT_SPEED_FACTOR: Final[float] = 2.0
"""Player speed multiplier with the fast cheat on.

Doubled, not more: faster turns the game uncontrollable and
the reviewer reads it as a bug, not a feature.
"""


class CheatCommand(Enum):
    """One-shot reviewer commands and toggle switches."""

    TOGGLE_CHEATS = auto()
    TOGGLE_INVINCIBLE = auto()
    TOGGLE_SPEED = auto()
    TOGGLE_FROZEN = auto()
    SKIP_LEVEL = auto()
    CLEAR_LEVEL = auto()
    START_FRIGHT = auto()
    LOSE_LIFE = auto()
    EXTRA_LIFE = auto()


@dataclass(frozen=True)
class CheatState:
    """Which cheat toggles are currently on.

    Attributes:
        enabled: Master switch. While off, no other command
            acts (except TOGGLE_CHEATS itself).
        invincible: Ghosts cannot catch the player; eating
            frightened ghosts still works.
        fast: Player moves CHEAT_SPEED_FACTOR times faster.
        frozen: Ghosts hold position; timers and collisions run on.
    """

    enabled: bool = False
    invincible: bool = False
    fast: bool = False
    frozen: bool = False


def effective_settings(
    base: GameSettings, cheats: CheatState
) -> GameSettings:
    """Fold the cheat toggles into the active tuning.

    Pure function: no game needed to test it. When nothing
    applies, the very same object comes back (not a copy), so
    an ``is`` comparison in tests proves no work was done.

    Args:
        base: Run tuning built from the Config, never mutated.
        cheats: Current toggle state.

    Returns:
        The settings rules.tick must use this tick.
    """
    if cheats.enabled and cheats.fast:
        return replace(
            base, player_speed=base.player_speed * CHEAT_SPEED_FACTOR
        )
    return base
