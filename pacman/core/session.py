"""Multi-level game session (Phase 7).

A Session lives above GameState: it owns everything that spans
the whole run (settings, level list, run RNG, finished flag)
and holds the current level's GameState as a replaceable field.

Decision A (recorded in module_contracts.md): score and lives
stay in GameState, so rules.tick keeps its signature and every
Phase 5/6 test keeps working. On a level transition the Session
copies exactly those two fields into the fresh state. The copy
is guarded by dedicated tests, so the "forgotten field" risk is
limited to two named fields instead of an open-ended list.

Decision B (REQ-104): time-up costs one life, respawns everybody
at home and resets the timer to full. Pacgums stay eaten. On the
last life time-up ends the game with GAME_OVER.

Pause (REQ-109) needs no code here: B pauses by not calling
tick, so no dt reaches the level timer. Core never reads a
system clock, only the dt it is given.
"""

from dataclasses import dataclass
from random import Random

from pacman.core.events import GameEvent
from pacman.core.rules import respawn_after_catch
from pacman.core.rules import set_direction as rules_set_direction
from pacman.core.rules import tick as rules_tick
from pacman.core.settings import GameSettings
from pacman.core.state import GameState, new_game_state
from pacman.maze.level import build_level
from pacman.maze.model import Direction


@dataclass(frozen=True)
class LevelSpec:
    """One level's shape, in core's own vocabulary.

    Core must not import data/, so the composition layer
    translates each LevelConfig into this record.
    """

    width: int
    height: int
    pacgums: int
    level_max_time: int


@dataclass
class Session:
    """One full run through every level.

    Attributes:
        level: Current level's mutable state.
        settings: Static tuning, shared by all levels.
        rng: The run's random source, shared by all levels.
        levels: Every level's spec, in play order.
        config_seed: Top-level seed, deciding each maze.
        finished: True after GAME_OVER or GAME_WON.
        won: True only after GAME_WON.
    """

    level: GameState
    settings: GameSettings
    rng: Random
    levels: tuple[LevelSpec, ...]
    config_seed: int
    finished: bool = False
    won: bool = False

    def set_direction(self, direction: Direction) -> None:
        """Store the player's desired turn for the level.

        Args:
            direction: The desired travel direction.
        """
        rules_set_direction(self.level, direction)

    def tick(self, dt: float) -> list[GameEvent]:
        """Advance the run by dt seconds.

        Finished sessions ignore ticks: B may call a few more
        times while switching screens, and events must fire
        exactly once. Death has priority over clearing: when
        one tick brings both GAME_OVER and LEVEL_CLEARED, the
        run ends in defeat and no transition happens.

        Args:
            dt: Seconds since the last tick.

        Returns:
            Events that happened during this tick, in order.
        """
        if self.finished:
            return []
        events = rules_tick(self.level, self.settings, self.rng, dt)
        if GameEvent.TIME_UP in events:
            self._on_time_up(events)
            return events
        if GameEvent.GAME_OVER in events:
            self.finished = True
            return events
        if GameEvent.LEVEL_CLEARED in events:
            self._on_level_cleared(events)
        return events

    def _on_time_up(self, events: list[GameEvent]) -> None:
        """Apply decision B: lose a life, respawn, reset timer."""
        self.level.lives -= 1
        fright_cancelled = respawn_after_catch(self.level)
        if (
            fright_cancelled
            and GameEvent.FRIGHT_ENDED not in events
        ):
            events.append(GameEvent.FRIGHT_ENDED)
        if self.level.lives <= 0:
            events.append(GameEvent.GAME_OVER)
            self.finished = True
            return
        spec = self.levels[self.level.level_index]
        self.level.time_remaining = float(spec.level_max_time)

    def _on_level_cleared(self, events: list[GameEvent]) -> None:
        """Move to the next level, or win on the last one."""
        if self.level.level_index + 1 >= len(self.levels):
            events.append(GameEvent.GAME_WON)
            self.finished = True
            self.won = True
            return
        score = self.level.score
        lives = self.level.lives
        next_index = self.level.level_index + 1
        spec = self.levels[next_index]
        maze, layout = build_level(
            spec.width,
            spec.height,
            spec.pacgums,
            next_index,
            self.config_seed,
            self.rng,
        )
        self.level = new_game_state(
            maze,
            layout,
            lives=lives,
            time_remaining=float(spec.level_max_time),
            level_index=next_index,
            level_count=len(self.levels),
        )
        self.level.score = score


def new_session(
    levels: tuple[LevelSpec, ...],
    settings: GameSettings,
    rng: Random,
    config_seed: int,
    lives: int = 3,
) -> Session:
    """Build a session starting at level zero.

    Args:
        levels: Every level's spec, at least one.
        settings: Static tuning for the run.
        rng: The run's random source.
        config_seed: Top-level seed from the config.
        lives: Player lives, from the config.

    Returns:
        A session whose level is the first maze.

    Raises:
        ValueError: If no level spec was supplied.
    """
    if not levels:
        raise ValueError("a session needs at least one level")
    first = levels[0]
    maze, layout = build_level(
        first.width,
        first.height,
        first.pacgums,
        0,
        config_seed,
        rng,
    )
    level = new_game_state(
        maze,
        layout,
        lives=lives,
        time_remaining=float(first.level_max_time),
        level_index=0,
        level_count=len(levels),
    )
    return Session(
        level=level,
        settings=settings,
        rng=rng,
        levels=levels,
        config_seed=config_seed,
    )
