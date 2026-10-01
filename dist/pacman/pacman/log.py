import logging
import os
import sys
from typing import Dict, Final


ALLOWED_LEVELS: Final[Dict[str, int]] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
LOGGING_LEVEL: Final[int] = logging.INFO
LOGGER_NAME: Final[str] = "pacman"
FORMAT_STR: Final[str] = "pac-man: %(levelname)s: %(message)s"


class LowercaseFormatter(logging.Formatter):
    """Format log records with lowercase level names."""

    def format(self, record: logging.LogRecord) -> str:
        original_levelname = record.levelname
        try:
            record.levelname = original_levelname.lower()
            return super().format(record)
        finally:
            record.levelname = original_levelname


def stdout_filter(record: logging.LogRecord) -> bool:
    """Allow records below WARNING to be written to standard output."""
    return record.levelno < logging.WARNING


def setup_logging() -> None:
    """Configure the Pac-Man logger and its standard output handlers."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.propagate = False
    while logger.handlers:
        logger.removeHandler(logger.handlers[0])
    env_level = os.environ.get("PACMAN_LOG_LEVEL")
    if env_level:
        level = ALLOWED_LEVELS.get(env_level, LOGGING_LEVEL)
    else:
        level = LOGGING_LEVEL
    logger.setLevel(level)
    formatter = LowercaseFormatter(FORMAT_STR)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(stdout_filter)
    # Створюємо stderr handler (для WARNING, ERROR, CRITICAL)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(formatter)
    # Додаємо обидва канали до головного логера
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)


def get_logger(module_name: str) -> logging.Logger:
    """Return the logger associated with a module name.

      Always pass ``__name__``. The returned logger must live under the
    ``pacman`` namespace to inherit the handlers configured by
    ``setup_logging``; a name outside that namespace will not be routed to
    stdout and stderr correctly.

    Args:
        module_name: The calling module's ``__name__``."""

    return logging.getLogger(module_name)
