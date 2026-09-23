"""Key specification table for config validation (T2.5).

Single source of truth for every config key, mirroring section 3 of
project-management/module_contracts.md.

The validator (T2.6) iterates over these records; nothing is validated
by hand-written per-key conditionals. New keys are added by appending
a record, never by a new special case.

Decisions that the contracts leave open (also recorded in the
requirements matrix, section "Open decisions"):

1. Fewer than 10 levels: the last level is repeated to reach
   LEVELS_MIN_COUNT.  (See LEVELS_FILL_RULE.)
2. Levels may differ in size; no cross-level constraint.
3. Levels 2+: level seed = config seed + level index, so changing
   the config seed reshapes every maze deterministically.
4. pacgum upper bound is the number of walkable cells, known only
   after maze generation; the record below marks it DEFERRED and the
   maze adapter supplies the bound at level load time.
5. Comment styles (REQ-037): decided in the lexer (T2.3), not here.
"""

from dataclasses import dataclass
from typing import Any, Optional

# Normalisation kinds (KeySpec.normalize)
CLAMP = "clamp"  # force into [min, max]
ODD = "odd"  # clamp, then round up to next odd (width)
NONE = "none"  # no normalisation (strings, lists with special handling)
DEFERRED = "deferred"  # upper bound set later by maze adapter (pacgum)
LEVELS = "levels"  # list handled by LEVEL_SPEC + fill rule

# What to do when a value is invalid
ON_BAD_CLAMP = "clamp"  # wrong type -> default; out of range -> clamp
ON_BAD_DEFAULT = "default"  # any invalid value -> use default

# Cross-key decisions
LEVELS_MIN_COUNT = 10
LEVELS_FILL_RULE = "repeat_last"


@dataclass(frozen=True)
class KeySpec:
    """One row of the config specification table."""

    key: str
    type: type
    default: Any
    min: Optional[int] = None
    max: Optional[int] = None
    normalize: str = CLAMP
    on_bad: str = ON_BAD_CLAMP


# Top-level keys
TOP_LEVEL: tuple[KeySpec, ...] = (
    KeySpec(
        key="highscore_filename",
        type=str,
        default="highscore.json",
        normalize=NONE,
        on_bad=ON_BAD_DEFAULT,
    ),
    KeySpec(
        key="lives",
        type=int,
        default=3,
        min=1,
        max=9,
    ),
    KeySpec(
        key="points_per_pacgum",
        type=int,
        default=10,
        min=0,
        max=10000,
    ),
    KeySpec(
        key="points_per_super_pacgum",
        type=int,
        default=50,
        min=0,
        max=10000,
    ),
    KeySpec(
        key="points_per_ghost",
        type=int,
        default=200,
        min=0,
        max=10000,
    ),
    KeySpec(
        key="seed",
        type=int,
        default=42,
        min=1,
        max=999999999,
    ),
    KeySpec(
        key="levels",
        type=list,
        default=[],
        normalize=LEVELS,
        on_bad=ON_BAD_DEFAULT,
    ),
)


# Per-level keys (LevelConfig)
LEVEL: tuple[KeySpec, ...] = (
    KeySpec(
        key="width",
        type=int,
        default=21,
        min=15,
        max=51,
        normalize=ODD,
    ),
    KeySpec(
        key="height",
        type=int,
        default=21,
        min=11,
        max=51,
    ),
    KeySpec(
        key="pacgum",
        type=int,
        default=42,
        min=0,
        max=1000,
        normalize=DEFERRED,
        on_bad=ON_BAD_DEFAULT,
    ),
    KeySpec(
        key="level_max_time",
        type=int,
        default=90,
        min=1,
        max=600,
    ),
)
