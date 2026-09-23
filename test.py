"""Manual smoke test: full loop with real core movement via tick().

Use arrow keys/WASD to move. Up/Down navigate the menu, Enter/Space
selects. Escape/close quits from either screen.

    python3 -m pacman.render.manual_check_integrated
"""

import time

from pacman.core.rules import set_direction, tick
from pacman.core.state import ScoringRules
from pacman.maze.model import Cell, Direction, Maze
from pacman.render.facade import GraphicsFacade
from pacman.render.fakes import tiny_game_state
from pacman.render.renderer import Renderer
from pacman.ui.events import InputEvent, translate
from pacman.ui.state_machine import AppState, AppStateMachine

_DIRECTION_BY_INPUT: dict[InputEvent, Direction] = {
    InputEvent.UP: Direction.UP,
    InputEvent.DOWN: Direction.DOWN,
    InputEvent.LEFT: Direction.LEFT,
    InputEvent.RIGHT: Direction.RIGHT,
}


def tiny_maze() -> Maze:
    """5x5 fully open maze — centre and corners are distinct cells."""
    width, height = 5, 5
    all_cells = [Cell(c, r) for r in range(height) for c in range(width)]
    passages: dict[Cell, frozenset[Direction]] = {}
    for cell in all_cells:
        open_dirs = set()
        for d in Direction:
            neighbour = Cell(cell.col + d.vector_x, cell.row + d.vector_y)
            if 0 <= neighbour.col < width and 0 <= neighbour.row < height:
                open_dirs.add(d)
        passages[cell] = frozenset(open_dirs)
    return Maze(
        width=width,
        height=height,
        passages=passages,
        blocks=frozenset(),
        centre=Cell(2, 2),
        corners=(Cell(0, 0), Cell(4, 0), Cell(0, 4), Cell(4, 4)),
    )


def main() -> None:
    window_width, window_height = 1200, 1200

    facade = GraphicsFacade(window_width, window_height, title="tick() integration test", font_size=64)
    renderer = Renderer(facade, window_width, window_height)
    machine = AppStateMachine()

    maze = tiny_maze()
    game_state = tiny_game_state(maze)
    scoring = ScoringRules(pacgum=10, super_pacgum=50, ghost=200)
    level_prepared = False

    last_time = time.monotonic()

    running = True
    while running:
        now = time.monotonic()
        dt = now - last_time
        last_time = now

        input_events = translate(facade.poll_events())
        for event in input_events:
            machine.handle(event)
            if machine.state is AppState.PLAYING and event in _DIRECTION_BY_INPUT:
                set_direction(game_state.core, _DIRECTION_BY_INPUT[event])

        if machine.state is AppState.EXIT:
            running = False
            continue

        if machine.state is AppState.MAIN_MENU:
            renderer.draw_screen(AppState.MAIN_MENU, machine.main_menu_payload())
        elif machine.state is AppState.PLAYING:
            if not level_prepared:
                renderer.prepare_level(maze)
                level_prepared = True
            events = tick(game_state.core, scoring, dt)
            for game_event in events:
                print(game_event)  # placeholder — real HUD reaction later
            renderer.draw_game(game_state)
        else:
            print(f"reached {machine.state}, not yet drawable — closing")
            running = False
            continue

        renderer.present()

    facade.close()


if __name__ == "__main__":
    main()