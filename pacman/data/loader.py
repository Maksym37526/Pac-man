"""Loading and preprocessing of the configuration file."""

import re
import json
from pacman.errors import ConfigError


def read_config(path: str) -> str:
    """Read the configuration file and return its contents.

    Args:
        path: Path to the configuration file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise ConfigError(f"Cannot read config file '{path}': {e.strerror}")
    except UnicodeDecodeError as e:
        raise ConfigError(f"Cannot decode config file '{path}': {e.reason}")


COMMENT_REM = re.compile(
    r'"(?:\\.|[^"\\])*"'  # JSON string, kept as-is
    r"|#[^\n]*"  # hash comment to end of line
    r"|//[^\n]*"  # slash comment to end of line
    r"|/\*.*?\*/",  # block comment, possibly multiline
    re.DOTALL,
)


def _replace_comment(match: re.Match[str]) -> str:
    """Return the replacement text for a single regex match."""
    # full match (return all group of match as-is)
    found = match.group(0)
    if found.startswith('"'):
        return found
    return "\n" * found.count("\n")


def strip_comments(text: str) -> str:
    """Remove `#`, `//` and `/* */` comments from config text.

    JSON string literals are preserved byte-for-byte. Line
    numbering is kept intact: a removed block comment is replaced
    with the same number of newlines, so JSON errors (T2.4) point
    at the correct lines.

    Args:
        text: Raw configuration file contents.

    Returns:
        The text with all comments removed.
    """
    return COMMENT_REM.sub(_replace_comment, text)


def parse_json(text: str) -> dict:
    """Parse JSON text into a Python dictionary.

    Args:
        text: JSON text to parse.

    Returns:
        The parsed JSON as a Python dictionary.

    Raises:
        ConfigError: If the JSON is invalid.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}")
    if not isinstance(data, dict):
        raise ConfigError(
            f"Top-level must be an object, got {type(data).__name__}")
    return data
