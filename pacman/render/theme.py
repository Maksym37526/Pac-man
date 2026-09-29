"""Colours and, for now, screen text positions.

Sizes do NOT live here: every pixel size derives from one number in
render/layout.py, so nothing in this module can desync from it. The
screen text positions below are a stop-gap until the screens are
split out and centred (refactor step 4).
"""

from pacman.core.entity import EntityKind
from pacman.render.facade import Color

# Maze (palette sampled from PacManAssets_Map_TileSet.png)
FLOOR_COLOR: Color = (10, 10, 30)
WALL_COLOR: Color = (77, 166, 255)
BLOCK_COLOR: Color = (75, 91, 171)

# Entities and pickups
PLAYER_COLOR: Color = (255, 220, 0)
GHOST_COLORS: dict[EntityKind, Color] = {
    EntityKind.GHOST_1: (255, 0, 0),
    EntityKind.GHOST_2: (255, 170, 220),
    EntityKind.GHOST_3: (0, 220, 220),
    EntityKind.GHOST_4: (255, 170, 0),
}
FRIGHTENED_COLOR: Color = (30, 30, 220)
EATEN_COLOR: Color = (120, 120, 120)
PACGUM_COLOR: Color = (255, 200, 150)
SUPER_PACGUM_COLOR: Color = (255, 240, 210)
"""Fallback-only super-pacgum tint, lighter than PACGUM_COLOR."""

# HUD
HUD_BACKGROUND: Color = (0, 0, 0)
HUD_TEXT_COLOR: Color = (255, 255, 255)
CHEAT_INDICATOR_COLOR: Color = (255, 80, 80)

# Generic screens (highscores, instructions, name entry)
SCREEN_BACKGROUND: Color = (10, 10, 30)
SCREEN_TITLE_COLOR: Color = (255, 220, 0)
SCREEN_TEXT_COLOR: Color = (200, 200, 200)

# Main menu
MENU_BACKGROUND: Color = (5, 5, 20)
MENU_TITLE_COLOR: Color = (255, 220, 0)
MENU_ITEM_COLOR: Color = (200, 200, 200)
MENU_SELECTED_COLOR: Color = (255, 255, 255)
MENU_TITLE_Y = 40
MENU_ITEM_START_Y = 140
MENU_ITEM_SPACING = 50

# Pause
PAUSE_BACKGROUND: Color = (5, 5, 20)
PAUSE_TITLE_COLOR: Color = (255, 220, 0)
PAUSE_ITEM_COLOR: Color = (200, 200, 200)
PAUSE_TITLE_Y = 60
PAUSE_ITEM_START_Y = 110
PAUSE_ITEM_SPACING = 24

# Victory / game over
VICTORY_BACKGROUND: Color = (5, 20, 5)
VICTORY_TITLE_COLOR: Color = (255, 220, 0)
VICTORY_TEXT_COLOR: Color = (220, 220, 220)
VICTORY_TITLE_Y = 60
VICTORY_SCORE_Y = 110
VICTORY_HINT_Y = 150
GAME_OVER_BACKGROUND: Color = (20, 5, 5)
GAME_OVER_TITLE_COLOR: Color = (220, 40, 40)
