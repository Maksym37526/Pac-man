"""Tests for pure highscore logic: pacman.data.highscore."""

import pytest

from pacman.data.highscore import (
    HighscoreEntry,
    insert_score,
    normalise_name,
)


def test_valid_names_pass_through() -> None:
    """Letters, digits, spaces, exactly 10 chars stay as-is."""
    assert normalise_name("Max") == "Max"
    assert normalise_name("AB 12 cd") == "AB 12 cd"
    assert normalise_name("0123456789") == "0123456789"


def test_long_name_is_cut() -> None:
    """15 characters shrink to the first 10."""
    assert normalise_name("A" * 15) == "A" * 10


def test_edges_are_stripped() -> None:
    """Surrounding spaces never reach the table."""
    assert normalise_name(" Max ") == "Max"


def test_empty_becomes_default() -> None:
    """Empty or blank input still saves a score, as PLAYER."""
    assert normalise_name("") == "PLAYER"
    assert normalise_name("   ") == "PLAYER"


def test_symbols_become_default() -> None:
    """Anything outside [A-Za-z0-9 ] is not kept."""
    assert normalise_name("a!b") == "PLAYER"
    assert normalise_name("a@b#c") == "PLAYER"


def test_cyrillic_becomes_default() -> None:
    """Decision A: Unicode alphanumerics are rejected (ASCII)."""
    assert normalise_name("Максим") == "PLAYER"


def test_trailing_newline_stripped() -> None:
    """Edge whitespace (even a newline) is stripped, not kept."""
    assert normalise_name("abc\n") == "abc"


def test_inner_newline_rejected() -> None:
    """fullmatch, not ^...$: 'ab\\ncd' must not slip through."""
    assert normalise_name("ab\ncd") == "PLAYER"


def test_non_string_becomes_default() -> None:
    """Garbage from the caller degrades to PLAYER, not a crash."""
    assert normalise_name(None) == "PLAYER"
    assert normalise_name(42) == "PLAYER"


def test_insert_sorts_highest_first() -> None:
    """A new best result lands on top."""
    table = (
        HighscoreEntry("A", 100),
        HighscoreEntry("B", 50),
    )
    updated = insert_score(table, HighscoreEntry("C", 200))
    assert [e.score for e in updated] == [200, 100, 50]


def test_table_cut_to_ten() -> None:
    """15 inserts leave exactly the 10 best."""
    table: tuple[HighscoreEntry, ...] = ()
    for points in range(15):
        table = insert_score(
            table, HighscoreEntry(f"P{points}", points)
        )
    assert len(table) == 10
    assert [e.score for e in table] == list(range(14, 4, -1))


def test_tie_keeps_earlier_first() -> None:
    """Decision C: equal scores stay in arrival order."""
    table = (HighscoreEntry("OLD", 500),)
    updated = insert_score(table, HighscoreEntry("NEW", 500))
    assert [e.name for e in updated] == ["OLD", "NEW"]


def test_zero_score_counts() -> None:
    """REQ-066: zero is a valid, storable score."""
    updated = insert_score((), HighscoreEntry("Z", 0))
    assert updated == (HighscoreEntry("Z", 0),)


def test_input_tuple_untouched() -> None:
    """Insert returns a new table; the old one never mutates."""
    table = (HighscoreEntry("A", 10),)
    insert_score(table, HighscoreEntry("B", 20))
    assert table == (HighscoreEntry("A", 10),)


def test_bad_score_rejected() -> None:
    """Negative, bool or non-int scores are caller bugs: ValueError."""
    with pytest.raises(ValueError):
        insert_score((), HighscoreEntry("N", -5))
    with pytest.raises(ValueError):
        insert_score((), HighscoreEntry("B", True))
