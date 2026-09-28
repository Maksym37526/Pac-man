"""Composition layer: build a runnable game from a Config.

The only module allowed to import both core/ and data/.
Core never imports data/ (plain data in, tuned settings out);
data/ never imports core/. This module is where the two meet:
points become GameSettings, LevelConfigs become LevelSpecs,
and everything lands in one Session with one shared Random.
"""

from random import Random

from pacman.core.session import LevelSpec, Session, new_session
from pacman.core.settings import GameSettings
from pacman.data.config import Config


def build_settings(config: Config) -> GameSettings:
    """Translate point values from Config into GameSettings.

    Args:
        config: Validated, immutable configuration.

    Returns:
        Static tuning with the configured point values.
    """
    return GameSettings(
        pacgum=config.points_per_pacgum,
        super_pacgum=config.points_per_super_pacgum,
        ghost=config.points_per_ghost,
    )


def build_level_specs(
    config: Config,
) -> tuple[LevelSpec, ...]:
    """Translate every LevelConfig into core's LevelSpec.

    Args:
        config: Validated, immutable configuration.

    Returns:
        One spec per configured level, in play order.
    """
    return tuple(
        LevelSpec(
            width=level.width,
            height=level.height,
            pacgums=level.pacgum,
            level_max_time=level.level_max_time,
        )
        for level in config.levels
    )


def new_game(
    config: Config, rng: Random | None = None
) -> Session:
    """Build a session ready for the main loop.

    Args:
        config: Validated, immutable configuration.
        rng: The run's random source; a fresh Random from
            system entropy when omitted, so levels 2+ differ
            on every launch (REQ-073). Level 1 still comes
            from the config seed directly, and tests pass a
            seeded Random explicitly for reproducibility.

    Returns:
        A session starting at level zero.
    """
    run_rng = rng if rng is not None else Random()
    return new_session(
        levels=build_level_specs(config),
        settings=build_settings(config),
        rng=run_rng,
        config_seed=config.seed,
        lives=config.lives,
    )
