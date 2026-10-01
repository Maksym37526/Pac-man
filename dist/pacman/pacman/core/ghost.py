"""Ghost AI: greedy chase and flight (Phase 6, REQ-089-093).

Pure logic. This module knows nothing about score, events or
GameState: it answers one question, which way a ghost leaves the
cell it just entered.

Decision (REQ-091): greedy choice on the intersection, not a full
path search. For every exit direction the ghost looks at the cell
that direction leads to and picks the one closest to (chase) or
farthest from (flight) the player, by Manhattan distance. Per-ghost
randomness (a chance of a random turn instead) keeps the four
ghosts from collapsing into a single moving object.
"""

from random import Random

from pacman.maze.model import Cell, Direction, Maze, step


def manhattan(first: Cell, second: Cell) -> int:
    """Grid distance between two cells, in steps.

    Args:
        first: One cell.
        second: The other cell.

    Returns:
        Steps to walk in four directions, ignoring walls.
    """
    return abs(first.col - second.col) + abs(first.row - second.row)


def exit_candidates(
    maze: Maze, cell: Cell, direction: Direction | None
) -> list[Direction]:
    """Exits a ghost may take, without an immediate U-turn.

    The reverse of the travel direction is excluded, so a greedy
    ghost cannot oscillate between two cells forever. The only
    exception is a dead end: with no other way out, the reverse
    is the only candidate, otherwise the ghost would stall.

    Args:
        maze: The current level's maze.
        cell: The cell just entered.
        direction: Current travel direction, None when standing.

    Returns:
        Open directions in deterministic (name-sorted) order.
    """
    open_dirs = sorted(
        maze.passages.get(cell, frozenset()), key=lambda d: d.name
    )
    if direction is None:
        return open_dirs
    back = direction.opposite
    forward = [d for d in open_dirs if d is not back]
    if forward:
        return forward
    return [back] if back in open_dirs else []


def choose_ghost_direction(
    cell: Cell,
    candidates: list[Direction],
    target: Cell,
    fleeing: bool,
    randomness: float,
    rng: Random,
) -> Direction:
    """Pick one exit towards (or away from) the target cell.

    With probability ``randomness`` a random exit wins outright;
    otherwise the exit leading closest to the target wins when
    hunting and farthest when fleeing. Ties break by direction
    name, so the result never depends on enum declaration order.

    Args:
        cell: The cell the ghost is leaving from.
        candidates: Exits from ``exit_candidates``, not empty.
        target: The cell to chase or flee, the player's cell.
        fleeing: True for flight (maximise), False for chase.
        randomness: Chance of a random turn, 0.0 to 1.0.
        rng: The run's random source, never the global module.

    Returns:
        The chosen exit direction.
    """
    if rng.random() < randomness:
        return rng.choice(candidates)
    pick = max if fleeing else min
    return pick(
        candidates,
        key=lambda d: (manhattan(step(cell, d), target), d.name),
    )
