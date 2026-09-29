"""Pure highscore logic (Phase 9).

No files here: this module works on immutable tuples, so it is
tested instantly without touching the filesystem. All dirty
cases live in highscore_store.py.
"""

import re
from dataclasses import dataclass
from typing import Final

TABLE_SIZE: Final[int] = 10
"""How many best results the table keeps (REQ-067)."""

MAX_NAME_LEN: Final[int] = 10
"""Longest allowed player name (REQ-065)."""

DEFAULT_NAME: Final[str] = "PLAYER"
"""Fallback when nothing usable was typed (decision B)."""

NAME_PATTERN: Final[re.Pattern[str]] = re.compile(
    f"[A-Za-z0-9 ]{{1,{MAX_NAME_LEN}}}"
)
"""Allowed names: ASCII letters, digits and spaces (decision A).

Built from MAX_NAME_LEN, so the length lives in exactly one
place: changing the constant rebuilds the pattern with it.

ASCII, not Unicode: "alphanumeric" in V.5 most directly reads
as ASCII letters and digits, and the menu font is chosen by B
and not yet fixed — Unicode names could enter the saved file
that a Latin-only font cannot draw (REQ-070). Widening later
is a one-line change; narrowing after scores exist is not.

Matched with fullmatch, never with ^...$: in Python $ also
matches before a trailing newline, so "ab\\ncd" would slip
through a ^...$ check.
"""


@dataclass(frozen=True)
class HighscoreEntry:
    """One row of the table: who scored how much."""

    name: str
    score: int


def normalise_name(raw: object) -> str:
    """Turn anything typed into a name the table accepts.

    Pipeline (decision B): strip the edges, cut to 10 chars,
    fall back to DEFAULT_NAME when empty, fall back again when
    the pattern still rejects it. Always returns a usable name:
    never raises, never returns an empty string.

    Args:
        raw: Whatever arrived from the name entry screen.

    Returns:
        A valid name matching NAME_PATTERN.
    """
    if not isinstance(raw, str):
        return DEFAULT_NAME
    cleaned = raw.strip()[:MAX_NAME_LEN]
    if not cleaned:
        return DEFAULT_NAME
    if NAME_PATTERN.fullmatch(cleaned) is None:
        return DEFAULT_NAME
    return cleaned


def insert_score(
    entries: tuple[HighscoreEntry, ...], entry: HighscoreEntry
) -> tuple[HighscoreEntry, ...]:
    """Return a new table with one more result recorded.

    The input tuple is never mutated. Sorted by score,
    highest first, cut to TABLE_SIZE. The sort is stable, so
    equal scores keep whoever scored first on top (decision C).

    Args:
        entries: Current table, best first.
        entry: The new result to record.

    Returns:
        The new table, at most TABLE_SIZE rows.

    Raises:
        ValueError: If the score is not a non-negative int.
            Such a value can only come from a caller bug: real
            game scores are ints, and file content is cleaned
            by the store layer instead.
    """
    if (
        not isinstance(entry.score, int)
        or isinstance(entry.score, bool)
        or entry.score < 0
    ):
        raise ValueError(
            f"score must be a non-negative int, got "
            f"{entry.score!r}"
        )
    ranked = sorted(
        [*entries, entry], key=lambda e: e.score, reverse=True
    )
    return tuple(ranked[:TABLE_SIZE])
