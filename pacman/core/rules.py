"""One game tick: movement, eating, win check (Phase 5).

The only writer of GameState. The renderer reads the state and
never mutates it.
"""

from typing import Final

from pacman.core.events import GameEvent
from pacman.core.movement import advance
from pacman.core.state import GameState, ScoringRules
from pacman.maze.model import Direction

PLAYER_SPEED: Final[float] = 8.0
"""Player speed in cells per second (open point 2, playtesting)."""


def set_direction(state: GameState, direction: Direction) -> None:
    """Store the player's desired turn.

    Takes a Direction, not an InputEvent: InputEvent lives in
    ui/, which core must not import. The composition layer
    translates MOVE_* into Direction and calls this.

    Args:
        state: The game state to update.
        direction: The desired travel direction.
    """
    state.player.next_direction = direction


def tick(
    state: GameState, scoring: ScoringRules, dt: float
) -> list[GameEvent]:
    """Advance the game by dt seconds.

    Moves the player, eats whatever is on every entered cell,
    and reports a win exactly once, on the tick that clears
    the last pacgum.

    Args:
        state: The game state, mutated in place.
        scoring: Points for each edible event.
        dt: Seconds since the last tick.

    Returns:
        Events that happened during this tick, in order.
    """
    events: list[GameEvent] = []
    entered = advance(state.player, state.maze, PLAYER_SPEED, dt)
    ate_something = False
    for cell in entered:
        if cell in state.pacgums:
            state.pacgums.discard(cell)
            state.score += scoring.pacgum
            events.append(GameEvent.PACGUM_EATEN)
            ate_something = True
        if cell in state.super_pacgums:
            state.super_pacgums.discard(cell)
            state.score += scoring.super_pacgum
            events.append(GameEvent.SUPER_PACGUM_EATEN)
            ate_something = True
    if (
        ate_something
        and not state.pacgums
        and not state.super_pacgums
    ):
        events.append(GameEvent.LEVEL_CLEARED)
    return events
