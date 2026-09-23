"""Command-line argument handling (T2.1)."""

from pacman.errors import ConfigError


def parse(argv: list[str]) -> str:
    """Return the config file path from command-line arguments.

    Args:
        argv: List of command-line arguments (excluding program name).

    Returns:
        Path to the config file.

    Raises:
        ConfigError: If argument count is wrong or file has no
            .json extension.
    """
    if len(argv) == 0:
        raise ConfigError("Missing config file argument.")
    if len(argv) > 1:
        raise ConfigError(
            f"Too many arguments: got {len(argv)}, expected 1"
        )
    if not argv[0].endswith(".json"):
        raise ConfigError("Config file must have a .json extension")
    return argv[0]
