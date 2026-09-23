"""Assembling one playable level.

Glues the three maze steps together — generate, normalise, lay out — and
decides which seed each level is generated from.
"""

from random import Random
from typing import Final

from pacman.maze.adapter import generate_maze
from pacman.maze.layout import MazeLayout, gen_layout
from pacman.maze.model import Maze
from pacman.maze.normalize import normalize

MAX_SEED: Final[int] = 999_999_999
"""Upper bound for a generated seed, matching the config spec."""


def level_seed(config_seed: int, level_index: int, rng: Random) -> int:
    """Return the maze seed for one level.

    Subject VI.1 asks for a fixed seed on the first level and a randomly
    generated maze on every level after it. The randomness is drawn from
    the run's own generator rather than the global module, which the
    maze package resets (PKG-4), and stays at or above 1 because the
    package treats 0 and negatives as "seed from system entropy"
    (PKG-1).

    Args:
        config_seed: Top-level seed from the config, already >= 1.
        level_index: Zero-based level number.
        rng: The run's random source.

    Returns:
        The seed to generate this level's maze with.
    """
    if level_index == 0:
        return config_seed
    return rng.randrange(1, MAX_SEED + 1)


def build_level(
    width: int,
    height: int,
    pacgums: int,
    level_index: int,
    config_seed: int,
    rng: Random,
) -> tuple[Maze, MazeLayout]:
    """Build one level, from generator call to finished layout.

    Args:
        width: Maze width from the level config, already validated.
        height: Maze height from the level config.
        pacgums: Requested pacgum count; clamped to the space available.
        level_index: Zero-based level number, deciding the seed.
        config_seed: Top-level seed from the config.
        rng: The run's random source, used for the seed and the layout.

    Returns:
        The normalised maze and the starting layout for it.

    Raises:
        MazeError: If the generator fails or the maze is unusable.
    """
    seed = level_seed(config_seed, level_index, rng)
    maze = normalize(generate_maze(size=(width, height), seed=seed))
    return maze, gen_layout(maze, pacgums, rng)
