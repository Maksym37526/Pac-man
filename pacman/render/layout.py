"""Render geometry derived from a single number: the tile size.

Every pixel size (wall thickness, entity margin, dot radii, font,
HUD height, window) is a formula of ``tile``, so changing the tile
size cannot leave one of them behind. Nothing here imports pygame,
so it is unit-testable (tests/test_layout.py).
"""

from __future__ import annotations

from dataclasses import dataclass

TILE_SIZES: tuple[int, ...] = (64, 48, 32, 24, 16)
"""Tile sizes the sprite sets will be authored for (refactor step 3).

There is no scaling primitive (see graphics_library.md), so sprites
cannot be stretched: each size needs its own pre-made set.
"""

WINDOW_BUDGET: tuple[int, int] = (1920, 1080)
"""Largest window (width, height) we aim for, in pixels."""

MIN_TILE = 8


@dataclass(frozen=True)
class Layout:
    """All pixel sizes for one run, fixed at startup (decision D3).

    Attributes:
        tile: Pixels per maze cell.
        wall: Wall thickness.
        entity_margin: Gap around an entity drawn as a plain square.
        pacgum_radius: Half-size of an ordinary pacgum.
        super_radius: Half-size of a super-pacgum.
        font_size: Font size for HUD and screen text.
        hud_height: Height of the HUD strip under the maze.
        window_width: Window width, from the largest level.
        window_height: Window height, from the largest level, plus HUD.
    """

    tile: int
    wall: int
    entity_margin: int
    pacgum_radius: int
    super_radius: int
    font_size: int
    hud_height: int
    window_width: int
    window_height: int

    @property
    def hud_top(self) -> int:
        """Y of the first HUD row."""
        return self.window_height - self.hud_height

    def maze_origin(self, cols: int, rows: int) -> tuple[int, int]:
        """Top-left pixel of a maze, centred in the area above the HUD.

        Args:
            cols: Maze width in cells.
            rows: Maze height in cells.

        Returns:
            (x, y) of the maze's top-left corner.
        """
        area_height = self.window_height - self.hud_height
        return (
            (self.window_width - cols * self.tile) // 2,
            (area_height - rows * self.tile) // 2,
        )

    def cell_origin(
        self, origin: tuple[int, int], col: float, row: float
    ) -> tuple[int, int]:
        """Pixel of a (possibly fractional) cell position.

        Args:
            origin: Maze origin from ``maze_origin``.
            col: Column, fractional while an entity is between cells.
            row: Row, likewise.

        Returns:
            (x, y) of that position's top-left corner.
        """
        return (
            origin[0] + int(col * self.tile),
            origin[1] + int(row * self.tile),
        )


def make_layout(tile: int, max_cols: int, max_rows: int) -> Layout:
    """Build a Layout from a tile size and the largest level's size.

    Args:
        tile: Pixels per cell, at least MIN_TILE.
        max_cols: Width in cells of the widest level.
        max_rows: Height in cells of the tallest level.

    Returns:
        The derived layout.

    Raises:
        ValueError: If the tile is too small or a size is not positive.
    """
    if tile < MIN_TILE:
        raise ValueError(f"tile {tile} is below the minimum {MIN_TILE}")
    if max_cols < 1 or max_rows < 1:
        raise ValueError(f"level size {max_cols}x{max_rows} must be positive")
    window_width = max_cols * tile
    window_height = max_rows * tile
    # Font size scales with window size, not just tile size
    font_size = max(16, min(window_width, window_height) // 20)
    hud_height = font_size * 2
    return Layout(
        tile=tile,
        wall=max(1, tile // 8),
        entity_margin=max(1, tile // 8),
        pacgum_radius=max(1, tile // 10),
        super_radius=max(2, tile * 3 // 16),
        font_size=font_size,
        hud_height=hud_height,
        window_width=window_width,
        window_height=window_height + hud_height,
    )


def fit_layout(
    max_cols: int,
    max_rows: int,
    budget: tuple[int, int] = WINDOW_BUDGET,
    tile_sizes: tuple[int, ...] = TILE_SIZES,
) -> Layout:
    """Pick the largest authored tile size whose window fits the budget.

    If even the smallest does not fit (a huge level), the smallest is
    used anyway: a big window beats an unplayable one.

    Args:
        max_cols: Width in cells of the widest level.
        max_rows: Height in cells of the tallest level.
        budget: Largest acceptable (width, height) in pixels.
        tile_sizes: Candidate tile sizes.

    Returns:
        The chosen layout.
    """
    candidates = sorted(tile_sizes, reverse=True)
    for tile in candidates:
        layout = make_layout(tile, max_cols, max_rows)
        if (
            layout.window_width <= budget[0]
            and layout.window_height <= budget[1]
        ):
            return layout
    return make_layout(candidates[-1], max_cols, max_rows)
