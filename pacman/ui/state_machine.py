"""Application state machine: owns AppState and menu navigation.

Reacts to InputEvent, never to raw pygame or facade types. Produces
the AppState and payload that render.draw_screen consumes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from pacman.ui.events import InputEvent, TypedChar
MAX_NAME_LENGTH = 10  # V.5: max 10 characters, alphanumeric and spaces only


@dataclass(frozen=True)
class GameOverPayload:
    """What draw_screen needs to draw the game-over screen."""
    final_score: int


@dataclass(frozen=True)
class NameEntryPayload:
    """What draw_screen needs to draw the name-entry screen."""
    name: str


@dataclass(frozen=True)
class HighscoresPayload:
    """What draw_screen needs to draw the highscore list.

    Attributes:
        entries: (name, score) pairs, already sorted/limited to top 10.
            Filled by the composer from load_highscores/save_score.
    """
    entries: list[tuple[str, int]]


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
    state: AppState = AppState.MAIN_MENU
    menu_index: int = 0
    name_buffer: str = ""
    confirmed_name: str | None = None

    def handle(self, event: InputEvent | TypedChar) -> None:
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
        elif self.state is AppState.GAME_OVER:
            self._handle_game_over(event)
        elif self.state is AppState.VICTORY:
            self._handle_victory(event)
        elif self.state is AppState.NAME_ENTRY:
            self._handle_name_entry(event)

    def _handle_victory(self, event: InputEvent | TypedChar) -> None:
        """Confirm/back moves to NAME_ENTRY, carrying the final score."""
        if event is InputEvent.SELECT or event is InputEvent.BACK:
            self.name_buffer = ""
            self.state = AppState.NAME_ENTRY

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
        """Pause on PAUSE or BACK; movement is core's job.

        Escape arrives as BACK (translate is stateless, §5), so
        PLAYING treats it as pause-enter: P or Esc pauses.
        """
        if event is InputEvent.PAUSE or event is InputEvent.BACK:
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

    def _handle_name_entry(self, event: InputEvent | TypedChar) -> None:
        """Build up to 10 ASCII alphanumeric-or-space characters, then confirm.

        Matches the highscore contract (REQ-065, decision A):
        NAME_PATTERN is [A-Za-z0-9 ]{1,10}, so anything else would
        be normalised to "PLAYER" in save_score. Filter here so the
        screen never shows a name the table cannot keep.
        On SELECT the typed name lands in confirmed_name for the
        composer to save; on BACK confirmed_name is None (skip).
        Either way the buffer is cleared and we return to MAIN_MENU.
        """
        if isinstance(event, TypedChar):
            char = event.char
            if (
                len(char) == 1
                and char.isascii()
                and (char.isalnum() or char == " ")
                and len(self.name_buffer) < MAX_NAME_LENGTH
            ):
                self.name_buffer += char
        elif event is InputEvent.TEXT_BACKSPACE:
            self.name_buffer = self.name_buffer[:-1]
        elif event is InputEvent.SELECT:
            self.confirmed_name = self.name_buffer
            self.name_buffer = ""
            self.state = AppState.MAIN_MENU
        elif event is InputEvent.BACK:
            self.confirmed_name = None
            self.name_buffer = ""
            self.state = AppState.MAIN_MENU

    def name_entry_payload(self) -> NameEntryPayload:
        """Snapshot of the name currently being typed."""
        return NameEntryPayload(name=self.name_buffer)

    def _handle_game_over(self, event: InputEvent) -> None:
        """Confirm/back moves to NAME_ENTRY, same flow as victory."""
        if event is InputEvent.SELECT or event is InputEvent.BACK:
            self.name_buffer = ""
            self.state = AppState.NAME_ENTRY


@dataclass(frozen=True)
class MainMenuPayload:
    """What draw_screen needs to draw the main menu.

    Attributes:
        selected_index: Index into the menu items, for highlighting.
    """
    selected_index: int


@dataclass(frozen=True)
class VictoryPayload:
    """What draw_screen needs to draw the victory screen.

    Attributes:
        final_score: The player's score at the moment of winning.
    """
    final_score: int
