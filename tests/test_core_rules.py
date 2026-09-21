"""Tests for eating and winning: pacman.core.rules.tick."""

from random import Random

import pytest

from pacman.core.entity import Entity, EntityKind
from pacman.core.events import GameEvent
from pacman.core.movement import MAX_DT, advance
from pacman.core.rules import PLAYER_SPEED, set_direction, tick
from pacman.core.state import GameState, ScoringRules
from pacman.maze.model import Cell, Direction
from tests.helpers import run_for

SCORING = ScoringRules(pacgum=10, super_pacgum=50, ghost=200)
ONE_CELL = 1.0 / PLAYER_SPEED
"""Base frame time: 1.5x enters exactly one cell, 2.5x exactly two.

Mid-cell margins, not exact multiples: speed * (2 / speed) can
round to 1.999... and enter one cell short. Tests follow any speed.
"""


def test_eats_pacgum(empty_state: GameState) -> None:
    """Entering a pacgum cell scores X, emits an event, removes it."""
    state: GameState = empty_state
    state.pacgums = {Cell(3, 2), Cell(0, 0)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, SCORING, 1.5 * ONE_CELL)
    assert state.score == 10
    assert GameEvent.PACGUM_EATEN in events
    assert Cell(3, 2) not in state.pacgums
    assert Cell(0, 0) in state.pacgums


def test_eats_on_every_entered_cell(empty_state: GameState) -> None:
    """One long frame eats each pacgum on its path, not just the last.

    The expectation comes from an independent advance() run with
    the same inputs, so the test holds for any PLAYER_SPEED: the
    MAX_DT clamp caps single-frame distance, and this test refuses
    to assume how many cells that is. Kept on a single direct tick:
    splitting the frame would stop testing what this test is for.
    """
    if PLAYER_SPEED * MAX_DT < 2.0:
        pytest.skip("a single frame cannot cross two cells at this speed")
    state: GameState = empty_state
    set_direction(state, Direction.RIGHT)
    probe = Entity.standing_at(EntityKind.PLAYER, Cell(2, 2))
    probe.next_direction = Direction.RIGHT
    entered = advance(probe, state.maze, PLAYER_SPEED, MAX_DT)
    assert len(entered) >= 1
    state.pacgums = set(entered)
    events = tick(state, SCORING, MAX_DT)
    assert state.score == 10 * len(entered)
    assert events.count(GameEvent.PACGUM_EATEN) == len(entered)
    assert not state.pacgums


def test_eats_super_pacgum(empty_state: GameState) -> None:
    """Super-pacgums score Y and emit their own event."""
    state: GameState = empty_state
    state.super_pacgums = {Cell(3, 2)}
    state.pacgums = {Cell(0, 0)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, SCORING, 1.5 * ONE_CELL)
    assert state.score == 50
    assert GameEvent.SUPER_PACGUM_EATEN in events
    assert not state.super_pacgums


def test_victory_on_last_pacgum(empty_state: GameState) -> None:
    """Clearing the last dot emits LEVEL_CLEARED exactly once."""
    state: GameState = empty_state
    state.pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, SCORING, 1.5 * ONE_CELL)
    assert GameEvent.LEVEL_CLEARED in events
    assert events.count(GameEvent.LEVEL_CLEARED) == 1


def test_victory_does_not_repeat(empty_state: GameState) -> None:
    """Ticks after the win emit nothing more."""
    state: GameState = empty_state
    state.pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    run_for(state, SCORING, 1.5 * ONE_CELL)
    events = tick(state, SCORING, 0.1)
    assert GameEvent.LEVEL_CLEARED not in events
    assert events == []


def test_no_victory_while_super_remains(
    empty_state: GameState,
) -> None:
    """All ordinary eaten but a super left: no LEVEL_CLEARED yet."""
    state: GameState = empty_state
    state.pacgums = {Cell(3, 2)}
    state.super_pacgums = {Cell(4, 4)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, SCORING, 1.5 * ONE_CELL)
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
    events = run_for(state, SCORING, 1.5 * ONE_CELL)
    assert GameEvent.SUPER_PACGUM_EATEN in events
    assert GameEvent.LEVEL_CLEARED not in events


def test_score_never_decreases(empty_state: GameState) -> None:
    """A thousand random ticks: the score only moves up."""
    state: GameState = empty_state
    maze = state.maze
    cells = sorted(maze.passages)
    rng = Random(42)
    state.pacgums = set(rng.sample(cells, 10))
    state.super_pacgums = set()
    seen = [state.score]
    for _ in range(1000):
        set_direction(state, rng.choice(list(Direction)))
        tick(state, SCORING, 0.05)
        seen.append(state.score)
    assert all(later >= earlier for earlier, later in zip(seen, seen[1:]))
