"""Shared fixtures for the core test suite."""

import pytest
from random import Random

from pacman.core.state import GameState, new_game_state
from pacman.maze.adapter import make_maze
from pacman.maze.fake import open_grid
from pacman.maze.layout import gen_layout
from pacman.maze.normalize import normalize


@pytest.fixture
def empty_state() -> GameState:
    """Open 5x5 maze, player at centre (2, 2), nothing placed."""
    maze = normalize(make_maze(open_grid(5, 5)))
    layout = gen_layout(maze, 0, Random(7))
    state = new_game_state(maze, layout)
    state.pacgums.clear()
    state.super_pacgums.clear()
    return state
