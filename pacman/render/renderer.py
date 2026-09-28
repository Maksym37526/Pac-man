"""Renderer: implements the Renderer contract from module_contracts.md.

Reads ``Maze`` and ``RenderGameState``, never mutates either, and
talks to pygame only through ``GraphicsFacade``. Every size comes
from the ``Layout`` it is built with; colours come from ``theme``.

Speed: pixel-by-pixel work happens once. Solid rectangles are built
once per (size, colour) and afterwards drawn with a single blit, the
maze and the HUD backdrop live in a cached background, and one frame
buffer is reused for every frame.
"""

from __future__ import annotations

from pacman.core.entity import Entity, EntityMode
from pacman.maze.model import Cell, Direction, Maze
from pacman.render.facade import Buffer, Color, GraphicsFacade
from pacman.render.layout import Layout
from pacman.render.theme import (
    BLOCK_COLOR,
    CHEAT_INDICATOR_COLOR,
    EATEN_COLOR,
    FLOOR_COLOR,
    FRIGHTENED_COLOR,
    GAME_OVER_BACKGROUND,
    GAME_OVER_TITLE_COLOR,
    GHOST_COLORS,
    HUD_BACKGROUND,
    HUD_TEXT_COLOR,
    MENU_BACKGROUND,
    MENU_ITEM_COLOR,
    MENU_ITEM_SPACING,
    MENU_ITEM_START_Y,
    MENU_SELECTED_COLOR,
    MENU_TITLE_COLOR,
    MENU_TITLE_Y,
    PACGUM_COLOR,
    PAUSE_BACKGROUND,
    PAUSE_ITEM_COLOR,
    PAUSE_ITEM_SPACING,
    PAUSE_ITEM_START_Y,
    PAUSE_TITLE_COLOR,
    PAUSE_TITLE_Y,
    PLAYER_COLOR,
    SCREEN_BACKGROUND,
    SCREEN_TEXT_COLOR,
    SCREEN_TITLE_COLOR,
    SUPER_PACGUM_COLOR,
    VICTORY_BACKGROUND,
    VICTORY_HINT_Y,
    VICTORY_SCORE_Y,
    VICTORY_TEXT_COLOR,
    VICTORY_TITLE_COLOR,
    VICTORY_TITLE_Y,
    WALL_COLOR,
)
from pacman.render.view_state import RenderGameState
from pacman.ui.cheats import CHEAT_LABELS
from pacman.ui.state_machine import (
    MAIN_MENU_LABELS,
    AppState,
    GameOverPayload,
    HighscoresPayload,
    MainMenuPayload,
    NameEntryPayload,
    VictoryPayload,
    _MAIN_MENU_ORDER,
)


class Renderer:
    """Draws the maze, the game and every screen via a GraphicsFacade."""

    def __init__(self, facade: GraphicsFacade, layout: Layout) -> None:
        """Store the facade and the run's fixed layout.

        Args:
            facade: Graphics facade to draw through.
            layout: Pixel sizes for the whole run (decision D3).
        """
        self._facade = facade
        self._layout = layout
        self._background: Buffer | None = None
        self._origin = (0, 0)
        self._frame = facade.new_buffer(
            layout.window_width, layout.window_height
        )
        self._solids: dict[tuple[int, int, Color], Buffer] = {}

    def cell_to_screen(
        self, cell: Cell, progress_x: float = 0.0, progress_y: float = 0.0
    ) -> tuple[int, int]:
        """Top-left pixel of a cell, optionally shifted by a tile fraction."""
        return self._layout.cell_origin(
            self._origin, cell.col + progress_x, cell.row + progress_y
        )

    def prepare_level(self, maze: Maze) -> None:
        """Render the static maze and HUD backdrop once into a cache.

        Args:
            maze: The level's maze.
        """
        layout = self._layout
        self._origin = layout.maze_origin(maze.width, maze.height)
        buffer = self._facade.new_buffer(
            layout.window_width, layout.window_height
        )
        self._facade.clear(buffer, FLOOR_COLOR)
        for row in range(maze.height):
            for col in range(maze.width):
                cell = Cell(col, row)
                if cell in maze.blocks:
                    self._fill_tile(buffer, cell, BLOCK_COLOR)
                    continue
                for direction in Direction:
                    if maze.is_wall_between(cell, direction):
                        self._draw_wall_edge(buffer, cell, direction)
        self._fill_rect(
            buffer,
            0,
            layout.hud_top,
            layout.window_width,
            layout.hud_height,
            HUD_BACKGROUND,
        )
        self._background = buffer

    def draw_game(self, state: RenderGameState) -> None:
        """Draw the cached maze, then pickups, entities and the HUD text.

        Args:
            state: Current game state. Never mutated.
        """
        if self._background is None:
            raise RuntimeError("draw_game called before prepare_level")
        layout = self._layout
        frame = self._frame
        self._facade.blit(self._background, (0, 0), dest=frame)

        for cell in state.core.pacgums:
            self._draw_dot(frame, cell, layout.pacgum_radius, PACGUM_COLOR)
        for cell in state.core.super_pacgums:
            self._draw_dot(
                frame, cell, layout.super_radius, SUPER_PACGUM_COLOR
            )
        self._draw_entity(frame, state.core.player, PLAYER_COLOR)
        for ghost in state.core.ghosts:
            self._draw_entity(frame, ghost, self._ghost_color(ghost))
        self._draw_hud(frame, state)

        self._facade.blit(frame, (0, 0))

    def present(self) -> None:
        """Push the composited frame to the window."""
        self._facade.present()

    # ---- drawing helpers ------------------------------------------

    def _solid(self, width: int, height: int, color: Color) -> Buffer:
        """A solid-colour buffer, built pixel by pixel once and cached.

        Filling a rectangle pixel by pixel costs width*height Python
        calls every time; blitting a cached buffer costs one. Built
        with put_pixel (not fill) to stay inside the approved primitives.
        """
        key = (width, height, color)
        solid = self._solids.get(key)
        if solid is None:
            solid = self._facade.new_buffer(width, height)
            for y in range(height):
                for x in range(width):
                    self._facade.put_pixel(solid, x, y, color)
            self._solids[key] = solid
        return solid

    def _fill_rect(
        self,
        buffer: Buffer,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Color,
    ) -> None:
        """Draw a solid rectangle by blitting a cached solid buffer."""
        self._facade.blit(
            self._solid(width, height, color), (x, y), dest=buffer
        )

    def _fill_tile(self, buffer: Buffer, cell: Cell, color: Color) -> None:
        """Fill one whole tile."""
        x, y = self.cell_to_screen(cell)
        tile = self._layout.tile
        self._fill_rect(buffer, x, y, tile, tile, color)

    def _draw_wall_edge(
        self, buffer: Buffer, cell: Cell, direction: Direction
    ) -> None:
        """Draw the wall segment on one edge of one tile."""
        x, y = self.cell_to_screen(cell)
        tile = self._layout.tile
        wall = self._layout.wall
        if direction is Direction.UP:
            self._fill_rect(buffer, x, y, tile, wall, WALL_COLOR)
        elif direction is Direction.DOWN:
            self._fill_rect(buffer, x, y + tile - wall, tile, wall, WALL_COLOR)
        elif direction is Direction.LEFT:
            self._fill_rect(buffer, x, y, wall, tile, WALL_COLOR)
        elif direction is Direction.RIGHT:
            self._fill_rect(buffer, x + tile - wall, y, wall, tile, WALL_COLOR)

    def _draw_dot(
        self, buffer: Buffer, cell: Cell, radius: int, color: Color
    ) -> None:
        """Draw a pickup as a small square centred in its tile."""
        x, y = self.cell_to_screen(cell)
        half = self._layout.tile // 2
        size = radius * 2 + 1
        self._fill_rect(
            buffer, x + half - radius, y + half - radius, size, size, color
        )

    def _draw_entity(
        self, buffer: Buffer, entity: Entity, color: Color
    ) -> None:
        """Draw an entity as a square, interpolated between its cells."""
        col = entity.prev_cell.col + (
            entity.cell.col - entity.prev_cell.col
        ) * entity.progress
        row = entity.prev_cell.row + (
            entity.cell.row - entity.prev_cell.row
        ) * entity.progress
        x, y = self._layout.cell_origin(self._origin, col, row)
        margin = self._layout.entity_margin
        size = self._layout.tile - 2 * margin
        self._fill_rect(buffer, x + margin, y + margin, size, size, color)

    def _ghost_color(self, ghost: Entity) -> Color:
        """Pick a ghost's colour from its mode and identity."""
        if ghost.mode is EntityMode.EATEN:
            return EATEN_COLOR
        if ghost.mode is EntityMode.FRIGHTENED:
            return FRIGHTENED_COLOR
        return GHOST_COLORS[ghost.kind]

    def _draw_hud(self, buffer: Buffer, state: RenderGameState) -> None:
        """Draw the HUD text; the strip is part of the cached backdrop."""
        layout = self._layout
        text = (
            f"Score: {state.core.score}  Lives: {state.core.lives}  "
            f"Level: {state.level_index + 1}/{state.level_count}  "
            f"Time: {int(state.time_remaining)}"
        )
        self._facade.draw_text(
            buffer, text, (4, layout.hud_top + 2), HUD_TEXT_COLOR
        )
        if state.cheats.active:
            labels = ", ".join(CHEAT_LABELS[k] for k in state.cheats.active)
            self._facade.draw_text(
                buffer,
                f"[{labels}]",
                (4, layout.hud_top + layout.font_size + 2),
                CHEAT_INDICATOR_COLOR,
            )

    # ---- screens (split out in refactor step 4) -------------------

    def draw_screen(self, app_state: AppState, payload: object) -> None:
        """Draw a non-gameplay screen.

        Args:
            app_state: Which screen to draw.
            payload: Screen-specific data.
        """
        frame = self._frame
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
        elif app_state is AppState.GAME_OVER:
            assert isinstance(payload, GameOverPayload)
            self._facade.clear(frame, GAME_OVER_BACKGROUND)
            self._draw_game_over(frame, payload)
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
            raise NotImplementedError(
                f"draw_screen not yet implemented for {app_state}"
            )
        self._facade.blit(frame, (0, 0))

    def _draw_main_menu(
        self, buffer: Buffer, payload: MainMenuPayload
    ) -> None:
        """Title and the four menu entries, the selected one highlighted."""
        self._facade.draw_text(
            buffer, "Pac-Man", (20, MENU_TITLE_Y), MENU_TITLE_COLOR
        )
        for index, item in enumerate(_MAIN_MENU_ORDER):
            y = MENU_ITEM_START_Y + index * MENU_ITEM_SPACING
            selected = index == payload.selected_index
            color = MENU_SELECTED_COLOR if selected else MENU_ITEM_COLOR
            prefix = "> " if selected else "  "
            self._facade.draw_text(
                buffer, prefix + MAIN_MENU_LABELS[item], (20, y), color
            )

    def _draw_paused(self, buffer: Buffer) -> None:
        """Pause menu: title and the two options from VI.8."""
        self._facade.draw_text(
            buffer, "Paused", (20, PAUSE_TITLE_Y), PAUSE_TITLE_COLOR
        )
        self._facade.draw_text(
            buffer, "P - Resume", (20, PAUSE_ITEM_START_Y), PAUSE_ITEM_COLOR
        )
        self._facade.draw_text(
            buffer,
            "Esc - Main Menu",
            (20, PAUSE_ITEM_START_Y + PAUSE_ITEM_SPACING),
            PAUSE_ITEM_COLOR,
        )

    def _draw_victory(self, buffer: Buffer, payload: VictoryPayload) -> None:
        """Victory screen: title, final score, continue hint."""
        self._facade.draw_text(
            buffer, "You Win!", (20, VICTORY_TITLE_Y), VICTORY_TITLE_COLOR
        )
        self._facade.draw_text(
            buffer,
            f"Final Score: {payload.final_score}",
            (20, VICTORY_SCORE_Y),
            VICTORY_TEXT_COLOR,
        )
        self._facade.draw_text(
            buffer,
            "Enter/Esc - Continue",
            (20, VICTORY_HINT_Y),
            VICTORY_TEXT_COLOR,
        )

    def _draw_game_over(
        self, buffer: Buffer, payload: GameOverPayload
    ) -> None:
        """Game-over screen: title, final score, continue hint."""
        self._facade.draw_text(
            buffer, "Game Over", (20, VICTORY_TITLE_Y), GAME_OVER_TITLE_COLOR
        )
        self._facade.draw_text(
            buffer,
            f"Final Score: {payload.final_score}",
            (20, VICTORY_SCORE_Y),
            VICTORY_TEXT_COLOR,
        )
        self._facade.draw_text(
            buffer,
            "Enter/Esc - Continue",
            (20, VICTORY_HINT_Y),
            VICTORY_TEXT_COLOR,
        )

    def _draw_name_entry(
        self, buffer: Buffer, payload: NameEntryPayload
    ) -> None:
        """Name entry: title, the name typed so far with a cursor, hint."""
        self._facade.draw_text(
            buffer, "Enter your name:", (20, 40), SCREEN_TITLE_COLOR
        )
        self._facade.draw_text(
            buffer, payload.name + "_", (20, 90), SCREEN_TEXT_COLOR
        )
        self._facade.draw_text(
            buffer,
            "Enter to confirm  Esc to skip",
            (20, 140),
            SCREEN_TEXT_COLOR,
        )

    def _draw_highscores(
        self, buffer: Buffer, payload: HighscoresPayload
    ) -> None:
        """Top-10 list: rank, name, score."""
        self._facade.draw_text(
            buffer, "High Scores", (20, 30), SCREEN_TITLE_COLOR
        )
        if not payload.entries:
            self._facade.draw_text(
                buffer, "(no scores yet)", (20, 70), SCREEN_TEXT_COLOR
            )
        for index, (name, score) in enumerate(payload.entries[:10]):
            line = f"{index + 1}. {name} - {score}"
            self._facade.draw_text(
                buffer, line, (20, 70 + index * 24), SCREEN_TEXT_COLOR
            )
        self._facade.draw_text(
            buffer,
            "Esc to return",
            (20, self._layout.window_height - 30),
            SCREEN_TEXT_COLOR,
        )

    def _draw_instructions(self, buffer: Buffer) -> None:
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