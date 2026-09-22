"""Application state machine: owns AppState and menu navigation.

Reacts to InputEvent, never to raw pygame or facade types. Produces
the AppState and payload that render.draw_screen consumes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from pacman.ui.events import InputEvent


class AppState(Enum):
    """Taken directly from subject IV and VI.8. No states beyond these."""
    MAIN_MENU = auto()
    INSTRUCTIONS = auto()
    HIGHSCORES = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    NAME_ENTRY = auto()
    EXIT = auto()


class MainMenuItem(Enum):
    """The four entries on the main menu, in display order (VI.8)."""
    START_GAME = auto()
    VIEW_HIGHSCORES = auto()
    INSTRUCTIONS = auto()
    EXIT = auto()


_MAIN_MENU_ORDER = [
    MainMenuItem.START_GAME,
    MainMenuItem.VIEW_HIGHSCORES,
    MainMenuItem.INSTRUCTIONS,
    MainMenuItem.EXIT,
]

MAIN_MENU_LABELS: dict[MainMenuItem, str] = {
    MainMenuItem.START_GAME: "Start Game",
    MainMenuItem.VIEW_HIGHSCORES: "View Highscores",
    MainMenuItem.INSTRUCTIONS: "Instructions",
    MainMenuItem.EXIT: "Exit",
}


@dataclass
class AppStateMachine:
    """Current AppState plus whatever selection state that state needs.

    Attributes:
        state: The current AppState.
        menu_index: Index into _MAIN_MENU_ORDER, only meaningful while
            state is MAIN_MENU.
    """
    state: AppState = AppState.MAIN_MENU
    menu_index: int = 0

    def handle(self, event: InputEvent) -> None:
        """Apply one input event, possibly changing state in place."""
        if event is InputEvent.QUIT:
            self.state = AppState.EXIT
            return

        if self.state is AppState.MAIN_MENU:
            self._handle_main_menu(event)
        elif self.state is AppState.INSTRUCTIONS:
            self._handle_instructions(event)
        elif self.state is AppState.HIGHSCORES:
            self._handle_highscores(event)
        elif self.state is AppState.PLAYING:
            self._handle_playing(event)
        elif self.state is AppState.PAUSED:
            self._handle_paused(event)
        # GAME_OVER, VICTORY, NAME_ENTRY: not yet handled, see caveat below.

    def _handle_main_menu(self, event: InputEvent) -> None:
        """Navigate and select among the four main menu entries."""
        if event is InputEvent.UP:
            self.menu_index = (self.menu_index - 1) % len(_MAIN_MENU_ORDER)
        elif event is InputEvent.DOWN:
            self.menu_index = (self.menu_index + 1) % len(_MAIN_MENU_ORDER)
        elif event is InputEvent.SELECT:
            self._activate_main_menu_item(_MAIN_MENU_ORDER[self.menu_index])

    def _activate_main_menu_item(self, item: MainMenuItem) -> None:
        """Enter the state a main menu selection leads to."""
        if item is MainMenuItem.START_GAME:
            self.state = AppState.PLAYING
        elif item is MainMenuItem.VIEW_HIGHSCORES:
            self.state = AppState.HIGHSCORES
        elif item is MainMenuItem.INSTRUCTIONS:
            self.state = AppState.INSTRUCTIONS
        elif item is MainMenuItem.EXIT:
            self.state = AppState.EXIT

    def _handle_instructions(self, event: InputEvent) -> None:
        """Only BACK does anything here: return to the main menu."""
        if event is InputEvent.BACK:
            self.state = AppState.MAIN_MENU

    def _handle_highscores(self, event: InputEvent) -> None:
        """Only BACK does anything here: return to the main menu."""
        if event is InputEvent.BACK:
            self.state = AppState.MAIN_MENU

    def _handle_playing(self, event: InputEvent) -> None:
        """Only PAUSE is handled at this layer; movement is core's job."""
        if event is InputEvent.PAUSE:
            self.state = AppState.PAUSED

    def _handle_paused(self, event: InputEvent) -> None:
        """Resume on PAUSE, abandon the run on BACK (VI.8 pause menu)."""
        if event is InputEvent.PAUSE:
            self.state = AppState.PLAYING
        elif event is InputEvent.BACK:
            self.state = AppState.MAIN_MENU

    def main_menu_payload(self) -> MainMenuPayload:
        """Build the payload draw_screen needs for the current menu state."""
        return MainMenuPayload(selected_index=self.menu_index)

@dataclass(frozen=True)
class MainMenuPayload:
    """What draw_screen needs to draw the main menu.

    Attributes:
        selected_index: Index into the menu items, for highlighting.
    """
    selected_index: int