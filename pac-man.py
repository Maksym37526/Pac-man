"""Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py config.json
"""

import sys
from pacman.data.cli import parse
from pacman.data.loader import read_config, strip_comments, parse_json
from pacman.errors import ConfigError
from pacman.log import setup_logging
from pacman.data.validator import validate_config
from pacman.data.config import build_config


def main(argv: list[str]) -> int:
    """Run the game.

    Args:
        argv: Command line arguments, excluding the program name.

    Returns:
        Process exit code: 0 on success, non-zero on error.
    """
    setup_logging()
    try:
        config_parse = parse(argv)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Usage: python3 pac-man.py config.json", file=sys.stderr)
        return 2
    try:
        raw_text = read_config(config_parse)
        text = strip_comments(raw_text)
        validated = validate_config(parse_json(text))
        build_config(validated)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print("pac-man: skeleton", argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
