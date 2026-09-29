"""Tests for multi-level sessions: pacman.core.session (Phase 7)."""

from random import Random

import pytest

from pacman.core.events import GameEvent
from pacman.core.session import LevelSpec, Session, new_session
from pacman.core.settings import GameSettings
from pacman.core.state import GameState, new_game_state
from pacman.data.config import build_config
from pacman.data.validator import validate_config
from pacman.game import build_level_specs, build_settings, new_game
from pacman.maze.adapter import make_maze
from pacman.maze.fake import open_grid
from pacman.maze.layout import gen_layout
from pacman.maze.model import Cell, Direction, step
from pacman.maze.normalize import normalize

QUIET = GameSettings(
    pacgum=10,
    super_pacgum=50,
    ghost=200,
    ghost_speed=0.0,
    frightened_speed=0.0,
)
SPECS = (
    LevelSpec(width=15, height=11, pacgums=0, level_max_time=90),
    LevelSpec(width=15, height=11, pacgums=5, level_max_time=123),
)


def make_open_session(
    count: int = 2,
    lives: int = 3,
    specs: tuple[LevelSpec, ...] | None = None,
) -> Session:
    """A session whose current level is a known open 5x5 maze."""
    if specs is None:
        specs = tuple(
            LevelSpec(
                width=15,
                height=11,
                pacgums=0,
                level_max_time=90 + 10 * index,
            )
            for index in range(count)
        )
    maze = normalize(make_maze(open_grid(5, 5)))
    layout = gen_layout(maze, 0, Random(7))
    state = new_game_state(
        maze,
        layout,
        lives=lives,
        time_remaining=float(specs[0].level_max_time),
        level_index=0,
        level_count=len(specs),
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


def eat_last_pacgum(session: Session) -> list[GameEvent]:
    """Place one pacgum ahead of the player and walk into it."""
    session.level.pacgums = {Cell(3, 2)}
    session.level.super_pacgums = set()
    session.set_direction(Direction.RIGHT)
    return session.tick(1.5 / QUIET.player_speed)


def eat_into_next_level(session: Session) -> list[GameEvent]:
    """Clear a generated level, then eat one dot to leave it.

    Freezes the ghosts first: the walk must trigger exactly one
    LEVEL_CLEARED, never a catch on the way out.
    """
    session.settings = QUIET
    centre = session.level.maze.centre
    open_dirs = sorted(
        session.level.maze.passages[centre], key=lambda d: d.name
    )
    assert open_dirs
    direction = open_dirs[0]
    session.level.pacgums = {step(centre, direction)}
    session.level.super_pacgums = set()
    session.set_direction(direction)
    return session.tick(1.5 / QUIET.player_speed)


def test_pause_preserves_timer() -> None:
    """Skipped ticks cost nothing; a real tick moves the timer."""
    session = make_open_session()
    session.level.time_remaining = 5.0
    # Paused frames: B renders without ever calling tick.
    assert session.level.time_remaining == pytest.approx(5.0)
    session.tick(0.1)
    assert session.level.time_remaining == pytest.approx(4.9)


def test_advances_to_next_level() -> None:
    """LEVEL_CLEARED on level 0 lands on level 1."""
    session = make_open_session()
    events = eat_last_pacgum(session)
    assert GameEvent.LEVEL_CLEARED in events
    assert GameEvent.GAME_WON not in events
    assert session.level.level_index == 1
    assert session.level.level_count == 2
    assert not session.finished


def test_score_survives_transition() -> None:
    """Points earned on level 0 are still there on level 1."""
    session = make_open_session()
    eat_last_pacgum(session)
    assert session.level.score == 10


def test_lives_survive_transition() -> None:
    """A lost life is not refunded by a level change."""
    session = make_open_session()
    session.level.lives = 2
    eat_last_pacgum(session)
    assert session.level.lives == 2


def test_timer_resets_from_next_config() -> None:
    """The new level counts down its own configured limit."""
    session = make_open_session()
    eat_last_pacgum(session)
    assert session.level.time_remaining == pytest.approx(100.0)


def test_new_level_has_fresh_pacgums() -> None:
    """The next maze brings its own dots to eat."""
    session = make_open_session(specs=SPECS)
    eat_last_pacgum(session)
    assert session.level.level_index == 1
    assert len(session.level.pacgums) == 5
    assert len(session.level.super_pacgums) == 4


def test_wins_on_last_level() -> None:
    """Clearing the final level ends the run with GAME_WON."""
    session = make_open_session(count=1)
    events = eat_last_pacgum(session)
    assert GameEvent.GAME_WON in events
    assert session.finished
    assert session.won


def test_won_ticks_stay_quiet() -> None:
    """Ticks after victory change nothing and emit nothing."""
    session = make_open_session(count=1)
    eat_last_pacgum(session)
    again = session.tick(0.1)
    assert again == []
    assert session.finished


def test_time_up_costs_a_life_and_resets_timer() -> None:
    """Time-up respawns everybody and restarts the same level."""
    session = make_open_session()
    session.level.time_remaining = 0.05
    events = session.tick(0.2)
    assert GameEvent.TIME_UP in events
    assert session.level.lives == 2
    assert session.level.time_remaining == pytest.approx(90.0)
    assert not session.finished


def test_time_up_keeps_eaten_pacgums() -> None:
    """Dots eaten before time-up stay eaten after the restart."""
    session = make_open_session()
    session.level.pacgums = {Cell(0, 0)}
    session.level.time_remaining = 0.05
    session.tick(0.2)
    assert session.level.pacgums == {Cell(0, 0)}


def test_time_up_on_last_life_ends_game() -> None:
    """Time-up with no lives left is GAME_OVER, not a restart."""
    session = make_open_session(lives=1)
    session.level.time_remaining = 0.05
    events = session.tick(0.2)
    assert GameEvent.TIME_UP in events
    assert GameEvent.GAME_OVER in events
    assert session.finished
    assert not session.won


def test_game_over_ticks_stay_quiet() -> None:
    """Ticks after defeat change nothing and emit nothing."""
    session = make_open_session(lives=1)
    session.level.time_remaining = 0.05
    session.tick(0.2)
    again = session.tick(0.2)
    assert again == []


def test_game_over_on_caught_last_life() -> None:
    """Losing the last life to a ghost finishes the session."""
    session = make_open_session(lives=1)
    ghost = session.level.ghosts[0]
    ghost.cell = session.level.player.cell
    ghost.prev_cell = session.level.player.cell
    ghost.progress = 0.0
    events = session.tick(0.05)
    assert GameEvent.GAME_OVER in events
    assert session.finished
    assert session.tick(0.05) == []


def test_death_beats_clear_in_same_tick() -> None:
    """Last dot eaten and caught at once: defeat, no transition."""
    session = make_open_session(lives=1)
    session.level.pacgums = {Cell(3, 2)}
    session.level.super_pacgums = set()
    ghost = session.level.ghosts[0]
    ghost.cell = Cell(3, 2)
    ghost.prev_cell = Cell(3, 2)
    ghost.progress = 0.0
    session.set_direction(Direction.RIGHT)
    events = session.tick(1.5 / QUIET.player_speed)
    assert GameEvent.PACGUM_EATEN in events
    assert GameEvent.PLAYER_CAUGHT in events
    assert GameEvent.GAME_OVER in events
    assert session.finished
    assert not session.won
    assert session.level.level_index == 0


def test_new_session_needs_a_level() -> None:
    """Building a session with no levels fails loudly."""
    with pytest.raises(ValueError):
        new_session((), QUIET, Random(1), 42)


def test_short_config_pads_to_ten_levels() -> None:
    """REQ-102 holds in the game: 3 configured levels play 10."""
    clean = validate_config({"levels": [{}, {}, {}]})
    config = build_config(clean)
    session = new_game(config, Random(9))
    assert len(session.levels) == 10
    assert session.level.level_count == 10


def test_later_levels_differ_across_runs() -> None:
    """REQ-073 at game level: level 1 fixed, level 2 fresh."""
    clean = validate_config(
        {
            "seed": 77,
            "levels": [
                {
                    "width": 15,
                    "height": 11,
                    "pacgum": 0,
                    "level_max_time": 90,
                },
                {
                    "width": 15,
                    "height": 11,
                    "pacgum": 0,
                    "level_max_time": 90,
                },
            ],
        }
    )
    config = build_config(clean)
    first = new_game(config)
    second = new_game(config)
    assert (
        first.level.maze.passages == second.level.maze.passages
    )
    for session in (first, second):
        eat_into_next_level(session)
    assert (
        first.level.maze.passages != second.level.maze.passages
    )


def test_new_game_wires_config_values() -> None:
    """Points, lives, seed and shapes arrive from the Config."""
    clean = validate_config(
        {
            "lives": 5,
            "points_per_pacgum": 7,
            "points_per_super_pacgum": 8,
            "points_per_ghost": 9,
            "seed": 77,
            "levels": [
                {
                    "width": 21,
                    "height": 21,
                    "pacgum": 3,
                    "level_max_time": 66,
                }
            ],
        }
    )
    config = build_config(clean)
    session = new_game(config, Random(3))
    assert session.level.lives == 5
    assert session.level.time_remaining == pytest.approx(66.0)
    assert session.settings.pacgum == 7
    assert session.settings.super_pacgum == 8
    assert session.settings.ghost == 9
    assert session.config_seed == 77
    assert session.levels[0].width == 21


def test_build_helpers_follow_config() -> None:
    """Settings and specs mirror the Config one to one."""
    clean = validate_config({})
    config = build_config(clean)
    settings = build_settings(config)
    specs = build_level_specs(config)
    assert settings.pacgum == config.points_per_pacgum
    assert len(specs) == len(config.levels)
    assert specs[0].level_max_time == config.levels[0].level_max_time


def test_level_state_carries_hud_fields(
    empty_state: GameState,
) -> None:
    """The renderer reads position in the run from one object."""
    assert empty_state.level_index == 0
    assert empty_state.level_count == 1
    assert empty_state.time_remaining == pytest.approx(90.0)
