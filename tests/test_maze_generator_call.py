"""Tests for the generator call in pacman.maze.adapter."""

import pytest

from pacman.errors import MazeError
from pacman.maze.adapter import call_generator
from pacman.maze.fake import (
    OPEN_3X3,
    FailingFactory,
    FakeFactory,
    NoisyFactory,
)


def test_seed_below_one_is_rejected() -> None:
    """Seed 0 means system entropy in the package, so it is refused."""
    with pytest.raises(MazeError, match="seed"):
        call_generator(size=(15, 15), seed=0, factory=FakeFactory(OPEN_3X3))


def test_generator_failure_becomes_maze_error() -> None:
    """A raw package exception never escapes the adapter."""
    with pytest.raises(MazeError):
        call_generator(size=(15, 15), seed=1, factory=FailingFactory())


def test_failure_keeps_the_original_exception() -> None:
    """The cause is chained, so debugging can reach the real error."""
    with pytest.raises(MazeError) as info:
        call_generator(size=(15, 15), seed=1, factory=FailingFactory())
    assert isinstance(info.value.__cause__, IndexError)


def test_perfect_false_is_passed_explicitly() -> None:
    """Subject V.4 requires PERFECT to be False, not left to a default."""
    factory = FakeFactory(OPEN_3X3)
    call_generator(size=(15, 15), seed=42, factory=factory)
    size, perfect, seed = factory.calls[0]
    assert perfect is False
    assert size == (15, 15)
    assert seed == 42


def test_package_output_is_captured(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Anything the package prints is routed away from stdout."""
    factory = NoisyFactory(OPEN_3X3, "MazeGenerator Warning: too small")
    call_generator(size=(15, 15), seed=1, factory=factory)
    assert "MazeGenerator Warning" not in capsys.readouterr().out


def test_grid_is_returned() -> None:
    """The call returns the raw grid, undecoded."""
    grid = call_generator(
        size=(3, 3), seed=1, factory=FakeFactory(OPEN_3X3)
    )
    assert grid == OPEN_3X3
