"""Placing the player, ghosts and pacgums in a normalised maze.

Layout is kept separate from Maze because the two have different
lifetimes: the maze is fixed for the level, while pacgums disappear as
they are eaten.
"""
from dataclasses import dataclass
from random import Random
from pacman.log import get_logger

from pacman.maze.model import Cell, Maze
logger = get_logger(__name__)


@dataclass(frozen=True)
class MazeLayout:
    """Where everything starts on one level.

    Attributes:
        player_start: The maze centre, guaranteed walkable.
        ghost_starts: One corner per ghost, in the maze's corner order.
        super_pacgums: The same four corners. Subject VI.1 places ghosts
            and super-pacgums in the corners, so they coincide at level
            start; this is intentional, not an oversight.
        pacgums: Ordinary pacgums, excluding the player's start cell and
            the four corners.
    """
    player_start: Cell
    ghost_starts: tuple[Cell, Cell, Cell, Cell]
    super_pacgums: frozenset[Cell]
    pacgums: frozenset[Cell]


def fit_pacgum(requested_count: int, avail_slots: int) -> int:
    """Clamp a requested pacgum count to the space actually available.

    The upper bound is only known after maze generation and
    normalisation, so it cannot be enforced by config validation.

    Args:
        requested_count: Pacgum count from the level config.
        avail_slots: Cells left after the player start and corners are
            removed.

    Returns:
        A count that fits, logging a warning if it had to be reduced.
    """
    if requested_count < 0:
        return 0
    if requested_count > avail_slots:
        logger.warning(
            "Requested pacgum count (%d) exceeds available corridor slots "
            "(%d). Clamping count down to maximum available space.",
            requested_count,
            avail_slots,
        )
        return avail_slots
    return requested_count


def gen_layout(maze: Maze,
               requested_pacgums: int,
               random_source: Random) -> MazeLayout:
    """Place everything a level needs inside a normalised maze.

    Pacgums are spread at random rather than filling every corridor. See
    the REQ-074 entry in the requirements matrix for why: filling the
    maze makes a level unwinnable within the configured time limit.

    Candidates are sorted before sampling, so the same generator state
    always produces the same layout. Without that, set iteration order
    would make the result depend on hash randomisation.

    Args:
        maze: A normalised maze; its centre and corners are walkable.
        requested_pacgums: Pacgum count from the level config.
        random_source: The run's random source. Never the global
            `random` module, which the maze package resets (PKG-4).

    Returns:
        The starting layout for one level.
    """
    player_start = maze.centre
    ghost_starts = maze.corners
    super_pacgums = frozenset(maze.corners)
    if len(super_pacgums) < 4:
        logger.warning(
            "Normalisation compressed ghost corners down to %d unique "
            "coordinates. Spawning fewer than 4 super-pacgums "
            "accordingly.",
            len(super_pacgums),
        )
    excluded_cells = {player_start}.union(super_pacgums)
    candidates = maze.walkable_cells - excluded_cells
    final_count = fit_pacgum(requested_pacgums, len(candidates))
    sort_candidates = sorted(candidates)
    sampled_cells = random_source.sample(sort_candidates, k=final_count)
    return MazeLayout(
        player_start=player_start,
        ghost_starts=ghost_starts,
        super_pacgums=super_pacgums,
        pacgums=frozenset(sampled_cells),
    )
