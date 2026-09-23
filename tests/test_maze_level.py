"""Tests for level seeding: pacman.maze.level (REQ-072, REQ-073)."""

from random import Random

from pacman.maze.level import MAX_SEED, build_level, level_seed


def test_level_zero_uses_config_seed() -> None:
    """Level 1 is generated with the fixed config seed."""
    assert level_seed(42, 0, Random(7)) == 42


def test_later_levels_draw_from_rng() -> None:
    """Levels 2+ draw a usable seed from the run's generator."""
    seed = level_seed(42, 1, Random(7))
    assert 1 <= seed <= MAX_SEED


def test_same_rng_reproduces_level_seed() -> None:
    """The same generator state always yields the same level seed."""
    first = level_seed(42, 3, Random(7))
    second = level_seed(42, 3, Random(7))
    assert first == second


def test_level_one_differs_across_runs() -> None:
    """Two fresh generators give different seeds for level 2+."""
    first = level_seed(42, 1, Random())
    second = level_seed(42, 1, Random())
    assert first != second


def test_level_zero_maze_is_reproducible() -> None:
    """The same config seed builds an identical level 1 maze."""
    first, _ = build_level(21, 21, 0, 0, 42, Random(7))
    second, _ = build_level(21, 21, 0, 0, 42, Random(7))
    assert first.passages == second.passages
    assert first.blocks == second.blocks
