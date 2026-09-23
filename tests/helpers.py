"""Shared step-splitting helper for the core test suite."""

from pacman.core.events import GameEvent
from pacman.core.movement import MAX_DT
from pacman.core.rules import tick
from pacman.core.state import GameState, ScoringRules


def run_for(
    state: GameState, scoring: ScoringRules, seconds: float
) -> list[GameEvent]:
    """Tick in steps of at most MAX_DT, collecting every event.

    A single tick with dt above MAX_DT is silently clamped by
    advance, so slow speeds would cover less distance than asked.
    Splitting keeps every step whole on any speed.
    """
    events: list[GameEvent] = []
    remaining = seconds
    while remaining > 0.0:
        step = min(MAX_DT, remaining)
        events += tick(state, scoring, step)
        remaining -= step
    return events
