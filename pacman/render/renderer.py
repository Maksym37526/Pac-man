"""Renderer: implements the Renderer contract from module_contracts.md.

Consumes ``Maze`` and ``GameState`` (currently the render/fakes.py
stand-in). Never mutates either. Only talks to pygame through
``GraphicsFacade``.
"""

from __future__ import annotations

from pacman.maze.model import Cell, Direction, Maze
from pacman.render.facade import Color, GraphicsFacade
from pacman.render.fakes import Entity, EntityKind, EntityMode, RenderGameState
from pacman.ui.cheats import CHEAT_LABELS
from pacman.data.config import Config
from pacman.ui.state_machine import AppState, HighscoresPayload, MAIN_MENU_LABELS, MainMenuPayload, NameEntryPayload, VictoryPayload, _MAIN_MENU_ORDER

SCREEN_BACKGROUND: Color = (10, 10, 30)
SCREEN_TITLE_COLOR: Color = (255, 220, 0)
SCREEN_TEXT_COLOR: Color = (200, 200, 200)

TILE_SIZE = 100
"""Pixels per maze cell. Fixed at asset-authoring time (decision D2)."""

CHEAT_INDICATOR_COLOR: Color = (255, 80, 80)

WALL_THICKNESS = 2
ENTITY_MARGIN = 40
"""Pixels of tile left uncovered on each side by an entity's square."""

HUD_HEIGHT = 24
"""Pixels reserved for the HUD strip at the bottom of the window."""

FLOOR_COLOR: Color = (10, 10, 30)
WALL_COLOR: Color = (40, 80, 220)
BLOCK_COLOR: Color = (0, 0, 0)
PLAYER_COLOR: Color = (255, 220, 0)
GHOST_COLORS: dict[EntityKind, Color] = {
    EntityKind.GHOST_1: (255, 0, 0),
    EntityKind.GHOST_2: (255, 170, 220),
    EntityKind.GHOST_3: (0, 220, 220),
    EntityKind.GHOST_4: (255, 170, 0),
}
FRIGHTENED_COLOR: Color = (30, 30, 220)
EATEN_COLOR: Color = (120, 120, 120)
HUD_BACKGROUND: Color = (0, 0, 0)
HUD_TEXT_COLOR: Color = (255, 255, 255)

VICTORY_TITLE_COLOR: Color = (255, 220, 0)
VICTORY_TEXT_COLOR: Color = (220, 220, 220)
VICTORY_BACKGROUND: Color = (5, 20, 5)
VICTORY_TITLE_Y = 60
VICTORY_SCORE_Y = 110
VICTORY_HINT_Y = 150

MENU_ITEM_LABELS = ["Start Game", "View Highscores", "Instructions", "Exit"]
MENU_TITLE_COLOR: Color = (255, 220, 0)
MENU_ITEM_COLOR: Color = (200, 200, 200)
MENU_SELECTED_COLOR: Color = (255, 255, 255)
MENU_BACKGROUND: Color = (5, 5, 20)

MENU_TITLE_Y = 40
MENU_ITEM_START_Y = 140
MENU_ITEM_SPACING = 50

PACGUM_COLOR: Color = (255, 200, 150)
PACGUM_RADIUS = 1
SUPER_PACGUM_COLOR: Color = (255, 200, 150)
SUPER_PACGUM_RADIUS = 4

PACGUM_COLOR: Color = (255, 200, 150)
PACGUM_RADIUS = 1
SUPER_PACGUM_COLOR: Color = (255, 200, 150)
SUPER_PACGUM_RADIUS = 4

PAUSE_TITLE_COLOR: Color = (255, 220, 0)
PAUSE_ITEM_COLOR: Color = (200, 200, 200)
PAUSE_BACKGROUND: Color = (5, 5, 20)
PAUSE_TITLE_Y = 60
PAUSE_ITEM_START_Y = 110
PAUSE_ITEM_SPACING = 24


def maze_window_size(maze_width_cells: int, maze_height_cells: int) -> tuple[int, int]:
    """Compute the full window size for a maze of the given cell size.

    Includes the HUD strip reserved below the maze area. Called once
    per level with the largest level's dimensions to size the window
    at startup (decision D3); smaller levels reuse this fixed size.

    Args:
        maze_width_cells: Maze width in cells.
        maze_height_cells: Maze height in cells.

    Returns:
        (window_width, window_height) in pixels.
    """
    return maze_width_cells * TILE_SIZE, maze_height_cells * TILE_SIZE + HUD_HEIGHT

def window_size_for_config(config: Config) -> tuple[int, int]:
    """Compute the fixed window size for a run, per D3.

    The window is sized once from the largest level's dimensions in
    the config — never per-level — so smaller levels are centred
    (see Renderer.prepare_level) rather than resizing the window.

    Args:
        config: The validated, immutable run config.

    Returns:
        (window_width, window_height) in pixels, including the HUD strip.
    """
    max_width = max(level.width for level in config.levels)
    max_height = max(level.height for level in config.levels)
    return maze_window_size(max_width, max_height)

class Renderer:
    """Draws maze and game state via a GraphicsFacade."""

    def __init__(self, facade: GraphicsFacade, window_width: int, window_height: int) -> None:
        """Store the facade and the window's fixed size.

        The window is sized once at startup from the largest level in
        the config (decision D3), via ``maze_window_size``. Smaller
        mazes are centred against this size, not against their own.
        The HUD strip is not part of the centred maze area — it always
        occupies the bottom ``HUD_HEIGHT`` pixels of the window.

        Args:
            facade: Graphics facade to draw through.
            window_width: Window width in pixels, fixed for the game's lifetime.
            window_height: Window height in pixels, fixed for the game's lifetime.
        """
        self._facade = facade
        self._window_width = window_width
        self._window_height = window_height
        self._background: object | None = None
        self._offset_x = 0
        self._offset_y = 0

    def cell_to_screen(self, cell: Cell, progress_x: float = 0.0, progress_y: float = 0.0) -> tuple[int, int]:
        """Convert a maze cell to top-left pixel coordinates in the window.

        Args:
            cell: The cell whose top-left corner to locate.
            progress_x: Fractional offset within the tile, X axis (0.0-1.0).
                Used for interpolated entity positions; 0.0 for static tiles.
            progress_y: Fractional offset within the tile, Y axis.

        Returns:
            (px, py) in window pixels, including the centring offset.
            Never overlaps the HUD strip, since the maze area excludes it.
        """
        px = self._offset_x + int((cell.col + progress_x) * TILE_SIZE)
        py = self._offset_y + int((cell.row + progress_y) * TILE_SIZE)
        return px, py

    def prepare_level(self, maze: Maze) -> None:
        """Render the static maze once into a cached background buffer.

        Walls are written pixel by pixel (no rect primitive available
        under the MLX-equivalence restriction), so this is deliberately
        called once per level rather than every frame. The maze area
        is centred within the window, above the HUD strip.
        """
        maze_area_height = self._window_height - HUD_HEIGHT
        level_width = maze.width * TILE_SIZE
        level_height = maze.height * TILE_SIZE
        self._offset_x = (self._window_width - level_width) // 2
        self._offset_y = (maze_area_height - level_height) // 2

        buffer = self._facade.new_buffer(self._window_width, self._window_height)
        self._facade.clear(buffer, FLOOR_COLOR)

        for cell in (Cell(c, r) for r in range(maze.height) for c in range(maze.width)):
            if cell in maze.blocks:
                self._fill_tile(buffer, cell, BLOCK_COLOR)
                continue
            for direction in Direction:
                if maze.is_wall_between(cell, direction):
                    self._draw_wall_edge(buffer, cell, direction)

        self._background = buffer

    def draw_game(self, state: RenderGameState) -> None:
        """Blit the cached background, then dynamic entities and the HUD.

        Args:
            state: Current game state. Never mutated.
        """
        if self._background is None:
            raise RuntimeError("draw_game called before prepare_level")

        frame = self._facade.new_buffer(self._window_width, self._window_height)
        self._facade.blit(self._background, (0, 0), dest=frame)

        for cell in state.core.pacgums:
            self._draw_dot(frame, cell, PACGUM_RADIUS, PACGUM_COLOR)
        for cell in state.core.super_pacgums:
            self._draw_dot(frame, cell, SUPER_PACGUM_RADIUS, SUPER_PACGUM_COLOR)

        self._draw_entity(frame, state.core.player, PLAYER_COLOR)
        for ghost in state.ghosts:
            self._draw_entity(frame, ghost, self._ghost_color(ghost))

        self._draw_hud(frame, state)

        self._facade.blit(frame, (0, 0))

    def _draw_dot(self, buffer: object, cell: Cell, radius: int, color: Color) -> None:
        """Draw a small filled square centred in a tile, pixel by pixel."""
        origin_x, origin_y = self.cell_to_screen(cell)
        center_x, center_y = origin_x + TILE_SIZE // 2, origin_y + TILE_SIZE // 2
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                self._facade.put_pixel(buffer, center_x + dx, center_y + dy, color)

    def _draw_hud(self, buffer: object, state: RenderGameState) -> None:
        """Draw the HUD strip: score, lives, level, remaining time, active cheats."""
        hud_top = self._window_height - HUD_HEIGHT
        for y in range(hud_top, self._window_height):
            for x in range(self._window_width):
                self._facade.put_pixel(buffer, x, y, HUD_BACKGROUND)
        text = (
            f"Score: {state.core.score}  Lives: {state.lives}  "
            f"Level: {state.level_index + 1}/{state.level_count}  "
            f"Time: {int(state.time_remaining)}"
        )
        self._facade.draw_text(buffer, text, (4, hud_top + 4), HUD_TEXT_COLOR)

        if state.cheats.active:
            labels = ", ".join(CHEAT_LABELS[kind] for kind in state.cheats.active)
            self._facade.draw_text(buffer, f"[{labels}]", (4, hud_top + HUD_HEIGHT // 2 + 2), CHEAT_INDICATOR_COLOR)

    def _ghost_color(self, ghost: Entity) -> Color:
        """Pick a ghost's colour based on its mode and identity."""
        if ghost.mode is EntityMode.EATEN:
            return EATEN_COLOR
        if ghost.mode is EntityMode.FRIGHTENED:
            return FRIGHTENED_COLOR
        return GHOST_COLORS[ghost.kind]

    def _draw_entity(self, buffer: object, entity: Entity, color: Color) -> None:
        """Draw one entity as a filled square, interpolated between cells."""
        delta_col = entity.cell.col - entity.prev_cell.col
        delta_row = entity.cell.row - entity.prev_cell.row
        progress_x = delta_col * entity.progress
        progress_y = delta_row * entity.progress
        origin_x, origin_y = self.cell_to_screen(entity.prev_cell, progress_x, progress_y)
        for dy in range(ENTITY_MARGIN, TILE_SIZE - ENTITY_MARGIN):
            for dx in range(ENTITY_MARGIN, TILE_SIZE - ENTITY_MARGIN):
                self._facade.put_pixel(buffer, origin_x + dx, origin_y + dy, color)

    def _fill_tile(self, buffer: object, cell: Cell, color: Color) -> None:
        """Fill one tile solid, pixel by pixel."""
        origin_x, origin_y = self.cell_to_screen(cell)
        for dy in range(TILE_SIZE):
            for dx in range(TILE_SIZE):
                self._facade.put_pixel(buffer, origin_x + dx, origin_y + dy, color)

    def _draw_wall_edge(self, buffer: object, cell: Cell, direction: Direction) -> None:
        """Draw the wall segment on one edge of one tile."""
        origin_x, origin_y = self.cell_to_screen(cell)
        if direction is Direction.UP:
            for dx in range(TILE_SIZE):
                for dy in range(WALL_THICKNESS):
                    self._facade.put_pixel(buffer, origin_x + dx, origin_y + dy, WALL_COLOR)
        elif direction is Direction.DOWN:
            for dx in range(TILE_SIZE):
                for dy in range(WALL_THICKNESS):
                    self._facade.put_pixel(
                        buffer, origin_x + dx, origin_y + TILE_SIZE - 1 - dy, WALL_COLOR
                    )
        elif direction is Direction.LEFT:
            for dy in range(TILE_SIZE):
                for dx in range(WALL_THICKNESS):
                    self._facade.put_pixel(buffer, origin_x + dx, origin_y + dy, WALL_COLOR)
        elif direction is Direction.RIGHT:
            for dy in range(TILE_SIZE):
                for dx in range(WALL_THICKNESS):
                    self._facade.put_pixel(
                        buffer, origin_x + TILE_SIZE - 1 - dx, origin_y + dy, WALL_COLOR
                    )

    def present(self) -> None:
        """Push the composited frame to the window and flip."""
        self._facade.present()
    
    def draw_screen(self, app_state: AppState, payload: object) -> None:
        frame = self._facade.new_buffer(self._window_width, self._window_height)

        if app_state is AppState.MAIN_MENU:
            assert isinstance(payload, MainMenuPayload)
            self._facade.clear(frame, MENU_BACKGROUND)
            self._draw_main_menu(frame, payload)
        elif app_state is AppState.PAUSED:
            self._facade.clear(frame, PAUSE_BACKGROUND)
            self._draw_paused(frame)
        elif app_state is AppState.VICTORY:
            assert isinstance(payload, VictoryPayload)
            self._facade.clear(frame, VICTORY_BACKGROUND)
            self._draw_victory(frame, payload)
        elif app_state is AppState.NAME_ENTRY:
            assert isinstance(payload, NameEntryPayload)
            self._facade.clear(frame, SCREEN_BACKGROUND)
            self._draw_name_entry(frame, payload)
        elif app_state is AppState.HIGHSCORES:
            assert isinstance(payload, HighscoresPayload)
            self._facade.clear(frame, SCREEN_BACKGROUND)
            self._draw_highscores(frame, payload)
        elif app_state is AppState.INSTRUCTIONS:
            self._facade.clear(frame, SCREEN_BACKGROUND)
            self._draw_instructions(frame)
        else:
            raise NotImplementedError(f"draw_screen not yet implemented for {app_state}")

        self._facade.blit(frame, (0, 0))

    def _draw_name_entry(self, buffer: object, payload: NameEntryPayload) -> None:
        """Name entry: title, typed-so-far name with a cursor, hint."""
        self._facade.draw_text(buffer, "Enter your name:", (20, 40), SCREEN_TITLE_COLOR)
        self._facade.draw_text(buffer, payload.name + "_", (20, 90), SCREEN_TEXT_COLOR)
        self._facade.draw_text(buffer, "Enter to confirm  Esc to skip", (20, 140), SCREEN_TEXT_COLOR)

    def _draw_highscores(self, buffer: object, payload: HighscoresPayload) -> None:
        """Top-10 list: rank, name, score. Empty list shows a placeholder line."""
        self._facade.draw_text(buffer, "High Scores", (20, 30), SCREEN_TITLE_COLOR)
        if not payload.entries:
            self._facade.draw_text(buffer, "(no scores yet)", (20, 70), SCREEN_TEXT_COLOR)
        for index, (name, score) in enumerate(payload.entries[:10]):
            line = f"{index + 1}. {name} - {score}"
            self._facade.draw_text(buffer, line, (20, 70 + index * 24), SCREEN_TEXT_COLOR)
        self._facade.draw_text(buffer, "Esc to return", (20, self._window_height - 30), SCREEN_TEXT_COLOR)

    def _draw_instructions(self, buffer: object) -> None:
        """Static controls reference (VI.8)."""
        lines = [
            "Controls:",
            "Arrows / WASD - Move",
            "P - Pause",
            "Enter / Space - Confirm",
            "Esc - Back",
            "F1-F5 - Cheats (invincibility, skip, freeze, extra life, speed)",
            "",
            "Esc to return",
        ]
        for index, line in enumerate(lines):
            color = SCREEN_TITLE_COLOR if index == 0 else SCREEN_TEXT_COLOR
            self._facade.draw_text(buffer, line, (20, 30 + index * 24), color)

    def _draw_victory(self, buffer: object, payload: VictoryPayload) -> None:
        """Draw the victory screen: title, final score, continue hint."""
        self._facade.draw_text(buffer, "You Win!", (20, VICTORY_TITLE_Y), VICTORY_TITLE_COLOR)
        self._facade.draw_text(
            buffer, f"Final Score: {payload.final_score}", (20, VICTORY_SCORE_Y), VICTORY_TEXT_COLOR
        )
        self._facade.draw_text(
            buffer, "Enter/Esc — Main Menu", (20, VICTORY_HINT_Y), VICTORY_TEXT_COLOR
        )
    def _draw_paused(self, buffer: object) -> None:
        """Draw the pause menu: title and the two options from VI.8."""
        self._facade.draw_text(buffer, "Paused", (20, PAUSE_TITLE_Y), PAUSE_TITLE_COLOR)
        self._facade.draw_text(
            buffer, "P — Resume", (20, PAUSE_ITEM_START_Y), PAUSE_ITEM_COLOR
        )
        self._facade.draw_text(
            buffer, "Esc — Main Menu", (20, PAUSE_ITEM_START_Y + PAUSE_ITEM_SPACING), PAUSE_ITEM_COLOR
        )

    def _draw_main_menu(self, buffer: object, payload: MainMenuPayload) -> None:
        """Draw the title and the four menu entries, highlighting the selected one."""
        self._facade.draw_text(buffer, "Pac-Man", (20, MENU_TITLE_Y), MENU_TITLE_COLOR)
        for index, item in enumerate(_MAIN_MENU_ORDER):
            y = MENU_ITEM_START_Y + index * MENU_ITEM_SPACING
            color = MENU_SELECTED_COLOR if index == payload.selected_index else MENU_ITEM_COLOR
            prefix = "> " if index == payload.selected_index else "  "
            self._facade.draw_text(buffer, prefix + MAIN_MENU_LABELS[item], (20, y), color)

    def _fill_solid(self, buffer: object, color: Color) -> None:
        """Fill a buffer solid, pixel by pixel — same reasoning as the HUD strip."""
        for y in range(self._window_height):
            for x in range(self._window_width):
                self._facade.put_pixel(buffer, x, y, color)