from collections import deque
from pacman.errors import MazeError
from pacman.maze.model import Cell, step, Maze
from pacman.maze.adapter import RawMaze
from pacman.log import get_logger

logger = get_logger(__name__)
MIN_REACHABLE_CELLS = 5
"""Player start plus one ghost per corner, as subject VI.1 requires."""


def reachable_from(raw: RawMaze, start: Cell) -> set[Cell]:
    """Return every cell reachable from a starting cell.

    Breadth-first search across open passages. Directions leading out of
    the grid were already dropped by the adapter, so no bounds check is
    needed here.

    Args:
        raw: The decoded maze to explore.
        start: The cell to start from.

    Returns:
        Every cell reachable from ``start``, including ``start`` itself.
        An empty set if ``start`` is a block or lies outside the grid.
    """
    if start not in raw.passages:
        return set()  # Start cell is blocked or out of bounds
    queue = deque([start])
    visited = {start}
    while queue:
        current_cell = queue.popleft()
        for direction in raw.passages[current_cell]:
            neighbour = step(current_cell, direction)
            if neighbour not in visited and neighbour in raw.passages:
                visited.add(neighbour)
                queue.append(neighbour)
    return visited


def nearest_reachable(target: Cell, reachable: set[Cell]) -> Cell:
    """Return the reachable cell closest to a target.

    Distance is Manhattan, which matches four-directional movement on a
    grid. Ties are broken by the cell itself, so the result depends only
    on the arguments and not on set iteration order: without that, adding
    an unrelated cell elsewhere could silently move the player's start.

    Args:
        target: The cell to get close to, typically the centre or a corner.
        reachable: Cells known to be reachable, from ``reachable_from``.

    Returns:
        The closest reachable cell, or ``target`` itself if it is in the set.

    Raises:
        MazeError: If ``reachable`` is empty.
    """
    if not reachable:
        raise MazeError(f"no reachable cell to place near {target}")
    return min(
        reachable,
        key=lambda c: (
            abs(target.col - c.col) + abs(target.row - c.row),
            c,
        ),
    )


def normalize(raw: RawMaze) -> Maze:
    """Turn a decoded grid into a maze the game can rely on.

    RawMaze is whatever the generator produced. Maze carries guarantees,
    and this is where they are established: every cell in the result is
    reachable from the player's start, and the centre and all four corners
    are walkable.

    Unreachable corridors are dropped rather than turned into blocks:
    blocks mean the generator's solid logo cells, which the renderer draws
    differently. A pacgum placed in an unreachable pocket would make the
    level impossible to finish, since subject VI.2 requires every pacgum
    to be eaten.

    One consequence: in the returned Maze, passages plus blocks no longer
    account for the whole grid. The difference is the number of cells
    dropped.

    Args:
        raw: The decoded maze, without guarantees.

    Returns:
        A maze whose centre and corners are walkable and whose every cell
        is reachable from the centre.

    Raises:
        MazeError: If the top-left corner is not walkable, or too few
            cells are reachable to place the player and four ghosts.
    """
    start_cell = Cell(0, 0)
    if start_cell not in raw.passages:
        raise MazeError(
            "the top-left corner is not walkable, so the maze cannot be "
            "explored from a known starting point"
        )
    reachable = reachable_from(raw, start_cell)
    if len(reachable) < MIN_REACHABLE_CELLS:
        raise MazeError(
            f"only {len(reachable)} reachable cells, need at least "
            f"{MIN_REACHABLE_CELLS} to place the player and four ghosts"
        )
    dropped = len(raw.passages) - len(reachable)
    if dropped:
        logger.warning(
            "maze has %d unreachable cell(s), dropped from the level",
            dropped,
        )

    def get_closest_walkable(target: Cell) -> Cell:
        if target in reachable:
            return target
        return nearest_reachable(target, reachable)

    geom_center = Cell(raw.width // 2, raw.height // 2)
    actual_center = get_closest_walkable(geom_center)
    actual_corners: tuple[Cell, Cell, Cell, Cell] = (
        get_closest_walkable(Cell(0, 0)),
        get_closest_walkable(Cell(raw.width - 1, 0)),
        get_closest_walkable(Cell(0, raw.height - 1)),
        get_closest_walkable(Cell(raw.width - 1, raw.height - 1))
    )
    filtered_passeges = {
        cell: directions
        for cell, directions in raw.passages.items()
        if cell in reachable
    }
    return Maze(
        width=raw.width,
        height=raw.height,
        passages=filtered_passeges,
        blocks=raw.blocks,
        centre=actual_center,
        corners=actual_corners
    )
