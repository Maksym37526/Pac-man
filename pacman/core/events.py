"""Game events produced by one tick.

An event names something that happened, without carrying the full
state. Callers (later phases, the HUD, tests) match on these instead
of diffing the whole GameState.
"""

from enum import Enum, auto


class GameEvent(Enum):
    """Something that happened during a tick."""

    PACGUM_EATEN = auto()
    SUPER_PACGUM_EATEN = auto()
    LEVEL_CLEARED = auto()
