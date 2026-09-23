class PacmanError(Exception):
    """Base class for Pacman errors."""


class ConfigError(PacmanError):
    """Raised when there is no config file, unreadable or corrupted."""


class MazeError(PacmanError):
    """Raised when maze generation fails or invariants are violated."""


class HighScoreError(PacmanError):
    """Raised when highscores cannot be loaded, processed, or saved."""
