"""Tests for ghosts: AI choice and in-game behaviour (Phase 6)."""

from random import Random

from pacman.core.collision import (
    has_swapped,
    is_touching,
    world_position,
)
from pacman.core.entity import (
    Entity,
    EntityKind,
    EntityMode,
)
from pacman.core.events import GameEvent
from pacman.core.ghost import (
    choose_ghost_direction,
    exit_candidates,
    manhattan,
)
from pacman.core.rules import set_direction, tick
from pacman.core.settings import GameSettings
from pacman.core.state import GameState, new_game_state
from pacman.maze.adapter import make_maze
from pacman.maze.fake import open_grid
from pacman.maze.layout import gen_layout
from pacman.maze.model import Cell, Direction, Maze, step
from pacman.maze.normalize import normalize
from tests.helpers import run_for

SETTINGS = GameSettings(
    pacgum=10, super_pacgum=50, ghost=200
)
QUIET = GameSettings(
    pacgum=10,
    super_pacgum=50,
    ghost=200,
    ghost_speed=0.0,
    frightened_speed=0.0,
)
ONE_CELL = 1.0 / SETTINGS.player_speed


def _park_others(state: GameState, keep: int = 0) -> None:
    """Freeze every ghost but one as long-waiting EATEN."""
    for index, ghost in enumerate(state.ghosts):
        if index != keep:
            ghost.mode = EntityMode.EATEN
            ghost.mode_timer = 999.0


# --- Pure AI: pacman.core.ghost ---


def test_manhattan_counts_steps() -> None:
    """Grid distance ignores walls, sums both axes."""
    assert manhattan(Cell(0, 0), Cell(3, 4)) == 7
    assert manhattan(Cell(2, 2), Cell(2, 2)) == 0


def test_chases_target(empty_state: GameState) -> None:
    """From a corridor picks the exit closer to the target."""
    state: GameState = empty_state
    maze = state.maze
    cell = Cell(2, 2)
    candidates = exit_candidates(maze, cell, Direction.RIGHT)
    picked = choose_ghost_direction(
        cell, candidates, Cell(4, 2), False, 0.0, Random(1)
    )
    assert picked == Direction.RIGHT


def test_no_u_turn(empty_state: GameState) -> None:
    """The reverse direction is excluded when alternatives exist."""
    state: GameState = empty_state
    candidates = exit_candidates(
        state.maze, Cell(2, 2), Direction.RIGHT
    )
    assert Direction.LEFT not in candidates
    assert candidates != []


def test_u_turn_in_dead_end() -> None:
    """With no other way out the reverse is the only candidate."""
    maze = Maze(
        width=3,
        height=1,
        passages={
            Cell(0, 0): frozenset({Direction.RIGHT}),
            Cell(1, 0): frozenset(
                {Direction.LEFT, Direction.RIGHT}
            ),
            Cell(2, 0): frozenset({Direction.LEFT}),
        },
        blocks=frozenset(),
        centre=Cell(1, 0),
        corners=(Cell(0, 0), Cell(2, 0), Cell(0, 0), Cell(2, 0)),
    )
    assert exit_candidates(maze, Cell(2, 0), Direction.RIGHT) == [
        Direction.LEFT
    ]


def test_flees_target(empty_state: GameState) -> None:
    """When fleeing picks the exit farther from the target."""
    state: GameState = empty_state
    maze = state.maze
    cell = Cell(2, 2)
    candidates = exit_candidates(maze, cell, Direction.RIGHT)
    before = manhattan(cell, Cell(4, 2))
    picked = choose_ghost_direction(
        cell, candidates, Cell(4, 2), True, 0.0, Random(2)
    )
    after = manhattan(step(cell, picked), Cell(4, 2))
    assert after > before


def test_zero_randomness_is_deterministic(
    empty_state: GameState,
) -> None:
    """The same input always gives the same exit."""
    state: GameState = empty_state
    maze = state.maze
    cell = Cell(2, 2)
    candidates = exit_candidates(maze, cell, Direction.RIGHT)
    first = choose_ghost_direction(
        cell, candidates, Cell(0, 0), False, 0.0, Random(3)
    )
    second = choose_ghost_direction(
        cell, candidates, Cell(0, 0), False, 0.0, Random(99)
    )
    assert first == second


def test_randomness_spreads_choices(
    empty_state: GameState,
) -> None:
    """Full randomness over several seeds visits several exits."""
    state: GameState = empty_state
    maze = state.maze
    cell = Cell(2, 2)
    candidates = exit_candidates(maze, cell, Direction.RIGHT)
    assert len(candidates) >= 2
    seen = {
        choose_ghost_direction(
            cell,
            candidates,
            Cell(4, 2),
            False,
            1.0,
            Random(seed),
        )
        for seed in range(20)
    }
    assert len(seen) > 1


# --- Collision unit tests: pacman.core.collision ---


def test_world_position_interpolates() -> None:
    """Half progress lands halfway between the two cells."""
    entity = Entity.standing_at(EntityKind.PLAYER, Cell(1, 2))
    entity.prev_cell = Cell(1, 2)
    entity.cell = Cell(2, 2)
    entity.progress = 0.5
    x, y = world_position(entity)
    assert abs(x - 1.5) < 1e-9
    assert abs(y - 2.0) < 1e-9


def test_standing_world_position_is_exact() -> None:
    """Equal cells render exactly there for any progress."""
    entity = Entity.standing_at(EntityKind.PLAYER, Cell(3, 3))
    x, y = world_position(entity)
    assert (x, y) == (3.0, 3.0)


def test_swap_counts_as_touch() -> None:
    """Exchanged cells touch even when far apart in world units."""
    player = Entity.standing_at(EntityKind.PLAYER, Cell(1, 2))
    ghost = Entity.standing_at(EntityKind.GHOST_1, Cell(2, 2))
    player.prev_cell = Cell(1, 2)
    player.cell = Cell(2, 2)
    player.progress = 0.01
    ghost.prev_cell = Cell(2, 2)
    ghost.cell = Cell(1, 2)
    ghost.progress = 0.01
    assert has_swapped(player, ghost) is True
    assert is_touching(player, ghost, 0.0) is True


def test_distant_cells_do_not_touch(
    empty_state: GameState,
) -> None:
    """No swap and far apart means no collision."""
    state: GameState = empty_state
    assert (
        is_touching(
            state.player,
            state.ghosts[0],
            SETTINGS.collision_radius,
        )
        is False
    )


# --- In-game behaviour: pacman.core.rules.tick ---


def test_ghost_approaches_player(
    empty_state: GameState,
) -> None:
    """A hunting ghost shortens its distance within half a second."""
    state: GameState = empty_state
    _park_others(state)
    ghost = state.ghosts[0]
    before = manhattan(state.player.cell, ghost.cell)
    assert before > 0
    run_for(state, SETTINGS, Random(4), 0.3)
    after = manhattan(state.player.cell, ghost.cell)
    assert after < before


def test_catch_costs_a_life(empty_state: GameState) -> None:
    """Touching a NORMAL ghost respawns the player at home."""
    state: GameState = empty_state
    ghost = state.ghosts[0]
    ghost.cell = Cell(2, 2)
    ghost.prev_cell = Cell(2, 2)
    events = tick(state, QUIET, Random(5), 0.05)
    assert GameEvent.PLAYER_CAUGHT in events
    assert state.lives == 2
    assert state.player.cell == state.maze.centre
    assert state.player.direction is None
    for home_ghost, corner in zip(
        state.ghosts, state.maze.corners, strict=True
    ):
        assert home_ghost.cell == corner


def test_catch_on_last_life_is_game_over(
    empty_state: GameState,
) -> None:
    """Losing the final life emits GAME_OVER as well."""
    state: GameState = empty_state
    state.lives = 1
    ghost = state.ghosts[0]
    ghost.cell = Cell(2, 2)
    ghost.prev_cell = Cell(2, 2)
    events = tick(state, QUIET, Random(6), 0.05)
    assert GameEvent.PLAYER_CAUGHT in events
    assert GameEvent.GAME_OVER in events
    assert state.lives == 0


def test_head_on_pass_is_caught(
    empty_state: GameState,
) -> None:
    """Walking into an oncoming ghost ends in a catch.

    The player heads right along row 2 while ghost 1 hunts from
    the right corner. They meet head-on; whether the tick that
    connects them fires via proximity or via the cell swap, the
    player is caught within two seconds.
    """
    state: GameState = empty_state
    _park_others(state)
    player = state.player
    player.cell = Cell(1, 2)
    player.prev_cell = Cell(1, 2)
    player.progress = 0.0
    player.direction = None
    set_direction(state, Direction.RIGHT)
    ghost = state.ghosts[0]
    ghost.cell = Cell(3, 2)
    ghost.prev_cell = Cell(3, 2)
    ghost.progress = 0.0
    ghost.direction = None
    ghost.next_direction = None
    events = run_for(state, SETTINGS, Random(7), 2.0)
    assert GameEvent.PLAYER_CAUGHT in events


def test_super_frightens_ghosts(
    empty_state: GameState,
) -> None:
    """Eating a super turns every NORMAL ghost FRIGHTENED."""
    state: GameState = empty_state
    state.super_pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, QUIET, Random(8), 1.5 * ONE_CELL)
    assert GameEvent.FRIGHT_STARTED in events
    assert state.frightened_remaining > 0.0
    assert all(
        ghost.mode is EntityMode.FRIGHTENED
        for ghost in state.ghosts
    )


def test_fright_ends_once(empty_state: GameState) -> None:
    """FRIGHT_ENDED fires exactly once and restores NORMAL."""
    short = GameSettings(
        pacgum=10,
        super_pacgum=50,
        ghost=200,
        ghost_speed=0.0,
        frightened_speed=0.0,
        fright_duration=0.4,
    )
    state: GameState = empty_state
    state.super_pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, short, Random(9), 1.5 * ONE_CELL)
    assert GameEvent.FRIGHT_STARTED in events
    events = run_for(state, short, Random(9), 1.0)
    assert events.count(GameEvent.FRIGHT_ENDED) == 1
    assert all(
        ghost.mode is EntityMode.NORMAL
        for ghost in state.ghosts
    )
    extra = tick(state, short, Random(9), 0.1)
    assert GameEvent.FRIGHT_ENDED not in extra


def test_eating_frightened_ghost(
    empty_state: GameState,
) -> None:
    """Touching an edible ghost scores Z and parks it EATEN."""
    state: GameState = empty_state
    state.super_pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    run_for(state, QUIET, Random(10), 1.5 * ONE_CELL)
    assert state.frightened_remaining > 0.0
    score_after_super = state.score
    ghost = state.ghosts[0]
    ghost.cell = state.player.cell
    ghost.prev_cell = state.player.cell
    ghost.progress = 0.0
    events = tick(state, QUIET, Random(10), 0.05)
    assert GameEvent.GHOST_EATEN in events
    assert state.score == score_after_super + QUIET.ghost
    assert ghost.mode is EntityMode.EATEN
    assert state.lives == 3


def test_eaten_ghost_ignores_touch(
    empty_state: GameState,
) -> None:
    """An EATEN ghost neither catches nor scores."""
    state: GameState = empty_state
    ghost = state.ghosts[0]
    ghost.mode = EntityMode.EATEN
    ghost.mode_timer = 5.0
    ghost.cell = state.player.cell
    ghost.prev_cell = state.player.cell
    events = tick(state, QUIET, Random(11), 0.05)
    assert events == []
    assert state.lives == 3


def test_eaten_ghost_returns_home(
    empty_state: GameState,
) -> None:
    """After the delay the eaten ghost stands at home NORMAL."""
    quick = GameSettings(
        pacgum=10,
        super_pacgum=50,
        ghost=200,
        ghost_speed=0.0,
        frightened_speed=0.0,
        respawn_delay=0.3,
    )
    state: GameState = empty_state
    for ghost in state.ghosts:
        ghost.mode = EntityMode.EATEN
        ghost.mode_timer = 5.0
    ghost = state.ghosts[0]
    ghost.mode_timer = 0.3
    run_for(state, quick, Random(12), 0.5)
    assert ghost.mode is EntityMode.NORMAL
    assert ghost.cell == ghost.home
    assert ghost.direction is None


def test_eaten_ghost_rejoins_fright(
    empty_state: GameState,
) -> None:
    """Respawning mid-fright returns a FRIGHTENED ghost.

    Otherwise one ghost would hunt while its three siblings are
    still edible, which reads as unfair on screen.
    """
    quick = GameSettings(
        pacgum=10,
        super_pacgum=50,
        ghost=200,
        ghost_speed=0.0,
        frightened_speed=0.0,
        fright_duration=5.0,
        respawn_delay=0.3,
    )
    state: GameState = empty_state
    state.super_pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, quick, Random(15), 1.5 * ONE_CELL)
    assert GameEvent.FRIGHT_STARTED in events
    assert state.frightened_remaining > 0.0
    ghost = state.ghosts[0]
    ghost.mode = EntityMode.EATEN
    ghost.mode_timer = 0.3
    run_for(state, quick, Random(15), 0.5)
    assert ghost.mode is EntityMode.FRIGHTENED
    assert ghost.cell == ghost.home


def test_death_cancels_fright_with_event(
    empty_state: GameState,
) -> None:
    """PLAYER_CAUGHT during fright pairs with FRIGHT_ENDED."""
    state: GameState = empty_state
    state.super_pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    run_for(state, QUIET, Random(16), 1.5 * ONE_CELL)
    assert state.frightened_remaining > 0.0
    for ghost in state.ghosts:
        ghost.mode = EntityMode.NORMAL
    ghost = state.ghosts[0]
    ghost.cell = state.player.cell
    ghost.prev_cell = state.player.cell
    ghost.progress = 0.0
    ghost.direction = None
    events = tick(state, QUIET, Random(16), 0.05)
    assert GameEvent.PLAYER_CAUGHT in events
    assert GameEvent.FRIGHT_ENDED in events
    assert state.frightened_remaining == 0.0
    assert all(
        peer.mode is EntityMode.NORMAL
        for peer in state.ghosts
    )


def test_ai_ignores_rng_mid_transition(
    empty_state: GameState,
) -> None:
    """A tick with no cell entry consumes no random numbers."""
    state: GameState = empty_state
    for ghost in state.ghosts:
        ghost.prev_cell = ghost.cell
        ghost.progress = 0.5
        ghost.direction = Direction.RIGHT
        ghost.next_direction = Direction.RIGHT
    state.player.direction = Direction.RIGHT
    state.player.next_direction = Direction.RIGHT
    state.player.progress = 0.5
    rng = Random(17)
    before = rng.getstate()
    tick(state, SETTINGS, rng, 0.01)
    assert rng.getstate() == before


def test_rng_use_is_frame_rate_independent(
    empty_state: GameState,
) -> None:
    """60 FPS and 30 FPS runs consume the same random draws.

    Ghost cells themselves may diverge: the AI samples the
    player's discrete cell at its own crossings, and those
    crossings land differently under different step sizes. What
    the fixed-step contract promises is only that the draw count
    does not depend on the frame rate.
    """
    _ = empty_state

    def fresh() -> GameState:
        maze = normalize(make_maze(open_grid(5, 5)))
        layout = gen_layout(maze, 0, Random(7))
        fresh_state = new_game_state(maze, layout)
        fresh_state.pacgums.clear()
        fresh_state.super_pacgums.clear()
        set_direction(fresh_state, Direction.RIGHT)
        return fresh_state

    fast = fresh()
    fast_rng = Random(18)
    for _ in range(120):
        tick(fast, SETTINGS, fast_rng, 1.0 / 60.0)
    slow = fresh()
    slow_rng = Random(18)
    for _ in range(60):
        tick(slow, SETTINGS, slow_rng, 1.0 / 30.0)
    assert fast_rng.getstate() == slow_rng.getstate()


def test_eaten_ghost_skips_fright(
    empty_state: GameState,
) -> None:
    """A super eaten during EATEN leaves that ghost EATEN."""
    state: GameState = empty_state
    ghost = state.ghosts[0]
    ghost.mode = EntityMode.EATEN
    ghost.mode_timer = 5.0
    state.super_pacgums = {Cell(3, 2)}
    set_direction(state, Direction.RIGHT)
    events = run_for(state, QUIET, Random(13), 1.5 * ONE_CELL)
    assert GameEvent.FRIGHT_STARTED in events
    assert ghost.mode is EntityMode.EATEN


def test_ghosts_do_not_clump(empty_state: GameState) -> None:
    """Early in a chase the four ghosts share more than one cell.

    Kept to one second on purpose: a longer run lets the player
    die and the ghosts reset to corners, which would pass without
    testing the chase spread at all.
    """
    state: GameState = empty_state
    set_direction(state, Direction.RIGHT)
    run_for(state, SETTINGS, Random(14), 1.0)
    assert len({ghost.cell for ghost in state.ghosts}) > 1
