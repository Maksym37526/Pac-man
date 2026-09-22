"""Manual smoke test: full loop, MAIN_MENU -> PLAYING via AppStateMachine.

Use Up/Down to navigate, Enter/Space to select. Selecting "Start Game"
switches to the game view built earlier (draw_game + HUD). Escape/close
quits from either screen.

    python3 -m pacman.render.manual_check_integrated
"""

from pacman.maze.model import Cell, Direction, Maze
from pacman.render.facade import GraphicsFacade
from pacman.render.fakes import tiny_game_state
from pacman.render.renderer import Renderer
from pacman.ui.events import InputEvent, translate
from pacman.ui.state_machine import AppState, AppStateMachine


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
    # Window sized for the menu; happens to be roomy enough for the 5x5
    # game view too, so one fixed window serves both screens (D3 spirit:
    # one size, decided once, reused everywhere).
    window_width, window_height = 1200, 1200

    facade = GraphicsFacade(window_width, window_height, title="menu -> playing integration test", font_size=64)    
    renderer = Renderer(facade, window_width, window_height)
    machine = AppStateMachine()

    maze = tiny_maze()
    game_state = tiny_game_state(maze)
    level_prepared = False

    running = True
    while running:
        input_events = translate(facade.poll_events())
        for event in input_events:
            machine.handle(event)

        if machine.state is AppState.EXIT:
            running = False
            continue

        if machine.state is AppState.MAIN_MENU:
            renderer.draw_screen(AppState.MAIN_MENU, machine.main_menu_payload())
        elif machine.state is AppState.PLAYING:
            if not level_prepared:
                renderer.prepare_level(maze)  # once per level, not every frame
                level_prepared = True
            renderer.draw_game(game_state)
        else:
            print(f"reached {machine.state}, not yet drawable — closing")
            running = False
            continue

        renderer.present()

    facade.close()


if __name__ == "__main__":
    main()