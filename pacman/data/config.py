"""Immutable config structures (T2.8).

Pure repackaging of the validated dict from T2.6; no validation here.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LevelConfig:
    width: int
    height: int
    pacgum: int
    level_max_time: int


@dataclass(frozen=True)
class Config:
    highscore_filename: str
    lives: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    seed: int
    levels: tuple[LevelConfig, ...]


def build_config(clean: dict[str, Any]) -> Config:
    """Freeze a clean config dict into immutable structures.

    Pure repackaging, no validation: the input is already clean by
    T2.6 guarantee, so a missing key here means a validator bug and
    surfaces loudly as KeyError instead of a silent default.

    Args:
        clean: Validated dict with every known key present; 'levels'
            is a list of clean per-level dicts.

    Returns:
        Immutable Config with levels as a tuple of LevelConfig.
    """
    levels = tuple(
        LevelConfig(
            width=level["width"],
            height=level["height"],
            pacgum=level["pacgum"],
            level_max_time=level["level_max_time"],
        )
        for level in clean["levels"]
    )
    return Config(
        highscore_filename=clean["highscore_filename"],
        lives=clean["lives"],
        points_per_pacgum=clean["points_per_pacgum"],
        points_per_super_pacgum=clean["points_per_super_pacgum"],
        points_per_ghost=clean["points_per_ghost"],
        seed=clean["seed"],
        levels=levels,
    )
