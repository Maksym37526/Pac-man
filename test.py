"""Manual smoke test: real Config + real core (ghosts, collisions, tick).

    python3 test.py config.json
"""

import sys
from dataclasses import replace
from random import Random

from pacman.core.cheats import CheatCommand
from pacman.core.events import GameEvent
from pacman.data.cli import parse
from pacman.data.config import build_config
from pacman.data.loader import read_config, strip_comments, parse_json
from pacman.data.validator import validate_config
from pacman.errors import ConfigError
from pacman.maze.model import Direction
from pacman.render.facade import GraphicsFacade
from pacman.render.layout import fit_layout
from pacman.render.timing import FrameLimiter
from pacman.render.view_state import RenderGameState
from pacman.render.renderer import Renderer
from pacman.ui.events import InputEvent, translate
from pacman.ui.state_machine import (
    AppState, AppStateMachine, GameOverPayload, HighscoresPayload, VictoryPayload,
)
from pacman.game import load_highscores, new_game, save_score

_DIRECTION_BY_INPUT: dict[InputEvent, Direction] = {
    InputEvent.UP: Direction.UP,
    InputEvent.DOWN: Direction.DOWN,
    InputEvent.LEFT: Direction.LEFT,
    InputEvent.RIGHT: Direction.RIGHT,
}
_CHEAT_BY_INPUT: dict[InputEvent, CheatCommand] = {
    InputEvent.CHEAT_MASTER: CheatCommand.TOGGLE_CHEATS,
    InputEvent.CHEAT_INVINCIBLE: CheatCommand.TOGGLE_INVINCIBLE,
    InputEvent.CHEAT_FAST: CheatCommand.TOGGLE_SPEED,
    InputEvent.CHEAT_SKIP: CheatCommand.SKIP_LEVEL,
    InputEvent.CHEAT_CLEAR: CheatCommand.CLEAR_LEVEL,
    InputEvent.CHEAT_FRIGHT: CheatCommand.START_FRIGHT,
    InputEvent.CHEAT_LOSE: CheatCommand.LOSE_LIFE,
}


def start_run(config, rng: Random):
    """Build a fresh Session: core owns levels, score and lives now.

    Playtest tuning (matrix open point #2): defaults (8/7/4)
    cells/s are twitchy on turns. Ghost stays slower than the
    player so the game stays winnable; confirm with A and record.
    """
    session = new_game(config, rng)
    session.settings = replace(
        session.settings,
        player_speed=5.0,
        ghost_speed=4.5,
        frightened_speed=3.0,
    )
    return session


def main() -> None:
    try:
        config_path = parse(sys.argv[1:])
        raw_text = read_config(config_path)
        text = strip_comments(raw_text)
        validated = validate_config(parse_json(text))
        config = build_config(validated)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    rng = Random(config.seed)
    session = start_run(config, rng)

    max_cols = max(level.width for level in config.levels)
    max_rows = max(level.height for level in config.levels)
    layout = fit_layout(max_cols, max_rows)
    facade = GraphicsFacade(layout.window_width, layout.window_height, title="Pac-Man", font_size=layout.font_size)
    renderer = Renderer(facade, layout)
    machine = AppStateMachine()

    # Load highscores at startup
    highscore_entries = load_highscores(config)

    level_prepared = False
    limiter = FrameLimiter()

    running = True
    while running:
        dt = limiter.wait()

        for event in translate(
            facade.poll_events(),
            name_entry=(machine.state is AppState.NAME_ENTRY),
        ):
            prev_state = machine.state
            machine.handle(event)

            if machine.confirmed_name is not None:
                # Cheated runs show the name screen but never store:
                # cheats_used rises once and never lowers (core flag).
                if not session.cheats_used:
                    highscore_entries, _ = save_score(
                        config,
                        highscore_entries,
                        machine.confirmed_name,
                        session.level.score,
                    )
                machine.confirmed_name = None

            if prev_state is AppState.MAIN_MENU and machine.state is AppState.PLAYING:
                # Fresh run on every START_GAME: the old session is
                # finished (lives spent) or mid-run (abandoned pause).
                session = start_run(config, Random(config.seed))
                level_prepared = False
                continue

            if machine.state is AppState.PLAYING and isinstance(event, InputEvent):
                if event in _DIRECTION_BY_INPUT:
                    session.set_direction(_DIRECTION_BY_INPUT[event])
                elif event in _CHEAT_BY_INPUT:
                    for game_event in session.apply_cheat(_CHEAT_BY_INPUT[event]):
                        if game_event is GameEvent.GAME_OVER:
                            machine.state = AppState.GAME_OVER
                        elif game_event is GameEvent.GAME_WON:
                            machine.state = AppState.VICTORY
                        elif game_event is GameEvent.LEVEL_CLEARED:
                            level_prepared = False

        if machine.state is AppState.EXIT:
            running = False
            continue

        if machine.state is AppState.MAIN_MENU:
            renderer.draw_screen(AppState.MAIN_MENU, machine.main_menu_payload())
        elif machine.state is AppState.PAUSED:
            renderer.draw_screen(AppState.PAUSED, None)
        elif machine.state is AppState.VICTORY:
            renderer.draw_screen(AppState.VICTORY, VictoryPayload(final_score=session.level.score))
            # Auto-transition to NAME_ENTRY after a short delay or on keypress
            # For now, we'll transition on next event
        elif machine.state is AppState.GAME_OVER:
            renderer.draw_screen(AppState.GAME_OVER, GameOverPayload(final_score=session.level.score))
        elif machine.state is AppState.NAME_ENTRY:
            renderer.draw_screen(
                AppState.NAME_ENTRY,
                machine.name_entry_payload(cheated=session.cheats_used),
            )
        elif machine.state is AppState.HIGHSCORES:
            renderer.draw_screen(AppState.HIGHSCORES, HighscoresPayload(entries=[(e.name, e.score) for e in highscore_entries]))
        elif machine.state is AppState.INSTRUCTIONS:
            renderer.draw_screen(AppState.INSTRUCTIONS, None)
        elif machine.state is AppState.PLAYING:
            if not level_prepared:
                renderer.prepare_level(session.level.maze)
                level_prepared = True
            renderer.advance(dt)
            for game_event in session.tick(dt):
                if game_event is GameEvent.GAME_OVER:
                    machine.state = AppState.GAME_OVER
                    break
                if game_event is GameEvent.GAME_WON:
                    machine.state = AppState.VICTORY
                    break
                if game_event is GameEvent.LEVEL_CLEARED:
                    level_prepared = False
            renderer.draw_game(
                RenderGameState(
                    core=session.level, cheats=session.cheats
                )
            )
        else:
            print(f"reached {machine.state}, not yet drawable — closing")
            running = False
            continue

        renderer.present()

    facade.close()


if __name__ == "__main__":
    main()