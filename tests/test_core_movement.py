"""Tests for movement: pacman.core.movement and rules.tick motion."""

from random import Random

from pacman.core.entity import Entity, EntityKind
from pacman.core.movement import advance, can_go, choose_direction
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


def test_stands_still_without_input(
    empty_state: GameState,
) -> None:
    """No direction set: the player never leaves the start cell."""
    state: GameState = empty_state
    start = state.player.cell
    events = tick(state, SETTINGS, Random(11), 0.1)
    assert state.player.cell == start
    assert state.player.direction is None
    assert events == []


def test_starts_moving_on_input(empty_state: GameState) -> None:
    """Setting RIGHT moves the player east within one cell tick."""
    state: GameState = empty_state
    set_direction(state, Direction.RIGHT)
    run_for(state, SETTINGS, Random(12), 1.5 * ONE_CELL)
    assert state.player.prev_cell == Cell(3, 2)
    assert state.player.direction == Direction.RIGHT


def test_stops_at_wall(empty_state: GameState) -> None:
    """Driving into the border stops with zero leftover progress."""
    state: GameState = empty_state
    set_direction(state, Direction.LEFT)
    run_for(state, SETTINGS, Random(13), 1.5 * ONE_CELL)
    run_for(state, SETTINGS, Random(13), 1.5 * ONE_CELL)
    run_for(state, SETTINGS, Random(13), 1.5 * ONE_CELL)
    assert state.player.cell == Cell(0, 2)
    assert state.player.direction is None
    assert state.player.progress == 0.0


def test_turns_at_intersection(empty_state: GameState) -> None:
    """A turn request applies at the next cell boundary."""
    state: GameState = empty_state
    set_direction(state, Direction.RIGHT)
    run_for(state, SETTINGS, Random(14), 1.5 * ONE_CELL)
    set_direction(state, Direction.DOWN)
    run_for(state, SETTINGS, Random(14), 1.5 * ONE_CELL)
    assert state.player.direction == Direction.DOWN


def test_big_dt_crosses_multiple_cells(
    empty_state: GameState,
) -> None:
    """Speed 8 for 0.25 s enters 2 cells: while, not if."""
    state: GameState = empty_state
    entity = state.player
    entity.next_direction = Direction.RIGHT
    entered = advance(entity, state.maze, 8.0, 0.25)
    assert len(entered) == 2


def test_huge_dt_is_clamped(empty_state: GameState) -> None:
    """A 10 s frame (debugger pause) behaves like one short frame."""
    state: GameState = empty_state
    entity = state.player
    entity.next_direction = Direction.RIGHT
    entered = advance(entity, state.maze, 8.0, 10.0)
    assert len(entered) == 2


def test_remainder_carries_over(empty_state: GameState) -> None:
    """Distance is conserved: entered cells plus progress matches."""
    state: GameState = empty_state
    entity = Entity.standing_at(EntityKind.PLAYER, Cell(0, 2))
    entity.next_direction = Direction.RIGHT
    entered_all: list[Cell] = []
    for _ in range(30):
        entered_all += advance(entity, state.maze, 1.0, 0.1)
    total = len(entered_all) + entity.progress
    assert abs(total - 3.0) < 1e-9


def test_can_go_rejects_none(empty_state: GameState) -> None:
    """None direction is never walkable, with no caller check."""
    state: GameState = empty_state
    assert can_go(state.maze, Cell(2, 2), None) is False


def test_turn_request_wins_over_straight(
    empty_state: GameState,
) -> None:
    """choose_direction prefers an open next_direction."""
    state: GameState = empty_state
    picked = choose_direction(
        state.maze, Cell(2, 2), Direction.RIGHT, Direction.DOWN
    )
    assert picked == Direction.DOWN
