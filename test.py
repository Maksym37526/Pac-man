"""Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py config.json
"""

import sys
import time
from random import Random

from pacman.core.rules import set_direction, tick
from pacman.core.state import ScoringRules, new_game_state
from pacman.data.cli import parse
from pacman.data.config import Config, build_config
from pacman.data.loader import read_config, strip_comments, parse_json
from pacman.data.validator import validate_config
from pacman.errors import ConfigError
from pacman.log import setup_logging
from pacman.maze.level import build_level
from pacman.maze.model import Direction
from pacman.render.facade import GraphicsFacade
from pacman.render.fakes import Entity, EntityKind, RenderGameState
from pacman.render.renderer import Renderer, maze_window_size
from pacman.ui.cheats import CheatKind
from pacman.ui.events import InputEvent, translate
from pacman.core.events import GameEvent

from pacman.ui.events import InputEvent, TypedChar, translate
from pacman.ui.state_machine import AppState, AppStateMachine, HighscoresPayload, VictoryPayload

_DIRECTION_BY_INPUT: dict[InputEvent, Direction] = {
    InputEvent.UP: Direction.UP,
    InputEvent.DOWN: Direction.DOWN,
    InputEvent.LEFT: Direction.LEFT,
    InputEvent.RIGHT: Direction.RIGHT,
}

_CHEAT_TOGGLE_BY_INPUT: dict[InputEvent, CheatKind] = {
    InputEvent.CHEAT_INVINCIBILITY: CheatKind.INVINCIBILITY,
    InputEvent.CHEAT_GHOST_FREEZE: CheatKind.GHOST_FREEZE,
    InputEvent.CHEAT_SPEED: CheatKind.INCREASED_SPEED,
}

def advance_to_level(
    config, level_index: int, rng: Random, carried_score: int, carried_lives: int
):
    """Build the next level, carrying score and lives across (VI.7).

    CAVEAT: new_game_state() always sets score=0 — there is no core
    API for "start a level but keep the running score/lives". Setting
    core_state.score/lives directly here works (GameState isn't
    frozen) but violates the "core/rules.py is the only writer"
    contract from state.py's own docstring. This needs a real answer
    from the colleague — either a new_game_state() parameter, or a
    dedicated "advance_level" function in core — not a silent
    workaround from the composition layer.
    """
    level_config = config.levels[level_index]
    maze, layout = build_level(
        width=level_config.width,
        height=level_config.height,
        pacgums=level_config.pacgum,
        level_index=level_index,
        config_seed=config.seed,
        rng=rng,
    )
    core_state = new_game_state(maze, layout)
    core_state.score = carried_score  # see CAVEAT above
    ghost_kinds = (EntityKind.GHOST_1, EntityKind.GHOST_2, EntityKind.GHOST_3, EntityKind.GHOST_4)
    ghosts = [Entity.standing_at(kind, corner) for kind, corner in zip(ghost_kinds, layout.ghost_starts)]
    return maze, RenderGameState(
        core=core_state, ghosts=ghosts, lives=carried_lives, level_index=level_index, level_count=len(config.levels)
    )

def window_size_for_config(config: Config) -> tuple[int, int]:
    """Compute the fixed window size for a run, per D3.

    Sized once from the largest level's dimensions in the config —
    never per-level — so smaller levels are centred by the renderer
    rather than resizing the window.
    """
    max_width = max(level.width for level in config.levels)
    max_height = max(level.height for level in config.levels)
    return maze_window_size(max_width, max_height)


def run(config: Config) -> None:
    """Run the game loop for a validated config.

    Args:
        config: Immutable, validated run configuration.
    """
    rng = Random(config.seed)
    level_index = 0
    level_config = config.levels[level_index]
    maze, layout = build_level(
        width=level_config.width,
        height=level_config.height,
        pacgums=level_config.pacgum,
        level_index=level_index,
        config_seed=config.seed,
        rng=rng,
    )

    window_width, window_height = window_size_for_config(config)
    facade = GraphicsFacade(window_width, window_height, title="Pac-Man")
    renderer = Renderer(facade, window_width, window_height)
    machine = AppStateMachine()

    core_state = new_game_state(maze, layout)
    ghost_kinds = (EntityKind.GHOST_1, EntityKind.GHOST_2, EntityKind.GHOST_3, EntityKind.GHOST_4)
    ghosts = [Entity.standing_at(kind, corner) for kind, corner in zip(ghost_kinds, layout.ghost_starts)]
    game_state = RenderGameState(core=core_state, ghosts=ghosts, lives=config.lives, level_count=len(config.levels))

    scoring = ScoringRules(
        pacgum=config.points_per_pacgum,
        super_pacgum=config.points_per_super_pacgum,
        ghost=config.points_per_ghost,
    )
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
            if machine.state is AppState.PLAYING:
                if event in _DIRECTION_BY_INPUT:
                    set_direction(game_state.core, _DIRECTION_BY_INPUT[event])
                elif event in _CHEAT_TOGGLE_BY_INPUT:
                    game_state.cheats.toggle(_CHEAT_TOGGLE_BY_INPUT[event])
                elif event is InputEvent.CHEAT_EXTRA_LIFE:
                    game_state.lives += 1
                elif event is InputEvent.CHEAT_LEVEL_SKIP:
                    print("CHEAT_LEVEL_SKIP requested — not yet implemented")

        if machine.state is AppState.EXIT:
            running = False
            continue

        if machine.state is AppState.MAIN_MENU:
            renderer.draw_screen(AppState.MAIN_MENU, machine.main_menu_payload())
        elif machine.state is AppState.PAUSED:
            renderer.draw_screen(AppState.PAUSED, None)
        elif machine.state is AppState.VICTORY:
            renderer.draw_screen(AppState.VICTORY, VictoryPayload(final_score=game_state.core.score))
        elif machine.state is AppState.NAME_ENTRY:
            renderer.draw_screen(AppState.NAME_ENTRY, machine.name_entry_payload())
        elif machine.state is AppState.HIGHSCORES:
            renderer.draw_screen(AppState.HIGHSCORES, HighscoresPayload(entries=[]))  # placeholder
        elif machine.state is AppState.INSTRUCTIONS:
            renderer.draw_screen(AppState.INSTRUCTIONS, None)
        elif machine.state is AppState.PLAYING:
            if not level_prepared:
                renderer.prepare_level(maze)
                level_prepared = True
            events = tick(game_state.core, scoring, dt)
            for game_event in events:
                print(game_event)
                if game_event is GameEvent.LEVEL_CLEARED:
                    next_index = game_state.level_index + 1
                    if next_index >= len(config.levels):
                        machine.state = AppState.VICTORY
                        break
                    maze, game_state = advance_to_level(
                        config, next_index, rng, game_state.core.score, game_state.lives
                    )
                    level_prepared = False
            renderer.draw_game(game_state)


        else:
            print(f"reached {machine.state}, not yet drawable — closing")
            running = False
            continue

        renderer.present()

    facade.close()


def main(argv: list[str]) -> int:
    """Run the game.

    Args:
        argv: Command line arguments, excluding the program name.

    Returns:
        Process exit code: 0 on success, non-zero on error.
    """
    setup_logging()
    try:
        config_parse = parse(argv)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Usage: python3 pac-man.py config.json", file=sys.stderr)
        return 2
    try:
        raw_text = read_config(config_parse)
        text = strip_comments(raw_text)
        validated = validate_config(parse_json(text))
        config = build_config(validated)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    run(config)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))