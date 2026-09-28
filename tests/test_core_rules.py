"""Tests for eating and winning: pacman.core.rules.tick."""

from random import Random

import pytest

from pacman.core.entity import Entity, EntityKind
from pacman.core.events import GameEvent
from pacman.core.movement import MAX_DT, advance
from pacman.core.rules import set_direction, tick
from pacman.core.settings import GameSettings
from pacman.core.state import GameState
from pacman.maze.model import Cell, Direction
from tests.helpers import run_for

SETTINGS = GameSettings(
    pacgum=10,
    super_pacgum=50,
    ghost=200,
    ghost_speed=0.0,
    frightened_speed=0.0,
)
ONE_CELL = 1.0 / SETTINGS.player_speed
"""Base frame time: 1.5x enters exactly one cell, 2.5x exactly two.

Mid-cell margins, not exact multiples: speed * (2 / speed) can
round to 1.999... and enter one cell short. Tests follow any speed.
"""


def test_eats_pacgum(empty_state: GameState) -> None:
    """Entering a pacgum cell scores X, emits an event, removes it."""
    state: GameState = empty_state
    state.pacgums = {Cell(3, 2), Cell(0, 0)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, SETTINGS, Random(1), 1.5 * ONE_CELL)
    assert state.score == 10
    assert GameEvent.PACGUM_EATEN in events
    assert Cell(3, 2) not in state.pacgums
    assert Cell(0, 0) in state.pacgums


def test_eats_on_every_entered_cell(
    empty_state: GameState,
) -> None:
    """One long frame eats each pacgum on its path, not just the last.

    The expectation comes from an independent advance() run with
    the same inputs, so the test holds for any player speed: the
    MAX_DT clamp caps single-frame distance. Kept on a single
    direct tick: splitting the frame would stop testing this.
    """
    state: GameState = empty_state
    set_direction(state, Direction.RIGHT)
    probe = Entity.standing_at(EntityKind.PLAYER, Cell(2, 2))
    probe.next_direction = Direction.RIGHT
    entered = advance(
        probe, state.maze, SETTINGS.player_speed, MAX_DT
    )
    assert len(entered) >= 1
    state.pacgums = set(entered)
    events = tick(state, SETTINGS, Random(2), MAX_DT)
    assert state.score == 10 * len(entered)
    assert events.count(GameEvent.PACGUM_EATEN) == len(entered)
    assert not state.pacgums


def test_eats_super_pacgum(empty_state: GameState) -> None:
    """Super-pacgums score Y and emit their own event."""
    state: GameState = empty_state
    state.super_pacgums = {Cell(3, 2)}
    state.pacgums = {Cell(0, 0)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, SETTINGS, Random(3), 1.5 * ONE_CELL)
    assert state.score == 50
    assert GameEvent.SUPER_PACGUM_EATEN in events
    assert not state.super_pacgums


def test_victory_on_last_pacgum(empty_state: GameState) -> None:
    """Clearing the last dot emits LEVEL_CLEARED exactly once."""
    state: GameState = empty_state
    state.pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, SETTINGS, Random(4), 1.5 * ONE_CELL)
    assert GameEvent.LEVEL_CLEARED in events
    assert events.count(GameEvent.LEVEL_CLEARED) == 1


def test_victory_does_not_repeat(empty_state: GameState) -> None:
    """Ticks after the win emit nothing more."""
    state: GameState = empty_state
    state.pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    run_for(state, SETTINGS, Random(5), 1.5 * ONE_CELL)
    events = tick(state, SETTINGS, Random(5), 0.1)
    assert GameEvent.LEVEL_CLEARED not in events
    assert GameEvent.FRIGHT_STARTED not in events
    assert GameEvent.FRIGHT_ENDED not in events


def test_no_victory_while_super_remains(
    empty_state: GameState,
) -> None:
    """All ordinary eaten but a super left: no LEVEL_CLEARED yet."""
    state: GameState = empty_state
    state.pacgums = {Cell(3, 2)}
    state.super_pacgums = {Cell(4, 4)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, SETTINGS, Random(6), 1.5 * ONE_CELL)
    assert GameEvent.PACGUM_EATEN in events
    assert GameEvent.LEVEL_CLEARED not in events


def test_no_victory_while_ordinary_remains(
    empty_state: GameState,
) -> None:
    """Last super eaten but an ordinary left: no LEVEL_CLEARED yet."""
    state: GameState = empty_state
    state.pacgums = {Cell(0, 0)}
    state.super_pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, SETTINGS, Random(7), 1.5 * ONE_CELL)
    assert GameEvent.SUPER_PACGUM_EATEN in events
    assert GameEvent.LEVEL_CLEARED not in events


def test_score_never_decreases(empty_state: GameState) -> None:
    """A thousand random ticks: the score only moves up."""
    state: GameState = empty_state
    live = GameSettings(pacgum=10, super_pacgum=50, ghost=200)
    maze = state.maze
    cells = sorted(maze.passages)
    rng = Random(42)
    state.pacgums = set(rng.sample(cells, 10))
    state.super_pacgums = set()
    seen = [state.score]
    for _ in range(1000):
        set_direction(state, rng.choice(list(Direction)))
        tick(state, live, rng, 0.05)
        seen.append(state.score)
    assert all(
        later >= earlier for earlier, later in zip(seen, seen[1:])
    )


def test_timer_counts_down(empty_state: GameState) -> None:
    """The level timer loses exactly the clamped dt."""
    state: GameState = empty_state
    state.time_remaining = 10.0
    tick(state, SETTINGS, Random(11), 0.1)
    assert state.time_remaining == pytest.approx(9.9)


def test_time_up_fires_once(empty_state: GameState) -> None:
    """TIME_UP arrives on the crossing tick, never again."""
    state: GameState = empty_state
    state.time_remaining = 0.1
    events = tick(state, SETTINGS, Random(12), 0.2)
    assert GameEvent.TIME_UP in events
    assert events.count(GameEvent.TIME_UP) == 1
    again = tick(state, SETTINGS, Random(12), 0.2)
    assert GameEvent.TIME_UP not in again


def test_timer_never_goes_negative(
    empty_state: GameState,
) -> None:
    """A long lag clamps the timer at exactly zero."""
    state: GameState = empty_state
    state.time_remaining = 0.1
    tick(state, SETTINGS, Random(13), 10.0)
    assert state.time_remaining == 0.0


def test_lag_does_not_eat_timer(empty_state: GameState) -> None:
    """One tick of dt=10 costs at most MAX_DT of level time."""
    state: GameState = empty_state
    state.time_remaining = 10.0
    tick(state, SETTINGS, Random(14), 10.0)
    assert state.time_remaining == pytest.approx(10.0 - MAX_DT)


def test_no_movement_after_time_up(
    empty_state: GameState,
) -> None:
    """The TIME_UP tick moves nobody and eats nothing."""
    state: GameState = empty_state
    state.time_remaining = 0.05
    state.pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    events = tick(state, SETTINGS, Random(15), 0.2)
    assert GameEvent.TIME_UP in events
    assert GameEvent.PACGUM_EATEN not in events
    assert Cell(3, 2) in state.pacgums
