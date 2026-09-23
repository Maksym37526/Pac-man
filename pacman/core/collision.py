"""Touch detection between the player and a ghost (Phase 6).

Two checks, because one is not enough. Proximity catches the
ordinary case: the world positions are close. The swap check
catches the head-on pass: the two entities exchanged cells in one
tick and were never in the same cell at any tick boundary.
"""

import math

from pacman.core.entity import Entity


def world_position(entity: Entity) -> tuple[float, float]:
    """Fractional position of an entity, in cell units.

    The same interpolation the renderer (B) uses to draw: between
    ``prev_cell`` and ``cell`` by ``progress``. A standing entity
    has equal cells, so this yields exactly that cell with no
    special case.

    Args:
        entity: The entity to locate.

    Returns:
        The (x, y) world position.
    """
    progress = entity.progress
    x = entity.prev_cell.col + (
        entity.cell.col - entity.prev_cell.col
    ) * progress
    y = entity.prev_cell.row + (
        entity.cell.row - entity.prev_cell.row
    ) * progress
    return (x, y)


def has_swapped(first: Entity, second: Entity) -> bool:
    """Whether two entities exchanged cells this tick.

    Args:
        first: One entity, typically the player.
        second: The other entity, typically a ghost.

    Returns:
        True if each one is where the other one was.
    """
    return (
        first.cell == second.prev_cell
        and first.prev_cell == second.cell
    )


def is_touching(
    player: Entity, ghost: Entity, radius: float
) -> bool:
    """Whether the player touches a ghost (REQ-081).

    Args:
        player: The player entity.
        ghost: One ghost entity.
        radius: Touch distance in cell units.

    Returns:
        True on a cell swap or when the world distance fits.
    """
    if has_swapped(player, ghost):
        return True
    px, py = world_position(player)
    gx, gy = world_position(ghost)
    return math.hypot(px - gx, py - gy) <= radius
