"""Tests for highscore storage: pacman.data.highscore_store."""

import json
from pathlib import Path
from typing import Any, cast

from pacman.data.config import build_config
from pacman.data.highscore import HighscoreEntry
from pacman.data.highscore_store import load, save
from pacman.data.validator import validate_config
from pacman.game import load_highscores, save_score


def write_text(path: Path, text: str) -> str:
    """Write raw text, returning the path as a string."""
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_roundtrip(tmp_path: Path) -> None:
    """Save then load returns the same table."""
    target = str(tmp_path / "scores.json")
    table = (
        HighscoreEntry("BOB", 300),
        HighscoreEntry("ANN", 100),
    )
    assert save(target, table) is True
    assert load(target) == table


def test_missing_file_is_empty(tmp_path: Path) -> None:
    """First launch: no file, no exception, empty table."""
    assert load(str(tmp_path / "absent.json")) == ()


def test_empty_file_is_empty(tmp_path: Path) -> None:
    """Zero bytes on disk degrade to an empty table."""
    target = tmp_path / "empty.json"
    assert load(write_text(target, "")) == ()


def test_non_json_is_empty(tmp_path: Path) -> None:
    """Garbage bytes never propagate an exception."""
    target = tmp_path / "junk.json"
    assert load(write_text(target, "not json {{{")) == ()


def test_non_list_top_level_is_empty(tmp_path: Path) -> None:
    """A JSON object instead of a list is rejected wholesale."""
    target = tmp_path / "object.json"
    assert load(write_text(target, '{"a": 1}')) == ()


def test_partial_recovery(tmp_path: Path) -> None:
    """Three corrupt records out of five leave two good ones."""
    target = tmp_path / "mixed.json"
    payload = [
        {"name": "OK1", "score": 50},
        {"name": "OK2", "score": 150},
        {"name": "BAD", "score": -5},
        {"name": "NOPE"},
        "just a string",
    ]
    assert load(write_text(target, json.dumps(payload))) == (
        HighscoreEntry("OK2", 150),
        HighscoreEntry("OK1", 50),
    )


def test_negative_score_dropped(tmp_path: Path) -> None:
    """REQ-066: negative scores never enter the table."""
    target = tmp_path / "negative.json"
    payload = [{"name": "NEG", "score": -1}]
    assert load(write_text(target, json.dumps(payload))) == ()


def test_string_score_dropped(tmp_path: Path) -> None:
    """REQ-066: scores must be integers, not strings."""
    target = tmp_path / "string.json"
    payload = [{"name": "STR", "score": "100"}]
    assert load(write_text(target, json.dumps(payload))) == ()


def test_bool_score_dropped(tmp_path: Path) -> None:
    """True is an int instance, but never a valid score."""
    target = tmp_path / "bool.json"
    payload = [{"name": "BOOL", "score": True}]
    assert load(write_text(target, json.dumps(payload))) == ()


def test_invalid_name_in_file_dropped(tmp_path: Path) -> None:
    """File rows must already be valid; symbols mean corruption."""
    target = tmp_path / "name.json"
    payload = [
        {"name": "a!b", "score": 10},
        {"name": "FINE", "score": 20},
    ]
    assert load(write_text(target, json.dumps(payload))) == (
        HighscoreEntry("FINE", 20),
    )


def test_fifty_records_load_ten(tmp_path: Path) -> None:
    """A bloated file still yields the ten best."""
    target = tmp_path / "big.json"
    payload = [
        {"name": f"P{i}", "score": i} for i in range(50)
    ]
    loaded = load(write_text(target, json.dumps(payload)))
    assert len(loaded) == 10
    assert [e.score for e in loaded] == list(range(49, 39, -1))


def test_unsorted_file_loads_sorted(tmp_path: Path) -> None:
    """Content order is never trusted; load sorts by score."""
    target = tmp_path / "messy.json"
    payload = [
        {"name": "LOW", "score": 5},
        {"name": "HIGH", "score": 500},
    ]
    assert load(write_text(target, json.dumps(payload))) == (
        HighscoreEntry("HIGH", 500),
        HighscoreEntry("LOW", 5),
    )


def test_directory_instead_of_file(tmp_path: Path) -> None:
    """A directory at the path degrades, never raises."""
    assert load(str(tmp_path)) == ()


def test_missing_parent_created(tmp_path: Path) -> None:
    """scores/top.json works even when scores/ is absent."""
    target = str(tmp_path / "scores" / "top.json")
    table = (HighscoreEntry("NEW", 42),)
    assert save(target, table) is True
    assert load(target) == table


def test_failed_write_keeps_old_data(tmp_path: Path) -> None:
    """A crash mid-write leaves the previous table intact."""
    target = tmp_path / "scores.json"
    old = (HighscoreEntry("OLD", 77),)
    assert save(str(target), old) is True
    before = target.read_text(encoding="utf-8")
    weird: Any = cast(Any, object())
    assert save(str(target), (HighscoreEntry("X", weird),)) is False
    assert target.read_text(encoding="utf-8") == before
    assert load(str(target)) == old
    litter = [p for p in tmp_path.iterdir()
              if p.name.startswith(".highscore-")]
    assert litter == []


def test_game_helpers_use_filename(tmp_path: Path) -> None:
    """REQ-040/068: helpers read and write the configured path."""
    clean = validate_config(
        {"highscore_filename": str(tmp_path / "custom.json")}
    )
    config = build_config(clean)
    assert load_highscores(config) == ()
    updated, ok = save_score(config, (), "Max", 100)
    assert ok is True
    assert updated == (HighscoreEntry("Max", 100),)
    assert load_highscores(config) == updated


def test_save_score_normalises_both_fields(
    tmp_path: Path,
) -> None:
    """Garbage in through save_score lands clean: PLAYER with 0."""
    clean = validate_config(
        {"highscore_filename": str(tmp_path / "fixed.json")}
    )
    config = build_config(clean)
    updated, ok = save_score(config, (), "a!b@c", -5)
    assert ok is True
    assert updated == (HighscoreEntry("PLAYER", 0),)
    assert load_highscores(config) == updated


def test_save_fails_when_parent_is_a_file(
    tmp_path: Path,
) -> None:
    """No write access to the location: False, never raised."""
    blocker = tmp_path / "blocker"
    blocker.write_text("in the way", encoding="utf-8")
    target = str(blocker / "scores.json")
    assert save(target, (HighscoreEntry("X", 1),)) is False
