"""Tests for cheat mode: pacman.core.cheats and Session cheats."""

from dataclasses import replace
from random import Random

from pacman.core.cheats import (
    CHEAT_SPEED_FACTOR,
    CheatCommand,
    CheatState,
    effective_settings,
)
from pacman.core.entity import EntityMode
from pacman.core.events import GameEvent
from pacman.core.session import LevelSpec, Session, new_session
from pacman.core.settings import GameSettings
from pacman.core.state import new_game_state
from pacman.maze.adapter import make_maze
from pacman.maze.fake import open_grid
from pacman.maze.layout import gen_layout
from pacman.maze.model import Cell, Direction
from pacman.maze.normalize import normalize

QUIET = GameSettings(
    pacgum=10,
    super_pacgum=50,
    ghost=200,
    ghost_speed=0.0,
    frightened_speed=0.0,
)
OFF = CheatState()


def make_session(count: int = 2) -> Session:
    """A session on a known open 5x5 maze, cheats ready."""
    specs = tuple(
        LevelSpec(
            width=15,
            height=11,
            pacgums=0,
            level_max_time=90,
        )
        for _ in range(count)
    )
    maze = normalize(make_maze(open_grid(5, 5)))
    layout = gen_layout(maze, 0, Random(7))
    state = new_game_state(
        maze,
        layout,
        lives=3,
        time_remaining=90.0,
        level_index=0,
        level_count=count,
    )
    state.pacgums.clear()
    state.super_pacgums.clear()
    return Session(
        level=state,
        settings=QUIET,
        rng=Random(1),
        levels=specs,
        config_seed=42,
    )


def enable(session: Session) -> None:
    """Turn the master switch on."""
    assert session.apply_cheat(CheatCommand.TOGGLE_CHEATS) == []


def touch_ghost(session: Session, mode: EntityMode) -> None:
    """Park the first ghost onto the standing player."""
    ghost = session.level.ghosts[0]
    ghost.cell = session.level.player.cell
    ghost.prev_cell = session.level.player.cell
    ghost.progress = 0.0
    ghost.mode = mode


def test_disabled_returns_same_object() -> None:
    """No cheats, no work: the very same settings object."""
    base = GameSettings(pacgum=1, super_pacgum=2, ghost=3)
    assert effective_settings(base, OFF) is base


def test_fast_without_master_changes_nothing() -> None:
    """fast=True alone is inert; the master switch gates all."""
    base = GameSettings(pacgum=1, super_pacgum=2, ghost=3)
    cheats = CheatState(enabled=False, fast=True)
    assert effective_settings(base, cheats) is base


def test_fast_speeds_up() -> None:
    """Both flags on: the player runs by the cheat factor."""
    base = GameSettings(pacgum=1, super_pacgum=2, ghost=3)
    cheats = CheatState(enabled=True, fast=True)
    tuned = effective_settings(base, cheats)
    assert tuned.player_speed == base.player_speed * CHEAT_SPEED_FACTOR
    assert base.player_speed == 8.0


def test_command_without_mode_does_nothing() -> None:
    """A stray keypress in a normal game changes nothing."""
    session = make_session()
    for command in (
        CheatCommand.TOGGLE_INVINCIBLE,
        CheatCommand.SKIP_LEVEL,
        CheatCommand.LOSE_LIFE,
    ):
        assert session.apply_cheat(command) == []
    assert session.level.level_index == 0
    assert session.level.lives == 3


def test_toggle_cheats_always_works() -> None:
    """The master switch is the one command needing no mode."""
    session = make_session()
    session.apply_cheat(CheatCommand.TOGGLE_CHEATS)
    assert session.cheats.enabled
    session.apply_cheat(CheatCommand.TOGGLE_CHEATS)
    assert not session.cheats.enabled


def test_disabling_keeps_taint() -> None:
    """cheats_used never lowers: the run stays non-storable."""
    session = make_session()
    assert not session.cheats_used
    enable(session)
    assert session.cheats_used
    session.apply_cheat(CheatCommand.TOGGLE_CHEATS)
    assert session.cheats_used


def test_clean_run_stays_untainted() -> None:
    """Ticks and turns without cheats leave the flag down."""
    session = make_session()
    session.set_direction(Direction.RIGHT)
    session.tick(0.1)
    assert not session.cheats_used


def test_skip_level_keeps_score_and_lives() -> None:
    """Jumping ahead carries the run, not just the index."""
    session = make_session()
    enable(session)
    session.level.score = 30
    session.level.lives = 2
    events = session.apply_cheat(CheatCommand.SKIP_LEVEL)
    assert GameEvent.LEVEL_CLEARED in events
    assert GameEvent.GAME_WON not in events
    assert session.level.level_index == 1
    assert session.level.score == 30
    assert session.level.lives == 2


def test_skip_on_last_level_wins() -> None:
    """Skipping the finale ends the run through the normal path."""
    session = make_session(count=1)
    enable(session)
    events = session.apply_cheat(CheatCommand.SKIP_LEVEL)
    assert GameEvent.LEVEL_CLEARED in events
    assert GameEvent.GAME_WON in events
    assert session.finished
    assert session.won


def test_cheats_quiet_after_victory() -> None:
    """Finished sessions ignore every command, toggles too."""
    session = make_session(count=1)
    enable(session)
    session.apply_cheat(CheatCommand.SKIP_LEVEL)
    assert session.finished
    for command in (
        CheatCommand.SKIP_LEVEL,
        CheatCommand.LOSE_LIFE,
        CheatCommand.TOGGLE_INVINCIBLE,
    ):
        assert session.apply_cheat(command) == []
    assert session.level.lives == 3


def test_cheats_quiet_after_defeat() -> None:
    """No lives from below zero: commands stop at GAME_OVER."""
    session = make_session()
    session.level.lives = 1
    enable(session)
    session.apply_cheat(CheatCommand.LOSE_LIFE)
    assert session.finished
    assert session.apply_cheat(CheatCommand.LOSE_LIFE) == []
    assert session.level.lives == 0


def test_clear_level_demonstrates_the_win() -> None:
    """CLEAR_LEVEL empties the maze and claims the clear."""
    session = make_session()
    enable(session)
    session.level.pacgums = {Cell(0, 0)}
    events = session.apply_cheat(CheatCommand.CLEAR_LEVEL)
    assert GameEvent.LEVEL_CLEARED in events
    assert session.level.level_index == 1


def test_start_fright() -> None:
    """One press shows the whole edible-ghost mechanic."""
    session = make_session()
    enable(session)
    events = session.apply_cheat(CheatCommand.START_FRIGHT)
    assert events == [GameEvent.FRIGHT_STARTED]
    assert all(
        ghost.mode is EntityMode.FRIGHTENED
        for ghost in session.level.ghosts
    )


def test_lose_life_respawns_home() -> None:
    """The cheat kills exactly like a ghost, minus the ghost."""
    session = make_session()
    enable(session)
    events = session.apply_cheat(CheatCommand.LOSE_LIFE)
    assert GameEvent.PLAYER_CAUGHT in events
    assert session.level.lives == 2
    assert session.level.player.cell == session.level.maze.centre
    assert not session.finished


def test_lose_last_life_ends_game() -> None:
    """Draining the last life shows the Game Over path."""
    session = make_session()
    session.level.lives = 1
    enable(session)
    events = session.apply_cheat(CheatCommand.LOSE_LIFE)
    assert GameEvent.GAME_OVER in events
    assert session.finished


def test_invincible_ghost_cannot_catch() -> None:
    """The shield is about survival: NORMAL touch is ignored."""
    session = make_session()
    enable(session)
    session.apply_cheat(CheatCommand.TOGGLE_INVINCIBLE)
    touch_ghost(session, EntityMode.NORMAL)
    events = session.tick(0.05)
    assert GameEvent.PLAYER_CAUGHT not in events
    assert session.level.lives == 3


def test_invincible_ghost_still_edible() -> None:
    """The shield never blocks dessert: FRIGHTENED still scores."""
    session = make_session()
    enable(session)
    session.apply_cheat(CheatCommand.TOGGLE_INVINCIBLE)
    session.apply_cheat(CheatCommand.START_FRIGHT)
    touch_ghost(session, EntityMode.FRIGHTENED)
    before = session.level.score
    events = session.tick(0.05)
    assert GameEvent.GHOST_EATEN in events
    assert session.level.score == before + QUIET.ghost


def test_timer_runs_despite_shield() -> None:
    """TIME_UP is a separate requirement; the shield skips it."""
    session = make_session()
    enable(session)
    session.apply_cheat(CheatCommand.TOGGLE_INVINCIBLE)
    session.level.time_remaining = 0.05
    events = session.tick(0.2)
    assert GameEvent.TIME_UP in events


def test_ten_skips_win_the_run() -> None:
    """REQ-097 concretely: a reviewer reaches Victory by hand."""
    specs = tuple(
        LevelSpec(
            width=15,
            height=11,
            pacgums=0,
            level_max_time=90,
        )
        for _ in range(10)
    )
    session = new_session(specs, QUIET, Random(5), 42)
    enable(session)
    events: list[GameEvent] = []
    for _ in range(10):
        events = session.apply_cheat(CheatCommand.SKIP_LEVEL)
    assert GameEvent.GAME_WON in events
    assert session.finished
    assert session.won


def test_clear_level_credits_dots() -> None:
    """CLEAR_LEVEL pays for every dot it removes, like honest play."""
    session = make_session()
    enable(session)
    session.level.pacgums = {Cell(0, 0), Cell(1, 1)}
    session.level.super_pacgums = {Cell(2, 2)}
    events = session.apply_cheat(CheatCommand.CLEAR_LEVEL)
    assert GameEvent.LEVEL_CLEARED in events
    assert session.level.score == 2 * 10 + 50


def test_frozen_ghosts_hold_position() -> None:
    """Frozen ghosts do not advance while the clock still runs."""
    session = make_session()
    session.settings = replace(session.settings, ghost_speed=5.0)
    enable(session)
    session.tick(0.2)
    session.apply_cheat(CheatCommand.TOGGLE_FROZEN)
    assert session.cheats.frozen
    before = [
        (g.cell, g.prev_cell, g.progress) for g in session.level.ghosts
    ]
    session.tick(0.5)
    after = [
        (g.cell, g.prev_cell, g.progress) for g in session.level.ghosts
    ]
    assert before == after
    session.apply_cheat(CheatCommand.TOGGLE_FROZEN)
    assert not session.cheats.frozen


def test_extra_life_adds_one() -> None:
    """EXTRA_LIFE is LOSE_LIFE mirrored, with no events attached."""
    session = make_session()
    enable(session)
    assert session.apply_cheat(CheatCommand.EXTRA_LIFE) == []
    assert session.level.lives == 4
