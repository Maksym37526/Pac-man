"""Discrete movement on the maze grid (D1).

Pure helpers over Entity and Maze. This module knows nothing about
score, pacgums or events: it only moves an entity and reports which
cells were entered.
"""

from typing import Final

from pacman.core.entity import Entity
from pacman.maze.model import Cell, Direction, Maze, step

MAX_DT: Final[float] = 0.25
"""Upper bound for one advance call, in seconds.

A huge frame (window drag, GC pause, debugger breakpoint) must not
send the entity spinning around a loop for thousands of cells.
Callers with a fixed-step loop clamp dt themselves as well, but
core never relies on the caller doing it right.

Phase 7 warning: the level timer must consume this same clamped
dt, not the raw frame time. Otherwise lag would eat the timer
while movement only covers the clamped fraction. Easiest fix is
to clamp once at tick entry and pass the result down here.
"""


def can_go(
    maze: Maze, cell: Cell, direction: Direction | None
) -> bool:
    """Whether an entity at a cell can leave in a direction.

    Args:
        maze: The current level's maze.
        cell: The cell to leave from.
        direction: The direction to try; None means no direction.

    Returns:
        True if the way is open, False for None or a wall.
    """
    if direction is None:
        return False
    return not maze.is_wall_between(cell, direction)


def choose_direction(
    maze: Maze,
    cell: Cell,
    direction: Direction | None,
    next_direction: Direction | None,
) -> Direction | None:
    """Pick the direction to take on entering a cell.

    The turn request wins if its way is open, otherwise the
    current direction continues if it is open, otherwise the
    entity stops.

    Args:
        maze: The current level's maze.
        cell: The cell just entered.
        direction: Current travel direction, None when standing.
        next_direction: Desired turn, None if no request.

    Returns:
        The direction to leave the cell with, or None to stop.
    """
    if can_go(maze, cell, next_direction):
        # mypy cannot narrow the Optional from can_go alone.
        assert next_direction is not None
        return next_direction
    if can_go(maze, cell, direction):
        assert direction is not None
        return direction
    return None


def advance(
    entity: Entity, maze: Maze, speed: float, dt: float
) -> list[Cell]:
    """Move an entity forward by dt seconds.

    Standing entities try to start via ``next_direction``. Moving
    entities accumulate ``speed * dt`` into progress; every cell
    boundary crossed picks a new direction and is reported, so no
    pacgum is ever skipped over on a long frame.

    Args:
        entity: The entity to move, mutated in place.
        maze: The current level's maze.
        speed: Cells per second, must be >= 0.
        dt: Seconds since the last tick, clamped to MAX_DT.

    Returns:
        Every cell entered during this call, in order. Empty if
        the entity did not reach a new cell.
    """
    if dt <= 0.0 or speed <= 0.0:
        return []
    if dt > MAX_DT:
        dt = MAX_DT
    entered: list[Cell] = []
    if entity.direction is None:
        wanted = entity.next_direction
        if not can_go(maze, entity.cell, wanted):
            return []
        assert wanted is not None
        entity.prev_cell = entity.cell
        entity.cell = step(entity.cell, wanted)
        entity.direction = wanted
    elif (
        entity.next_direction is entity.direction.opposite
        and 0.0 < entity.progress < 1.0
    ):
        # Instant 180° reversal, classic feel: finish the cell
        # first and turning feels laggy (up to a full cell at
        # low speed). Swap the segment and mirror progress, so
        # the position is unchanged and travel continues back.
        # At exact boundaries (progress 0) the commit logic
        # below already turns with no delay, so only mid-cell
        # reversals need this.
        entity.prev_cell, entity.cell = entity.cell, entity.prev_cell
        entity.progress = 1.0 - entity.progress
        entity.direction = entity.next_direction
    entity.progress += speed * dt
    while entity.progress >= 1.0:
        entity.progress -= 1.0
        entered.append(entity.cell)
        coming = choose_direction(
            maze, entity.cell, entity.direction,
            entity.next_direction,
        )
        if coming is None:
            entity.prev_cell = entity.cell
            entity.progress = 0.0
            entity.direction = None
            break
        entity.prev_cell = entity.cell
        entity.cell = step(entity.cell, coming)
        entity.direction = coming
    return entered
