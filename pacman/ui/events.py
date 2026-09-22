"""Input translation: pygame-free events for the UI state machine.

Consumes RawEvent from the graphics facade (already stripped of
pygame types) and produces InputEvent, the only event type ui/ and
core logic ever see.
"""

from __future__ import annotations

from enum import Enum, auto

from pacman.render.facade import RawEvent


class InputEvent(Enum):
    """An abstract input the game reacts to, independent of any backend."""
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    SELECT = auto()
    BACK = auto()
    PAUSE = auto()
    QUIT = auto()


_KEY_MAP: dict[str, InputEvent] = {
    "up": InputEvent.UP,
    "w": InputEvent.UP,
    "down": InputEvent.DOWN,
    "s": InputEvent.DOWN,
    "left": InputEvent.LEFT,
    "a": InputEvent.LEFT,
    "right": InputEvent.RIGHT,
    "d": InputEvent.RIGHT,
    "return": InputEvent.SELECT,
    "space": InputEvent.SELECT,
    "escape": InputEvent.BACK,
    "p": InputEvent.PAUSE,
}


def translate(raw_events: list[RawEvent]) -> list[InputEvent]:
    """Convert a batch of RawEvent into InputEvent, dropping unmapped keys.

    Args:
        raw_events: Events from GraphicsFacade.poll_events().

    Returns:
        Translated events, in the same order, skipping anything with
        no mapping (e.g. keys we don't use, keyup events).
    """
    translated: list[InputEvent] = []
    for raw in raw_events:
        if raw.kind == "quit":
            translated.append(InputEvent.QUIT)
        elif raw.kind == "keydown" and raw.key in _KEY_MAP:
            translated.append(_KEY_MAP[raw.key])
    return translated