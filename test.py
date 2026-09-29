"""Manual smoke test: real Config + real core (ghosts, collisions, tick).

    python3 test.py config.json
"""

import sys
from random import Random

from pacman.core.events import GameEvent
from pacman.core.rules import set_direction, tick
from pacman.core.settings import GameSettings
from pacman.core.state import new_game_state
from pacman.data.cli import parse
from pacman.data.config import build_config
from pacman.data.loader import read_config, strip_comments, parse_json
from pacman.data.validator import validate_config
from pacman.errors import ConfigError
from pacman.maze.level import build_level
from pacman.maze.model import Direction
from pacman.render.facade import GraphicsFacade
from pacman.render.layout import fit_layout
from pacman.render.timing import FrameLimiter
from pacman.render.view_state import RenderGameState
from pacman.render.renderer import Renderer
from pacman.ui.cheats import CheatKind
from pacman.ui.events import InputEvent, translate
from pacman.ui.state_machine import (
    AppState, AppStateMachine, GameOverPayload, HighscoresPayload, VictoryPayload,
)
from pacman.data.highscore import HighscoreEntry
from pacman.game import load_highscores, save_score

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


def build_render_state(config, level_index: int, rng: Random, carried_score: int):
    """Build one level's maze + RenderGameState, via the real core pipeline.

    CAVEAT: new_game_state() always sets score=0; carrying score
    across levels means overwriting core_state.score directly here,
    which conflicts with state.py's "core/rules.py is the only
    writer" docstring. Needs a real answer from the colleague.
    """
    level_config = config.levels[level_index]
    maze, layout = build_level(
        width=level_config.width, height=level_config.height,
        pacgums=level_config.pacgum, level_index=level_index,
        config_seed=config.seed, rng=rng,
    )
    core_state = new_game_state(
        maze,
        layout,
        lives=config.lives,
        time_remaining=level_config.level_max_time,
        level_index=level_index,
        level_count=len(config.levels),
    )
    core_state.score = carried_score  # see CAVEAT above
    render_state = RenderGameState(core=core_state)
    return maze, render_state


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
    maze, game_state = build_render_state(config, level_index=0, rng=rng, carried_score=0)

    max_cols = max(level.width for level in config.levels)
    max_rows = max(level.height for level in config.levels)
    layout = fit_layout(max_cols, max_rows)
    facade = GraphicsFacade(layout.window_width, layout.window_height, title="Pac-Man", font_size=layout.font_size)
    renderer = Renderer(facade, layout)
    machine = AppStateMachine()

    # Load highscores at startup
    highscore_entries = load_highscores(config)

    # Playtest tuning (matrix open point #2): defaults (8/7/4)
    # cells/s are twitchy on turns. Ghost stays slower than the
    # player so the game stays winnable; confirm with A and record.
    settings = GameSettings(
        pacgum=config.points_per_pacgum,
        super_pacgum=config.points_per_super_pacgum,
        ghost=config.points_per_ghost,
        player_speed=5.0,
        ghost_speed=4.5,
        frightened_speed=3.0,
    )
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
                # Save highscore only; fresh state is built on next
                # START_GAME. Score is still valid: the run's core
                # is rebuilt only when a new game starts.
                highscore_entries, _ = save_score(
                    config,
                    highscore_entries,
                    machine.confirmed_name,
                    game_state.core.score,
                )
                machine.confirmed_name = None

            if prev_state is AppState.MAIN_MENU and machine.state is AppState.PLAYING:
                # Fresh run on every START_GAME: old core has lives=0 /
                # eaten pacgums / spent timer, so tick() would never
                # collide again (rules.py breaks when lives <= 0).
                # Rebuilding here also drops active cheats.
                rng = Random(config.seed)
                maze, game_state = build_render_state(config, level_index=0, rng=rng, carried_score=0)
                level_prepared = False
                continue

            if machine.state is AppState.PLAYING and isinstance(event, InputEvent):
                if event in _DIRECTION_BY_INPUT:
                    set_direction(game_state.core, _DIRECTION_BY_INPUT[event])
                elif event in _CHEAT_TOGGLE_BY_INPUT:
                    game_state.cheats.toggle(_CHEAT_TOGGLE_BY_INPUT[event])
                elif event is InputEvent.CHEAT_EXTRA_LIFE:
                    game_state.core.lives += 1
                elif event is InputEvent.CHEAT_LEVEL_SKIP:
                    # Skip to next level
                    next_index = game_state.core.level_index + 1
                    if next_index >= len(config.levels):
                        machine.state = AppState.VICTORY
                    else:
                        maze, game_state = build_render_state(config, next_index, rng, game_state.core.score)
                        level_prepared = False

        if machine.state is AppState.EXIT:
            running = False
            continue

        if machine.state is AppState.MAIN_MENU:
            renderer.draw_screen(AppState.MAIN_MENU, machine.main_menu_payload())
        elif machine.state is AppState.PAUSED:
            renderer.draw_screen(AppState.PAUSED, None)
        elif machine.state is AppState.VICTORY:
            renderer.draw_screen(AppState.VICTORY, VictoryPayload(final_score=game_state.core.score))
            # Auto-transition to NAME_ENTRY after a short delay or on keypress
            # For now, we'll transition on next event
        elif machine.state is AppState.GAME_OVER:
            renderer.draw_screen(AppState.GAME_OVER, GameOverPayload(final_score=game_state.core.score))
        elif machine.state is AppState.NAME_ENTRY:
            renderer.draw_screen(AppState.NAME_ENTRY, machine.name_entry_payload())
        elif machine.state is AppState.HIGHSCORES:
            renderer.draw_screen(AppState.HIGHSCORES, HighscoresPayload(entries=[(e.name, e.score) for e in highscore_entries]))
        elif machine.state is AppState.INSTRUCTIONS:
            renderer.draw_screen(AppState.INSTRUCTIONS, None)
        elif machine.state is AppState.PLAYING:
            if not level_prepared:
                renderer.prepare_level(maze)
                level_prepared = True
            renderer.advance(dt)
            for game_event in tick(game_state.core, settings, rng, dt):
                print(game_event)
                if game_event is GameEvent.GAME_OVER:
                    machine.state = AppState.GAME_OVER
                    break
                if game_event is GameEvent.LEVEL_CLEARED:
                    next_index = game_state.core.level_index + 1
                    if next_index >= len(config.levels):
                        machine.state = AppState.VICTORY
                        break
                    maze, game_state = build_render_state(config, next_index, rng, game_state.core.score)
                    level_prepared = False
            renderer.draw_game(game_state)
        else:
            print(f"reached {machine.state}, not yet drawable — closing")
            running = False
            continue

        renderer.present()

    facade.close()


if __name__ == "__main__":
    main()