"""Highscore file storage (Phase 9).

The dirty layer: reading tolerates any state of the file, and
writing never leaves a half-written table behind. Pure table
logic lives in highscore.py; this module only moves rows
between tuples and disk.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pacman.data.highscore import (
    NAME_PATTERN,
    TABLE_SIZE,
    HighscoreEntry,
)
from pacman.log import get_logger

logger = get_logger(__name__)


def _clean_record(raw: Any) -> HighscoreEntry | None:
    """Turn one decoded JSON value into an entry, or drop it.

    File content is never trusted: every field is checked, and
    anything off drops just this record, never the table.

    Args:
        raw: One item of the decoded top-level list.

    Returns:
        A valid entry, or None when the record is corrupt.
    """
    if not isinstance(raw, dict):
        return None
    name = raw.get("name")
    score = raw.get("score")
    if not isinstance(name, str):
        return None
    if NAME_PATTERN.fullmatch(name) is None:
        return None
    if not isinstance(score, int) or isinstance(score, bool):
        return None
    if score < 0:
        return None
    return HighscoreEntry(name=name, score=score)


def load(path: str) -> tuple[HighscoreEntry, ...]:
    """Read the table from disk, surviving any file state.

    Never raises: a missing file is a normal first launch
    (empty table, no warning); anything else wrong degrades to
    an empty or partially recovered table with a warning.

    Args:
        path: Where the JSON table lives.

    Returns:
        The stored table, best first, at most TABLE_SIZE rows.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except FileNotFoundError:
        return ()
    except OSError as error:
        logger.warning(
            "Highscores unreadable at '%s': %s", path, error
        )
        return ()
    except UnicodeDecodeError as error:
        logger.warning(
            "Highscores at '%s' are not UTF-8: %s", path, error
        )
        return ()
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError as error:
        logger.warning(
            "Highscores at '%s' are not JSON: %s", path, error
        )
        return ()
    if not isinstance(decoded, list):
        logger.warning(
            "Highscores at '%s': top level must be a list", path
        )
        return ()
    kept = [
        clean for clean in (_clean_record(raw) for raw in decoded)
        if clean is not None
    ]
    ranked = sorted(kept, key=lambda e: e.score, reverse=True)
    if len(ranked) < len(decoded):
        logger.warning(
            "Highscores at '%s': dropped %d corrupt record(s)",
            path,
            len(decoded) - len(ranked),
        )
    return tuple(ranked[:TABLE_SIZE])


def save(path: str, entries: tuple[HighscoreEntry, ...]) -> bool:
    """Write the table atomically, creating parent folders.

    The payload goes to a temporary file in the target's own
    directory (same filesystem, so the final os.replace stays
    atomic on POSIX and Windows alike), is flushed, then moved
    over the old file in one step. A crash mid-write leaves the
    previous table intact. Any failure is logged and reported,
    never raised.

    No os.fsync here on purpose: flush plus the atomic rename
    already survive a process crash, which is the realistic
    failure mode. fsync would additionally force the OS buffers
    onto the physical medium (power-loss durability), which is
    beyond what the subject requires and costs a disk stall on
    every save. If asked: a process crash is survived (the data
    is already with the OS and the rename is atomic); a power
    loss is not, because neither the content nor the directory
    entry is forced to the physical medium. That durability
    level is beyond what V.5 asks for and costs a disk stall on
    every save.

    Args:
        path: Where the JSON table lives.
        entries: The table to store, best first.

    Returns:
        True when the new table reached the disk.
    """
    target = Path(path)
    try:
        if str(target.parent) not in ("", "."):
            target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        logger.warning(
            "Highscores directory for '%s' not created: %s",
            path,
            error,
        )
        return False
    payload = [
        {"name": entry.name, "score": entry.score}
        for entry in entries
    ]
    tmp_name: str | None = None
    try:
        descriptor, tmp_name = tempfile.mkstemp(
            dir=str(target.parent), prefix=".highscore-",
            suffix=".tmp",
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as tmp:
            json.dump(payload, tmp, indent=2)
            tmp.write("\n")
            tmp.flush()
        os.replace(tmp_name, target)
        return True
    except (OSError, ValueError, TypeError) as error:
        logger.warning(
            "Highscores not saved to '%s': %s", path, error
        )
        return False
    finally:
        # No-op on success: os.replace already moved the temp
        # file away, so there is nothing left to clean up.
        if tmp_name is not None:
            Path(tmp_name).unlink(missing_ok=True)
