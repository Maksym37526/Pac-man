"""Offline sprite preparation (dev-only, not part of the game).

Slices the authored sheets in assets/ into individual frames and
upscales them with exact nearest-neighbor replication to the game
tile size. The game itself never scales: it only blits these files
1:1 via GraphicsFacade.load_image (mlx_png_file_to_image).

Sheets (all multiples of their base cell):
  PacManAssets-PacMan.png  32px cells, 4x3
    row 0: RIGHT  closed/slit, mid, wide, full
    row 1: NOT left mouths (pixel-verified: mouths face right,
      plus a vertical pill); skipped, renderer uses neutral
    row 2: death  shrink, dot, burst
  PacManAssets-Ghosts.png  32px cells, 4x11
    one row per color: 0 red, 1 blue, 2 pink, 3 orange
    (+ spare rows 4-7 unused for now)
    row 8 frightened, row 9 fright-blink, row 10 eyes+faces
      (top half of each row-10 cell: directional eyes)
  PacManAssets-Items.png   16px cells, 8x2
    row 1 col 0 small pacgum, col 1 super pacgum

Usage:
    python3 assets/upscale.py [tile]
Default tile is 64 (must divide evenly into the upscale factor:
32px cells need an even tile, 16px cells a multiple of 16).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

ASSETS = Path(__file__).resolve().parent
OUT = ASSETS / "gen"
BASE_PM = 32
BASE_DOT = 16

# (sheet, base_cell, col, row, out_name)
FRAMES: list[tuple[str, int, int, int, str]] = [
    # Pac-Man RIGHT / LEFT / vertical / death
    ("PacManAssets-PacMan.png", BASE_PM, 0, 0, "pm_right_0.png"),
    ("PacManAssets-PacMan.png", BASE_PM, 1, 0, "pm_right_1.png"),
    ("PacManAssets-PacMan.png", BASE_PM, 2, 0, "pm_right_2.png"),
    ("PacManAssets-PacMan.png", BASE_PM, 3, 0, "pm_right_3.png"),
    ("PacManAssets-PacMan.png", BASE_PM, 0, 2, "pm_death_0.png"),
    ("PacManAssets-PacMan.png", BASE_PM, 1, 2, "pm_death_1.png"),
    ("PacManAssets-PacMan.png", BASE_PM, 2, 2, "pm_death_2.png"),
    # Dots (16px base)
    ("PacManAssets-Items.png", BASE_DOT, 0, 1, "dot_small.png"),
    ("PacManAssets-Items.png", BASE_DOT, 1, 1, "dot_big.png"),
]

# Ghost body colors: (kind_index, sheet row). One row per color,
# four wave phases across the columns. Kind order follows
# GHOST_COLORS: GHOST_1 red, GHOST_2 pink, GHOST_3 blue, GHOST_4 orange.
GHOST_ROWS = {0: 0, 1: 2, 2: 1, 3: 3}

# (sheet, base_cell, col, row, half, out_name); half top/bottom for eyes.
GHOST_EXTRA: list[tuple[str, int, int, int, str, str]] = [
    ("PacManAssets-Ghosts.png", BASE_PM, 0, 8, "full", "ghost_fright_0.png"),
    ("PacManAssets-Ghosts.png", BASE_PM, 1, 8, "full", "ghost_fright_1.png"),
    ("PacManAssets-Ghosts.png", BASE_PM, 0, 9, "full", "ghost_blink_0.png"),
    ("PacManAssets-Ghosts.png", BASE_PM, 1, 9, "full", "ghost_blink_1.png"),
    ("PacManAssets-Ghosts.png", BASE_PM, 0, 10, "top", "eyes_0.png"),
    ("PacManAssets-Ghosts.png", BASE_PM, 1, 10, "top", "eyes_1.png"),
    ("PacManAssets-Ghosts.png", BASE_PM, 2, 10, "top", "eyes_2.png"),
    ("PacManAssets-Ghosts.png", BASE_PM, 3, 10, "top", "eyes_3.png"),
]


def _upscale(surf: pygame.Surface, factor: int) -> pygame.Surface:
    """Exact pixel replication, no blending."""
    w, h = surf.get_size()
    out = pygame.Surface((w * factor, h * factor), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            out.fill(
                surf.get_at((x, y)),
                (x * factor, y * factor, factor, factor),
            )
    return out


def main(tile: int) -> None:
    """Slice and upscale every frame into OUT/tileXX/."""
    pygame.init()
    pygame.display.set_mode((10, 10))
    dest = OUT / f"tile{tile}"
    dest.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, int, int, int, str, str]] = [
        (s, c, x, y, "full", n) for (s, c, x, y, n) in FRAMES
    ] + GHOST_EXTRA
    # Ghost bodies: 4 wave phases (one row) per color.
    for kind, row in GHOST_ROWS.items():
        for col in range(4):
            jobs.append(
                (
                    "PacManAssets-Ghosts.png",
                    BASE_PM,
                    col,
                    row,
                    "full",
                    f"ghost_{kind}_{col}.png",
                )
            )

    cache: dict[str, pygame.Surface] = {}
    for sheet, base, col, row, half, name in jobs:
        if sheet not in cache:
            cache[sheet] = pygame.image.load(
                str(ASSETS / sheet)
            ).convert_alpha()
        src = cache[sheet]
        if base == BASE_PM and tile % 2:
            raise ValueError(
                f"tile {tile} breaks 32px cells (need even)"
            )
        if base == BASE_DOT and tile % 16:
            raise ValueError(
                f"tile {tile} breaks 16px cells (need multiple of 16)"
            )
        factor = tile // base
        h = base // 2 if half == "top" else base
        cell = pygame.Surface((base, h), pygame.SRCALPHA)
        y0 = row * base
        for y in range(h):
            for x in range(base):
                cell.set_at((x, y), src.get_at((col * base + x, y0 + y)))
        pygame.image.save(_upscale(cell, factor), str(dest / name))
    print(f"wrote {len(jobs)} frames to {dest}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 64)
