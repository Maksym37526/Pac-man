"""Input translation: pygame-free events for the UI state machine.

Consumes RawEvent from the graphics facade (already stripped of
pygame types) and produces InputEvent, the only event type ui/ and
core logic ever see.
"""

from __future__ import annotations

from enum import Enum, auto

from pacman.render.facade import RawEvent
from dataclasses import dataclass

@dataclass(frozen=True)
class TypedChar:
    """One typed character, for NAME_ENTRY. Not an InputEvent member
    because InputEvent (an Enum) cannot carry per-instance data."""
    char: str

class InputEvent(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    SELECT = auto()
    BACK = auto()
    PAUSE = auto()
    QUIT = auto()
    TEXT_BACKSPACE = auto()
    CHEAT_INVINCIBILITY = auto()
    CHEAT_LEVEL_SKIP = auto()
    CHEAT_GHOST_FREEZE = auto()
    CHEAT_EXTRA_LIFE = auto()
    CHEAT_SPEED = auto()



_KEY_MAP: dict[str, InputEvent] = {
    "up": InputEvent.UP, "w": InputEvent.UP,
    "down": InputEvent.DOWN, "s": InputEvent.DOWN,
    "left": InputEvent.LEFT, "a": InputEvent.LEFT,
    "right": InputEvent.RIGHT, "d": InputEvent.RIGHT,
    "return": InputEvent.SELECT, "space": InputEvent.SELECT,
    "escape": InputEvent.BACK,
    "p": InputEvent.PAUSE,
    "backspace": InputEvent.TEXT_BACKSPACE,
    "f1": InputEvent.CHEAT_INVINCIBILITY,
    "f2": InputEvent.CHEAT_LEVEL_SKIP,
    "f3": InputEvent.CHEAT_GHOST_FREEZE,
    "f4": InputEvent.CHEAT_EXTRA_LIFE,
    "f5": InputEvent.CHEAT_SPEED,
}


def translate(raw_events: list[RawEvent]) -> list[InputEvent | TypedChar]:
    """Convert RawEvent into InputEvent/TypedChar, dropping unmapped keys."""
    translated: list[InputEvent | TypedChar] = []
    for raw in raw_events:
        if raw.kind == "quit":
            translated.append(InputEvent.QUIT)
        elif raw.kind == "keydown":
            if raw.key in _KEY_MAP:
                translated.append(_KEY_MAP[raw.key])
            elif raw.unicode.isprintable() and raw.unicode:
                translated.append(TypedChar(raw.unicode))
    return translated