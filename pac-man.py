"""Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py config.json
"""

import sys


def main(argv: list[str]) -> int:
    """Run the game.

    Args:
        argv: Command line arguments, excluding the program name.

    Returns:
        Process exit code: 0 on success, non-zero on error.
    """
    print("pac-man: skeleton", argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
