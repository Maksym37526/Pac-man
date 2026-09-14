from ast import arg
import sys


def parse(argv: list[str]) -> str:
    """
    Parses command-line arguments and returns an exit code.

    Args:
        argv: List of command-line arguments (excluding the program name)."""
    if len(argv) == 0:
        raise ValueError("Missing config file argument.")
    if len(argv) > 1:
        raise ValueError(f"Too many arguments: got {len(argv)}, expected 1")
    if not argv[0].endswith(".json"):
        raise ValueError("Config file must have a .json extension")
    return argv[0]
