"""Table-driven validation of the raw config dictionary (T2.6)."""

from typing import Any, Optional

from pacman.data.spec import (
    LEVEL,
    LEVELS,
    LEVELS_FILL_RULE,
    LEVELS_MIN_COUNT,
    ODD,
    ON_BAD_DEFAULT,
    TOP_LEVEL,
    KeySpec,
)
from pacman.log import get_logger

logger = get_logger(__name__)


def _type_msg(spec: KeySpec, value: Any) -> str:
    # Message for a value of the wrong type: what came, what is used.
    return (
        f"key '{spec.key}': {value!r} invalid, using default {spec.default!r}"
    )


def _fix_msg(spec: KeySpec, value: Any, fixed: Any) -> str:
    # Message for a corrected number: what it was, what it became.
    return f"key '{spec.key}': {value!r} corrected to {fixed!r}"


def _clean_value(value: Any, spec: KeySpec) -> tuple[Any, Optional[str]]:
    # Clean one present value against one spec row.
    # Lists never reach here: LEVELS is branched out by the caller.
    # Returns (clean value, message) — message is None if unchanged.
    if spec.type is int and isinstance(value, bool):
        # isinstance(True, int) is True: bools need an explicit guard.
        return spec.default, _type_msg(spec, value)
    if not isinstance(value, spec.type):
        return spec.default, _type_msg(spec, value)
    fixed: Any = value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        out_of_range = (
            (spec.min is not None and fixed < spec.min)
            or (spec.max is not None and fixed > spec.max)
        )
        if out_of_range:
            if spec.on_bad == ON_BAD_DEFAULT:
                return spec.default, _type_msg(spec, value)
            if spec.min is not None and fixed < spec.min:
                fixed = spec.min
            if spec.max is not None and fixed > spec.max:
                fixed = spec.max
    if spec.normalize == ODD and fixed % 2 == 0:
        # PKG-2: an even width puts a wall block in the maze centre.
        # -1 (not +1) so the fix never exceeds max; re-clamp
        # afterwards for safety if min/max are ever even.
        fixed -= 1
        if spec.min is not None and fixed < spec.min:
            fixed = spec.min
        if spec.max is not None and fixed > spec.max:
            fixed = spec.max
    if fixed != value:
        return fixed, _fix_msg(spec, value, fixed)
    return value, None


def _default_level() -> dict[str, Any]:
    # One level built purely from LEVEL defaults.
    return {spec.key: spec.default for spec in LEVEL}


def _validate_levels(value: Any) -> tuple[list[dict[str, Any]], list[str]]:
    # Normalize raw 'levels' into a list of clean level dicts.
    messages: list[str] = []
    if not isinstance(value, list):
        # Missing or broken list: rebuild from defaults (worth logging:
        # ten whole levels is a structural fix, not a quiet default).
        messages.append(
            f"key 'levels': invalid, generated {LEVELS_MIN_COUNT} defaults"
        )
        return [_default_level() for _ in range(LEVELS_MIN_COUNT)], messages
    items: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            messages.append(f"levels[{index}]: invalid, using default level")
            items.append(_default_level())
            continue
        level: dict[str, Any] = {}
        for spec in LEVEL:
            if spec.key not in raw:
                level[spec.key] = spec.default
                continue
            clean, msg = _clean_value(raw[spec.key], spec)
            level[spec.key] = clean
            if msg is not None:
                messages.append(f"levels[{index}]: {msg}")
        items.append(level)
    given = len(items)
    while len(items) < LEVELS_MIN_COUNT:
        if LEVELS_FILL_RULE == "repeat_last" and items:
            # Copies, not references: repeated levels must not share
            # one dict object, or a later mutation hits them all.
            items.append(dict(items[-1]))
        else:
            # Empty list has no last level to repeat: pure defaults.
            items.append(_default_level())
    if len(items) > given:
        messages.append(
            f"key 'levels': {given} supplied, padded to {LEVELS_MIN_COUNT}"
        )
    # More than LEVELS_MIN_COUNT: kept as-is, no rule forbids extra.
    return items, messages


def validate_config(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the raw config dict against the spec tables.

    Unknown keys are dropped silently (REQ-052). Each correction
    is logged as a warning to stderr (REQ-051). Never raises: bad input
    becomes safe defaults (REQ-050).

    Args:
        data: Raw parsed config (a dict, guaranteed by T2.4).

    Returns:
        Clean dict with every known key present; 'levels' is a
        list of clean per-level dicts.
    """
    clean: dict[str, Any] = {}
    messages: list[str] = []
    for spec in TOP_LEVEL:
        if spec.normalize == LEVELS:
            # Structural key: the whole list is handled separately.
            levels, level_msgs = _validate_levels(data.get(spec.key))
            clean[spec.key] = levels
            messages.extend(level_msgs)
            continue
        if spec.key not in data:
            # Missing key: silent default (absence is not an error).
            clean[spec.key] = spec.default
            continue
        value, msg = _clean_value(data[spec.key], spec)
        clean[spec.key] = value
        if msg is not None:
            messages.append(msg)
    for msg in messages:
        logger.warning(msg)
    return clean


def level_seed(base: int, index: int) -> int:
    """Derive a level's maze seed from the config seed.

    One seed in the config deterministically reshapes every maze:
    level N always generates from the same seed for a given config.

    Args:
        base: Top-level config seed (already clamped to >= 1).
        index: Zero-based level number (0 for the first level).

    Returns:
        The seed to generate this level's maze with.
    """
    return base + index


def fit_pacgum(
    requested: int, free_cells: int
) -> tuple[int, Optional[str]]:
    """Fit the pacgum count to the maze's walkable cells.

    The upper bound is known only after maze generation, so the
    future maze adapter calls this once walkable cells are known.

    Args:
        requested: Pacgum count from the validated level (>= 0).
        free_cells: Walkable cells in the generated maze.

    Returns:
        Pair (fitted count, message); message is None if unchanged.
    """
    fitted = max(0, min(requested, free_cells))
    if fitted != requested:
        return fitted, f"pacgum: {requested} exceeds {free_cells} cells"
    return fitted, None
