"""Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py config.json
"""

from pydoc import cli
import sys
from pacman.data.cli import parse


def main(argv: list[str]) -> int:
    """Run the game.

    Args:
        argv: Command line arguments, excluding the program name.

    Returns:
        Process exit code: 0 on success, non-zero on error.
    """
    try:
        config_file = parse(argv)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    print("pac-man: skeleton", argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
