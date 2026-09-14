"""Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py config.json
"""

import sys
from pacman.data.cli import parse
from pacman.data.loader import read_config, strip_comments
from pacman.errors import ConfigError


def main(argv: list[str]) -> int:
    """Run the game.

    Args:
        argv: Command line arguments, excluding the program name.

    Returns:
        Process exit code: 0 on success, non-zero on error.
    """
    try:
        config_parse = parse(argv)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Usage: python3 pac-man.py config.json", file=sys.stderr)
        return 2
    try:
        text = read_config(config_parse)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    text = strip_comments(text)
    print("pac-man: skeleton", argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
