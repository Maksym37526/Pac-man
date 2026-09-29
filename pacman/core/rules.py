"""One game tick: movement, fright, collisions, win check.

The only writer of GameState. The renderer reads the state and
never mutates it.

Step order is load-bearing:
    1. clamp dt once, at the entry
    2. level timer (TIME_UP on the crossing tick only, early out)
    3. fright timer (FRIGHT_ENDED on the crossing tick only)
    4. eaten-ghost timers (home teleport on expiry)
    5. player move and eating (super starts fright)
    6. ghost moves (AI picks next_direction every tick)
    7. collisions (one life per tick at most)
    8. victory check, as in Phase 5
"""

from random import Random

from pacman.core.collision import is_touching
from pacman.core.entity import EntityMode
from pacman.core.events import GameEvent
from pacman.core.ghost import choose_ghost_direction, exit_candidates
from pacman.core.movement import MAX_DT, advance
from pacman.core.settings import GameSettings
from pacman.core.state import GameState
from pacman.maze.model import Direction


def set_direction(state: GameState, direction: Direction) -> None:
    """Store the player's desired turn.

    Takes a Direction, not an InputEvent: InputEvent lives in
    ui/, which core must not import. The composition layer
    translates MOVE_* into Direction and calls this.

    Args:
        state: The game state to update.
        direction: The desired travel direction.
    """
    state.player.next_direction = direction


def respawn_after_catch(state: GameState) -> bool:
    """Put the player and every ghost back at home, standing.

    Ghosts return to their corners so the player gets breathing
    room (VI.2 is silent on ghosts; leaving them in place would
    burn three lives in a second). An active fright is cancelled:
    every ghost wakes up NORMAL.

    Args:
        state: The game state, mutated in place.

    Returns:
        True if a fright was active and is now cancelled, so the
        caller can emit the paired FRIGHT_ENDED event.
    """
    was_frightened = state.frightened_remaining > 0.0
    state.player.place_at_home()
    for ghost in state.ghosts:
        ghost.place_at_home()
        ghost.mode = EntityMode.NORMAL
        ghost.mode_timer = 0.0
    state.frightened_remaining = 0.0
    return was_frightened


def start_fright(state: GameState, duration: float) -> None:
    """Turn every hunting ghost edible for a duration.

    Shared by the super-pacgum branch of tick and the
    START_FRIGHT cheat: one implementation, two callers.

    Args:
        state: The game state, mutated in place.
        duration: Seconds ghosts stay edible.
    """
    state.frightened_remaining = duration
    for ghost in state.ghosts:
        if ghost.mode is EntityMode.NORMAL:
            ghost.mode = EntityMode.FRIGHTENED


def tick(
    state: GameState,
    settings: GameSettings,
    rng: Random,
    dt: float,
    invincible: bool = False,
) -> list[GameEvent]:
    """Advance the game by dt seconds.

    Args:
        state: The game state, mutated in place.
        settings: Static tuning (speeds, points, durations).
        rng: The run's random source for ghost turns.
        dt: Seconds since the last tick, clamped to MAX_DT.
        invincible: Cheat shield against NORMAL ghosts. Eating
            frightened ghosts and the level timer work as
            always: the shield is narrow, never "turn all off".

    Returns:
        Events that happened during this tick, in order.
    """
    events: list[GameEvent] = []
    if dt <= 0.0:
        return events
    dt = min(dt, MAX_DT)

    if state.time_remaining <= 0.0:
        return events
    state.time_remaining = max(0.0, state.time_remaining - dt)
    if state.time_remaining <= 0.0:
        events.append(GameEvent.TIME_UP)
        return events

    if state.frightened_remaining > 0.0:
        cooled = max(0.0, state.frightened_remaining - dt)
        state.frightened_remaining = cooled
        if cooled <= 0.0:
            for ghost in state.ghosts:
                if ghost.mode is EntityMode.FRIGHTENED:
                    ghost.mode = EntityMode.NORMAL
            events.append(GameEvent.FRIGHT_ENDED)

    for ghost in state.ghosts:
        if ghost.mode is EntityMode.EATEN:
            ghost.mode_timer -= dt
            if ghost.mode_timer <= 0.0:
                ghost.place_at_home()
                if state.frightened_remaining > 0.0:
                    ghost.mode = EntityMode.FRIGHTENED
                else:
                    ghost.mode = EntityMode.NORMAL
                ghost.mode_timer = 0.0

    entered = advance(
        state.player, state.maze, settings.player_speed, dt
    )
    ate_something = False
    for cell in entered:
        if cell in state.pacgums:
            state.pacgums.discard(cell)
            state.score += settings.pacgum
            events.append(GameEvent.PACGUM_EATEN)
            ate_something = True
        if cell in state.super_pacgums:
            state.super_pacgums.discard(cell)
            state.score += settings.super_pacgum
            events.append(GameEvent.SUPER_PACGUM_EATEN)
            ate_something = True
            start_fright(state, settings.fright_duration)
            events.append(GameEvent.FRIGHT_STARTED)

    for index, ghost in enumerate(state.ghosts):
        if ghost.mode is EntityMode.EATEN:
            continue
        speed = settings.ghost_speed
        if ghost.mode is EntityMode.FRIGHTENED:
            speed = settings.frightened_speed
        stood_still = ghost.direction is None
        entered_cells = advance(ghost, state.maze, speed, dt)
        if not entered_cells and not stood_still:
            continue
        randomness = settings.ghost_randomness[index]
        candidates = exit_candidates(
            state.maze, ghost.cell, ghost.direction
        )
        if candidates:
            ghost.next_direction = choose_ghost_direction(
                ghost.cell,
                candidates,
                state.player.cell,
                ghost.mode is EntityMode.FRIGHTENED,
                randomness,
                rng,
            )

    for ghost in state.ghosts:
        if state.lives <= 0:
            break
        if not is_touching(
            state.player, ghost, settings.collision_radius
        ):
            continue
        if ghost.mode is EntityMode.FRIGHTENED:
            ghost.mode = EntityMode.EATEN
            ghost.mode_timer = settings.respawn_delay
            state.score += settings.ghost
            events.append(GameEvent.GHOST_EATEN)
        elif ghost.mode is EntityMode.NORMAL and not invincible:
            state.lives -= 1
            events.append(GameEvent.PLAYER_CAUGHT)
            fright_cancelled = respawn_after_catch(state)
            if fright_cancelled:
                events.append(GameEvent.FRIGHT_ENDED)
            if state.lives <= 0:
                events.append(GameEvent.GAME_OVER)
            break

    if (
        ate_something
        and not state.pacgums
        and not state.super_pacgums
    ):
        events.append(GameEvent.LEVEL_CLEARED)
    return events
