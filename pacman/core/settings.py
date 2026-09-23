"""Static game tuning, separated from mutable state (Phase 6).

Settings describes how the game should behave. GameState describes
what is happening right now. The two have opposite lifetimes, so
they live in different modules: ``state.py`` changes sixty times a
second, this module never changes during a run.

A cheat (Phase 10) is a different Settings instance, built from the
same Config with one field overridden.

Random is deliberately not a field here. A generator mutates its
internal state on every call, so it is a dependency the game
consumes, not a setting. ``tick`` takes it as a separate argument.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GameSettings:
    """Everything ``tick`` needs that is not the state itself.

    Built once per game from Config, outside ``core``, so ``core``
    never imports ``data``.

    Attributes:
        pacgum: Points for one ordinary pacgum (no default: always
            passed explicitly, so the value cannot drift from the
            config spec table).
        super_pacgum: Points for one super-pacgum, same rule.
        ghost: Points for one edible ghost, same rule.
        player_speed: Player cells per second.
        ghost_speed: Ghost cells per second when hunting.
        frightened_speed: Ghost cells per second when edible.
        fright_duration: Seconds ghosts stay edible after a super.
        respawn_delay: Seconds an eaten ghost waits before home.
        collision_radius: Touch distance in cell units (REQ-081).
        ghost_randomness: Per-ghost chance of a random turn
            (REQ-091): ghost 1 is a pure chaser, ghosts 2-4
            increasingly erratic so they do not collapse into one.
    """

    pacgum: int
    super_pacgum: int
    ghost: int
    player_speed: float = 8.0
    ghost_speed: float = 7.0
    frightened_speed: float = 4.0
    fright_duration: float = 7.0
    respawn_delay: float = 7.0
    collision_radius: float = 0.5
    ghost_randomness: tuple[float, float, float, float] = (
        0.0,
        0.1,
        0.2,
        0.3,
    )
