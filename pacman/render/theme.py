"""Colours and, for now, screen text positions.

Sizes do NOT live here: every pixel size derives from one number in
render/layout.py, so nothing in this module can desync from it. The
screen text positions below are a stop-gap until the screens are
split out and centred (refactor step 4).

Themes: the module constants below are the live palette (midnight
by default). cycle_theme()/set_theme() swap the whole set at
runtime; the renderer reads colors through this module, so every
screen repaints on the next frame. Sprites keep their authored
colors (see Renderer party mode for the joke version of that).
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


def _palette(
    floor: Color,
    wall: Color,
    block: Color,
    player: Color,
    ghosts: tuple[Color, Color, Color, Color],
    frightened: Color,
    eaten: Color,
    pacgum: Color,
    super_pacgum: Color,
    hud_bg: Color,
    hud_text: Color,
    cheat: Color,
    screen_bg: Color,
    screen_title: Color,
    screen_text: Color,
    menu_bg: Color,
    menu_title: Color,
    menu_item: Color,
    menu_sel: Color,
    pause_bg: Color,
    pause_title: Color,
    pause_item: Color,
    victory_bg: Color,
    victory_title: Color,
    victory_text: Color,
    over_bg: Color,
    over_title: Color,
) -> dict[str, object]:
    """One full palette, keyed by module constant name."""
    kinds = (
        EntityKind.GHOST_1,
        EntityKind.GHOST_2,
        EntityKind.GHOST_3,
        EntityKind.GHOST_4,
    )
    return {
        "FLOOR_COLOR": floor,
        "WALL_COLOR": wall,
        "BLOCK_COLOR": block,
        "PLAYER_COLOR": player,
        "GHOST_COLORS": dict(zip(kinds, ghosts, strict=True)),
        "FRIGHTENED_COLOR": frightened,
        "EATEN_COLOR": eaten,
        "PACGUM_COLOR": pacgum,
        "SUPER_PACGUM_COLOR": super_pacgum,
        "HUD_BACKGROUND": hud_bg,
        "HUD_TEXT_COLOR": hud_text,
        "CHEAT_INDICATOR_COLOR": cheat,
        "SCREEN_BACKGROUND": screen_bg,
        "SCREEN_TITLE_COLOR": screen_title,
        "SCREEN_TEXT_COLOR": screen_text,
        "MENU_BACKGROUND": menu_bg,
        "MENU_TITLE_COLOR": menu_title,
        "MENU_ITEM_COLOR": menu_item,
        "MENU_SELECTED_COLOR": menu_sel,
        "PAUSE_BACKGROUND": pause_bg,
        "PAUSE_TITLE_COLOR": pause_title,
        "PAUSE_ITEM_COLOR": pause_item,
        "VICTORY_BACKGROUND": victory_bg,
        "VICTORY_TITLE_COLOR": victory_title,
        "VICTORY_TEXT_COLOR": victory_text,
        "GAME_OVER_BACKGROUND": over_bg,
        "GAME_OVER_TITLE_COLOR": over_title,
    }


MIDNIGHT = _palette(
    (10, 10, 30), (77, 166, 255), (75, 91, 171),
    (255, 220, 0),
    ((255, 0, 0), (255, 170, 220), (0, 220, 220), (255, 170, 0)),
    (30, 30, 220), (120, 120, 120),
    (255, 200, 150), (255, 240, 210),
    (0, 0, 0), (255, 255, 255), (255, 80, 80),
    (10, 10, 30), (255, 220, 0), (200, 200, 200),
    (5, 5, 20), (255, 220, 0), (200, 200, 200), (255, 255, 255),
    (5, 5, 20), (255, 220, 0), (200, 200, 200),
    (5, 20, 5), (255, 220, 0), (220, 220, 220),
    (20, 5, 5), (220, 40, 40),
)
"""Original dark palette (first in legacy order)."""

SUNSET = _palette(
    (30, 12, 20), (255, 140, 40), (150, 60, 70),
    (255, 230, 120),
    ((255, 60, 60), (255, 150, 180), (255, 200, 80), (200, 120, 255)),
    (120, 40, 200), (150, 130, 130),
    (255, 190, 130), (255, 240, 210),
    (20, 8, 12), (255, 235, 220), (255, 120, 80),
    (30, 12, 20), (255, 200, 60), (230, 200, 180),
    (25, 10, 15), (255, 200, 60), (230, 200, 180), (255, 255, 240),
    (25, 10, 15), (255, 200, 60), (230, 200, 180),
    (25, 25, 10), (255, 200, 60), (240, 220, 200),
    (30, 8, 8), (255, 90, 70),
)
"""Warm evening palette."""

TOXIC = _palette(
    (5, 15, 8), (60, 255, 120), (20, 90, 45),
    (220, 255, 120),
    ((120, 255, 120), (255, 255, 120), (120, 220, 255), (255, 180, 120)),
    (150, 40, 220), (130, 130, 130),
    (200, 255, 170), (240, 255, 220),
    (0, 0, 0), (220, 255, 230), (255, 100, 100),
    (5, 15, 8), (180, 255, 120), (200, 230, 200),
    (3, 12, 6), (180, 255, 120), (200, 230, 200), (240, 255, 240),
    (3, 12, 6), (180, 255, 120), (200, 230, 200),
    (8, 25, 8), (180, 255, 120), (220, 240, 220),
    (25, 8, 8), (255, 90, 70),
)
"""Green matrix palette."""

PINK = _palette(
    (30, 8, 18), (255, 130, 180), (150, 60, 90),
    (255, 220, 240),
    ((255, 80, 140), (255, 170, 200), (255, 210, 230), (200, 100, 160)),
    (160, 60, 200), (150, 130, 140),
    (255, 200, 220), (255, 240, 245),
    (15, 4, 10), (255, 225, 240), (255, 120, 170),
    (30, 8, 18), (255, 170, 210), (240, 200, 220),
    (22, 6, 14), (255, 170, 210), (240, 200, 220), (255, 245, 250),
    (22, 6, 14), (255, 170, 210), (240, 200, 220),
    (30, 12, 18), (255, 170, 210), (245, 215, 225),
    (32, 8, 12), (255, 110, 150),
)
"""Bubblegum palette."""

GRAY = _palette(
    (18, 18, 22), (160, 160, 170), (85, 85, 95),
    (245, 245, 245),
    ((220, 220, 220), (180, 180, 190), (140, 200, 220), (220, 190, 150)),
    (110, 110, 200), (130, 130, 130),
    (215, 215, 220), (245, 245, 250),
    (0, 0, 0), (235, 235, 240), (255, 100, 100),
    (18, 18, 22), (240, 240, 240), (200, 200, 205),
    (12, 12, 16), (240, 240, 240), (200, 200, 205), (255, 255, 255),
    (12, 12, 16), (240, 240, 240), (200, 200, 205),
    (16, 22, 16), (240, 240, 240), (215, 215, 220),
    (22, 8, 8), (255, 110, 110),
)
"""Monochrome palette."""

RED = _palette(
    (25, 5, 5), (255, 70, 60), (140, 30, 30),
    (255, 220, 150),
    ((255, 90, 70), (255, 150, 130), (255, 200, 120), (220, 80, 200)),
    (150, 50, 200), (150, 130, 130),
    (255, 180, 150), (255, 235, 225),
    (12, 2, 2), (255, 225, 215), (255, 130, 90),
    (25, 5, 5), (255, 190, 80), (240, 200, 190),
    (18, 4, 4), (255, 190, 80), (240, 200, 190), (255, 250, 245),
    (18, 4, 4), (255, 190, 80), (240, 200, 190),
    (28, 12, 8), (255, 190, 80), (245, 220, 205),
    (30, 5, 5), (255, 100, 90),
)
"""Hot red palette."""

YELLOW = _palette(
    (25, 22, 8), (255, 210, 80), (140, 120, 40),
    (255, 250, 200),
    ((255, 200, 60), (255, 170, 120), (255, 230, 150), (220, 150, 255)),
    (120, 80, 220), (150, 145, 130),
    (255, 225, 160), (255, 248, 225),
    (12, 10, 2), (255, 245, 220), (255, 150, 80),
    (25, 22, 8), (255, 220, 100), (240, 225, 195),
    (18, 16, 6), (255, 220, 100), (240, 225, 195), (255, 252, 245),
    (18, 16, 6), (255, 220, 100), (240, 225, 195),
    (26, 24, 10), (255, 220, 100), (245, 230, 200),
    (28, 10, 8), (255, 130, 90),
)
"""Golden palette."""

PURPLE = _palette(
    (15, 8, 30), (170, 100, 255), (80, 40, 140),
    (240, 220, 255),
    ((200, 120, 255), (255, 150, 220), (130, 180, 255), (255, 190, 120)),
    (90, 200, 220), (140, 130, 150),
    (220, 190, 255), (245, 235, 255),
    (8, 4, 15), (235, 220, 255), (255, 110, 150),
    (15, 8, 30), (210, 150, 255), (215, 195, 240),
    (10, 6, 22), (210, 150, 255), (215, 195, 240), (250, 245, 255),
    (10, 6, 22), (210, 150, 255), (215, 195, 240),
    (14, 20, 14), (210, 150, 255), (225, 210, 240),
    (28, 8, 16), (255, 110, 150),
)
"""Royal purple palette."""

COTTON = _palette(
    (200, 220, 255), (255, 150, 200), (150, 180, 240),
    (255, 180, 90),
    ((255, 120, 150), (200, 120, 220), (100, 170, 255), (255, 170, 90)),
    (150, 90, 220), (140, 140, 150),
    (230, 120, 170), (255, 255, 255),
    (170, 195, 245), (40, 40, 90), (200, 60, 120),
    (200, 220, 255), (220, 60, 130), (60, 60, 120),
    (185, 205, 250), (220, 60, 130), (60, 60, 120), (40, 40, 90),
    (185, 205, 250), (220, 60, 130), (60, 60, 120),
    (200, 235, 220), (220, 60, 130), (60, 90, 80),
    (250, 210, 225), (200, 50, 100),
)
"""Cotton candy: light blue plus light pink."""

VICE = _palette(
    (20, 5, 35), (80, 220, 255), (90, 40, 140),
    (255, 240, 160),
    ((120, 230, 255), (255, 130, 200), (150, 160, 255), (255, 190, 110)),
    (160, 80, 255), (140, 130, 150),
    (150, 225, 255), (255, 220, 240),
    (10, 2, 18), (220, 240, 255), (255, 110, 160),
    (20, 5, 35), (255, 130, 190), (200, 190, 240),
    (14, 4, 26), (255, 130, 190), (200, 190, 240), (245, 240, 255),
    (14, 4, 26), (255, 130, 190), (200, 190, 240),
    (10, 24, 20), (255, 130, 190), (210, 230, 225),
    (30, 6, 14), (255, 100, 140),
)
"""Neon vice: dark purple, cyan walls, pink titles."""

THEMES: dict[str, dict[str, object]] = {
    "midnight": MIDNIGHT,
    "sunset": SUNSET,
    "toxic": TOXIC,
    "pink": PINK,
    "gray": GRAY,
    "red": RED,
    "yellow": YELLOW,
    "purple": PURPLE,
    "cotton": COTTON,
    "vice": VICE,
}
"""All palettes, in cycle order."""

THEME_ORDER: tuple[str, ...] = (
    "cotton",
    "midnight",
    "sunset",
    "toxic",
    "pink",
    "gray",
    "red",
    "yellow",
    "purple",
    "vice",
)

_current: str = "cotton"

# The literals above spell midnight; the live palette starts on
# cotton (project default). Keep this single update point instead
# of duplicating the cotton values into every constant.
globals().update(COTTON)


def current_theme() -> str:
    """Name of the active palette."""
    return _current


def set_theme(name: str) -> bool:
    """Swap the whole live palette; unknown names are ignored.

    Args:
        name: One of THEME_ORDER.

    Returns:
        True when the palette changed.
    """
    global _current
    palette = THEMES.get(name)
    if palette is None or name == _current:
        return False
    globals().update(palette)
    _current = name
    return True


def cycle_theme() -> str:
    """Advance to the next palette, wrapping around."""
    nxt = THEME_ORDER[(THEME_ORDER.index(_current) + 1) % len(THEME_ORDER)]
    set_theme(nxt)
    return nxt
