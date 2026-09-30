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
    CHEAT_MASTER = auto()
    CHEAT_INVINCIBLE = auto()
    CHEAT_FAST = auto()
    CHEAT_SKIP = auto()
    CHEAT_CLEAR = auto()
    CHEAT_FRIGHT = auto()
    CHEAT_LOSE = auto()


_KEY_MAP: dict[str, InputEvent] = {
    "up": InputEvent.UP, "w": InputEvent.UP,
    "down": InputEvent.DOWN, "s": InputEvent.DOWN,
    "left": InputEvent.LEFT, "a": InputEvent.LEFT,
    "right": InputEvent.RIGHT, "d": InputEvent.RIGHT,
    "return": InputEvent.SELECT, "space": InputEvent.SELECT,
    "escape": InputEvent.BACK,
    "p": InputEvent.PAUSE,
    "backspace": InputEvent.TEXT_BACKSPACE,
    # Cyrillic homologs (JCUKEN): same physical keys with a
    # Russian layout active. Name entry is unaffected: printable
    # unicode wins over this map there, so letters still type.
    "ц": InputEvent.UP, "ф": InputEvent.LEFT,
    "ы": InputEvent.DOWN, "в": InputEvent.RIGHT,
    "з": InputEvent.PAUSE,
    "1": InputEvent.CHEAT_MASTER,
    "2": InputEvent.CHEAT_INVINCIBLE,
    "3": InputEvent.CHEAT_FAST,
    "4": InputEvent.CHEAT_SKIP,
    "5": InputEvent.CHEAT_CLEAR,
    "6": InputEvent.CHEAT_FRIGHT,
    "7": InputEvent.CHEAT_LOSE,
}


def translate(
    raw_events: list[RawEvent], *, name_entry: bool = False
) -> list[InputEvent | TypedChar]:
    """Convert RawEvent into InputEvent/TypedChar, dropping unmapped keys.

    Args:
        raw_events: This frame's facade events.
        name_entry: True while the name-entry screen is open. WASD,
            space and P double as game keys, so printable characters
            win over _KEY_MAP here (return/escape/backspace carry no
            printable unicode and keep their control meaning).
    """
    translated: list[InputEvent | TypedChar] = []
    for raw in raw_events:
        if raw.kind == "quit":
            translated.append(InputEvent.QUIT)
        elif raw.kind == "keydown":
            if (
                name_entry
                and raw.unicode
                and raw.unicode.isprintable()
            ):
                translated.append(TypedChar(raw.unicode))
            elif raw.key in _KEY_MAP:
                translated.append(_KEY_MAP[raw.key])
            elif raw.unicode.isprintable() and raw.unicode:
                translated.append(TypedChar(raw.unicode))
    return translated
