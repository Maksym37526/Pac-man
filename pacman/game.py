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
from pacman.data.highscore import (
    HighscoreEntry,
    insert_score,
    normalise_name,
)
from pacman.data.highscore_store import load as load_table
from pacman.data.highscore_store import save as save_table


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


def _clean_score(score: int) -> int:
    """Clamp an incoming score to something storable.

    Negative, bool or non-int values can only arrive from a
    caller bug (real game scores start at zero and only grow),
    but the boundary fixes instead of raising: same V.3
    philosophy as the name pipeline. Strictness stays one
    layer down, in insert_score.

    Args:
        score: Claimed final score of the run.

    Returns:
        The score itself when usable, 0 otherwise.
    """
    if not isinstance(score, int) or isinstance(score, bool):
        return 0
    return max(0, score)


def load_highscores(
    config: Config,
) -> tuple[HighscoreEntry, ...]:
    """Read the persistent table once, at game start (REQ-068).

    The path comes from the config (REQ-040). Loading never
    raises: any file trouble degrades to an empty table.

    Args:
        config: Validated, immutable configuration.

    Returns:
        The stored table, best first.
    """
    return load_table(config.highscore_filename)


def save_score(
    config: Config,
    entries: tuple[HighscoreEntry, ...],
    name: str,
    score: int,
) -> tuple[tuple[HighscoreEntry, ...], bool]:
    """Record one finished run and persist the table (REQ-068).

    The typed name is normalised first, and so is the score
    (anything unusable becomes 0), so B passes whatever the
    entry screen collected and whatever the run produced. This
    function never raises; strictness lives one layer down, in
    insert_score. The game continues whether or not the write
    succeeded.

    Args:
        config: Validated, immutable configuration.
        entries: Table as loaded at game start.
        name: Player name from the entry screen.
        score: Final score of the run.

    Returns:
        The updated table and whether it reached the disk.
    """
    updated = insert_score(
        entries,
        HighscoreEntry(normalise_name(name), _clean_score(score)),
    )
    return updated, save_table(config.highscore_filename, updated)
