# Module Interface Contracts

Agreed before any implementation work. These are the shapes of the data that
cross the boundary between the two workstreams. They are contracts, not
implementations: nothing here says *how* a value is produced, only what it is
and who may touch it.

**Change protocol.** Anything in this document changes only by joint agreement,
in its own commit, announced to the other partner immediately. A one-sided
change to a contract is the single most common cause of wasted work in a paired
project.

## Ownership

| Owner | Scope |
|---|---|
| **A** — Core / Systems | config, maze adapter, entities, movement, ghost behaviour, game rules, timer, highscores, packaging |
| **B** — Presentation / Interaction | graphics facade, renderer, input, screens, application state machine, HUD, assets |

**Dependency rule:** `pacman/core` must not import anything from `pacman/render`
or `pacman/ui`. Verified by review and by the fact that the game must be able to
run headless (REQ-022).

---

## 0. Foundational decisions

Three decisions that everything below depends on.

### D1 — Movement model: continuous position, discrete events

A moving entity holds a current cell, a previous cell, a direction, and a
progress value from 0.0 to 1.0 describing how far it has travelled between the
two. Logic advances progress; when it reaches 1.0 the entity commits to the new
cell.

**Every game event fires at commit time**, never mid-transition: eating a
pacgum, colliding with a ghost, choosing the next direction, checking whether
the level is complete.

Rationale: collisions and pickups become exact integer comparisons instead of
distance thresholds, ghost decisions happen once per cell instead of once per
frame, and the renderer gets smooth motion for free by interpolating between
the two cells using progress.

### D2 — Tile size is a global constant

Sprites are PNG files authored at exactly the tile size. Scaling is unavailable
(see `graphics-library.md`), so tile size can never change at runtime.

### D3 — Maze size varies per level; the window does not

Each level carries its own width and height from the config. The window is
sized once at startup from the largest level in the config. Smaller mazes are
centred, leaving a margin.

Rationale: the configuration is replaced during the defense (subject V.3), so
assuming uniform level sizes is a crash waiting to happen.

---

## 1. Coordinate systems

Three of them. Confusing them is the most common source of bugs in this kind of
project, so the names are fixed here and used everywhere.

| Name | Type | Meaning |
|---|---|---|
| **Cell** | `(col, row)`, both `int` | index into the maze grid. `col` is horizontal, `row` is vertical |
| **World** | `(x, y)`, both `float` | continuous position in cell units; a value of `(3.5, 2.0)` means halfway between cells `(3,2)` and `(4,2)` |
| **Screen** | `(px, py)`, both `int` | pixels in the window, including tile size and the centring offset |

Conversion between them belongs to B and lives in the renderer. `core` never
computes screen coordinates and never sees them.

> Note the ordering trap: the maze grid returned by the assigned package is
> indexed `maze[row][col]`, i.e. row first. Our `Cell` is `(col, row)`, i.e.
> column first, matching `(x, y)` intuition. The adapter is the only place where
> both orders appear, and it is responsible for getting it right.

---

## 2. Contract: `Maze`

Produced by the maze adapter (A), consumed by game rules (A) and the renderer
(B). Immutable for the lifetime of a level.

| Field / query | Type | Meaning |
|---|---|---|
| `width` | `int` | number of columns, read from the returned grid, never from the requested size |
| `height` | `int` | number of rows |
| `is_wall_between(cell, direction)` | `bool` | whether movement from `cell` in `direction` is blocked |
| `is_blocked(cell)` | `bool` | whether the cell itself is a solid block (the package's "42" logo cells) |
| `walkable_neighbours(cell)` | list of `(direction, cell)` | every direction from `cell` that is not blocked |
| `centre` | `Cell` | the player start cell; guaranteed walkable |
| `corners` | tuple of 4 `Cell` | top-left, top-right, bottom-left, bottom-right; guaranteed walkable |
| `walkable_cells` | set of `Cell` | every cell that is not a solid block |

### Invariants the adapter guarantees

The rest of the game relies on these and does not re-check them.

1. `width` and `height` are read from the actual returned grid.
2. Every cell in `walkable_cells` is reachable from `centre`, verified by flood
   fill.
3. `centre` is walkable. If the geometric centre is a solid block, the nearest
   walkable cell is used instead.
4. All four entries of `corners` are walkable.
5. Wall data is symmetric: if there is a wall east of cell X, there is a wall
   west of its eastern neighbour.

### Failure

If the generator raises, returns an unusable grid, or an invariant cannot be
satisfied, the adapter raises a single project-specific error carrying a
human-readable message. It never lets a raw `IndexError` or `TypeError` from the
package escape (see PKG-5 in the requirements matrix).

---

## 3. Contract: `Config`

Produced by the config loader (A) after parsing, validation and clamping.
Immutable. The raw parsed dictionary never travels beyond the loader.

### Top level

| Field | Type | Default | Notes |
|---|---|---|---|
| `highscore_filename` | `str` | project default | REQ-040 |
| `levels` | list of `LevelConfig` | 10 generated defaults | at least 10 entries; padded if the config supplies fewer (REQ-102) |
| `lives` | `int` | 3 | REQ-043 |
| `points_per_pacgum` | `int` | 10 | REQ-045 |
| `points_per_super_pacgum` | `int` | 50 | REQ-046 |
| `points_per_ghost` | `int` | 200 | REQ-047 |
| `seed` | `int` | 42 | clamped to >= 1, see PKG-1 |

### Per level (`LevelConfig`)

| Field | Type | Default | Notes |
|---|---|---|---|
| `width` | `int` | 21 | clamped to odd and >= 15, see PKG-2 and PKG-3 |
| `height` | `int` | 21 | clamped to >= 11, see PKG-3 |
| `pacgum` | `int` | 42 | clamped to the number of available walkable cells |
| `level_max_time` | `int` | 90 | seconds, REQ-049 |

### Validation rules

- Every key has a declared type, default, minimum and maximum, held as **data**
  in a specification table, not as scattered conditionals.
- A missing or invalid value is clamped to a safe default, a clear message is
  logged, and execution continues (REQ-050, REQ-051).
- Unknown keys are ignored without comment (REQ-052).
- No input produces a traceback (REQ-053).
- The README configuration section is written from the same specification table,
  so documentation cannot drift from behaviour (REQ-146).

---

## 4. Contract: `GameState`

The single object the renderer reads. **The renderer never mutates it.**
GameState itself is mutable (it changes ~60 times a second), but only
`core/rules.py` writes to it. This is the seam between A and B, and the
reason the game can run headless.

| Field | Type | Meaning |
|---|---|---|
| `maze` | `Maze` | current level's maze |
| `player` | `Entity` | see below |
| `ghosts` | list of `Entity` | exactly 4 |
| `pacgums` | set of `Cell` | remaining ordinary pacgums |
| `super_pacgums` | set of `Cell` | remaining power pellets |
| `score` | `int` | never decreases (REQ-101) |
| `lives` | `int` | remaining lives |
| `level_index` | `int` | 0-based; the HUD displays `level_index + 1` |
| `level_count` | `int` | total number of levels |
| `time_remaining` | `float` | seconds left on this level, pause-compensated |
| `frightened_remaining` | `float` | seconds left of the edible state; `0.0` when inactive |
| `cheats` | `CheatState` | which cheats are currently active, for the HUD indicator |

Phase 5 implements `maze`, `player`, `pacgums`, `super_pacgums`
and `score`; Phase 6 adds `ghosts`, `lives` and
`frightened_remaining`; Phase 7 adds `time_remaining`,
`level_index` and `level_count`; `cheats` arrives later
(Phase 10).

### `Entity`

| Field | Type | Meaning |
|---|---|---|
| `cell` | `Cell` | the cell being moved into |
| `prev_cell` | `Cell` | the cell being moved out of |
| `progress` | `float` | 0.0 to 1.0 along the transition, per D1 |
| `direction` | `Direction \| None` | current direction of travel; `None` means standing (B must handle it, e.g. keep the last sprite orientation) |
| `next_direction` | `Direction \| None` | desired turn at the next cell boundary; filled by keyboard for the player, by AI for ghosts |
| `kind` | `EntityKind` | `PLAYER` or one of the four ghost identities |
| `home` | `Cell` | respawn cell: centre for the player, own corner per ghost |
| `mode` | `EntityMode` | `NORMAL`, `FRIGHTENED`, `EATEN` |
| `mode_timer` | `float` | seconds left in the mode; used only for `EATEN` |

`RESPAWNING` was removed from the enum in Phase 6: an eaten ghost
waits out its timer in `EATEN` and teleports home, so no fourth
state is needed. Speed is not a field of the entity: it is computed
in `rules.py` from `GameSettings` plus the current state (fright,
cheats) and passed into the movement function.

The renderer computes the world position by interpolating between `prev_cell`
and `cell` using `progress`, then converts to screen coordinates. The exact
formula lives in `core/collision.py` (`world_position`): B reuses it instead
of writing a second copy.

### Enumerations

| Enum | Members |
|---|---|
| `Direction` | `UP`, `DOWN`, `LEFT`, `RIGHT` |
| `EntityKind` | `PLAYER`, `GHOST_1`, `GHOST_2`, `GHOST_3`, `GHOST_4` |
| `EntityMode` | `NORMAL`, `FRIGHTENED`, `EATEN` |
| `AppState` | `MAIN_MENU`, `INSTRUCTIONS`, `HIGHSCORES`, `PLAYING`, `PAUSED`, `GAME_OVER`, `VICTORY`, `NAME_ENTRY`, `EXIT` |

`AppState` is taken directly from subject IV and VI.8. No states beyond these.

### `GameEvent`

Returned by `tick()` alongside the mutated state; B reads these for
the HUD. Phases 6 and 7 extend the enum, they never reinterpret it.

| Event | Fires when |
|---|---|
| `PACGUM_EATEN` | the player enters a cell holding an ordinary pacgum |
| `SUPER_PACGUM_EATEN` | the player enters a cell holding a super-pacgum |
| `LEVEL_CLEARED` | the tick that eats the last remaining dot (ordinary and super sets both empty); exactly once, never repeated on later ticks |
| `GHOST_EATEN` | the player touches a `FRIGHTENED` ghost: +Z, ghost becomes `EATEN` |
| `PLAYER_CAUGHT` | the player touches a `NORMAL` ghost: −1 life, player and ghosts respawn at home |
| `GAME_OVER` | the tick that takes the last life (by catch or by time-up); the session is finished, later ticks emit nothing |
| `FRIGHT_STARTED` | a super-pacgum turns every `NORMAL` ghost `FRIGHTENED` (timer resets, never stacks) |
| `FRIGHT_ENDED` | the fright timer crosses zero, or death cancels an active fright; exactly once per fright — paired events are always paired, including cancellation paths |
| `TIME_UP` | the level timer crosses zero; fires once, on the crossing tick only, with no movement or eating in that tick |
| `GAME_WON` | the cleared level is the last one in the run; the session is finished, later ticks emit nothing |

### `GameSettings`

Frozen tuning built outside `core` from `Config`, replacing the
Phase 5 `ScoringRules`. `tick(state, settings, rng, dt)` takes it
plus a `Random` passed separately (a generator is a consumed
dependency, not a setting). Fields: three point values, three
speeds (`player_speed` 8.0, `ghost_speed` 7.0 — slower so the game
stays winnable, `frightened_speed` 4.0 — slower so ghosts stay
catchable), `fright_duration`, `respawn_delay` (both 7.0 s),
`collision_radius` (0.5 cells) and per-ghost `ghost_randomness`
`(0.0, 0.1, 0.2, 0.3)` — the REQ-091 decision below.

Note for B: `FRIGHTENED` and `EATEN` need distinct sprites (VI.3:
the player must see who is edible), and `frightened_remaining` is
available for the end-of-fright blink.

### `Session` (Phase 7)

One full run through every level. The renderer keeps reading a
single `GameState` (`session.level`); nothing about `draw_game`
changes. What changes is who B drives and where run-wide data
lives.

| Field | Type | Meaning |
|---|---|---|
| `level` | `GameState` | current level's state; replaced wholesale on every transition |
| `settings` | `GameSettings` | static tuning, shared by all levels |
| `rng` | `Random` | the run's random source, shared by all levels |
| `levels` | tuple of `LevelSpec` | every level's shape, in play order; core's own record (`width`, `height`, `pacgums`, `level_max_time`), translated from `LevelConfig` by the composition layer |
| `config_seed` | `int` | top-level seed, deciding each maze |
| `finished` | `bool` | true after `GAME_OVER` or `GAME_WON`; ticks on a finished session return `[]` |
| `won` | `bool` | true only after `GAME_WON` |

Decision A (why it looks like this): `score` and `lives` stay
in `GameState`, so `rules.tick(state, settings, rng, dt)` keeps
its signature and every Phase 5/6 test keeps working. On a
transition the session copies exactly those two fields into the
fresh state; dedicated tests guard the copy. The alternative —
moving them into `Session` — would have rewritten the tick
signature and the whole core test suite for no behavioural gain.

Boundary change for B: drive `session.tick(dt)`, not
`rules.tick(...)`. `session.tick` calls `rules.tick` for the
current level, then handles `TIME_UP` (lose a life, respawn at
home via the shared `respawn_after_catch`, reset the timer to
full, pacgums stay eaten; `GAME_OVER` on the last life),
`LEVEL_CLEARED` (next level, or `GAME_WON` on the last one) and
`GAME_OVER` (mark finished). Input goes through
`session.set_direction(direction)` — same `Direction`, same
meaning as `rules.set_direction`, B never touches the inner
state object directly.

Pause contract (REQ-109): core owns no clock. `tick` consumes
only the `dt` it is given, and the level timer subtracts that
same clamped `dt` (never the raw frame time, so lag cannot eat
the timer). B pauses by not calling `tick`; calling `tick`
with a real `dt` while "paused" would keep the game running.
`tick(dt=0)` is a safe no-op.

Time-up decision (REQ-104): time-up costs one life and restarts
the timer, it does not end the game immediately. Rationale: it
reuses the exact ghost-death punishment (one life, everybody
home, fright cancelled), and 90 s comfortably fits a level
(~23 s for 42 pacgums at speed 8), so the limit punishes
stalling without making the game unwinnable.

---

## 5. Contract: `InputEvent`

B translates raw key events into these; A never sees a key code.

| Event | Bound to | Used in |
|---|---|---|
| `MOVE_UP` / `MOVE_DOWN` / `MOVE_LEFT` / `MOVE_RIGHT` | arrows and WASD (REQ-079) | gameplay, menu navigation |
| `CONFIRM` | Enter / Space | menus, name entry |
| `BACK` | Escape | leave a screen |
| `PAUSE` | Escape or P during gameplay | REQ-108 |
| `QUIT` | window close button | REQ-115 |
| `TEXT_CHAR` | a printable character | name entry only; carries the character |
| `TEXT_BACKSPACE` | Backspace | name entry only |
| `CHEAT_*` | dedicated keys | one event per cheat, list finalised with REQ-098 |

Movement events carry intent, not state. A stores the most recent one as the
desired direction and applies it at the next commit point, per D1.

Boundary: `core` accepts movement as a `Direction` via
`set_direction()`, never as an `InputEvent` — `InputEvent` lives in
`ui/`, which `core` must not import. The composition layer translates
`MOVE_*` into `Direction` and calls `set_direction()`.

---

## 6. Contract: `Renderer`

Implemented by B, called by the main loop. Every method is read-only with
respect to game data.

| Operation | Input | Notes |
|---|---|---|
| `prepare_level(maze)` | `Maze` | called once per level; renders the static maze into a cached background buffer |
| `draw_game(state)` | `GameState` | blits the cached background, then the dynamic entities and the HUD |
| `draw_screen(app_state, payload)` | `AppState` plus screen-specific data | menus, highscore list, instructions, game over, victory, name entry |
| `present()` | — | pushes the completed frame to the window |

`prepare_level` exists because of the graphics restriction: maze walls are drawn
pixel by pixel, which is expensive, and the maze does not change during a level.

---

## 7. Module map

```
pacman/
├── log.py    A   logging setup, shared by every package
├── errors.py A   project-specific exception hierarchy, shared by every package
├── game.py   A   composition layer: the only module importing both core/ and data/
├── core/     A   entities, movement, ghost behaviour, rules, scoring, timer, session
├── maze/     A   adapter to mazegenerator, normalisation, invariant checks
├── data/     A   config loading and validation, highscore persistence
├── render/   B   graphics facade, renderer, sprite loading
└── ui/       B   application state machine, screens, input translation
```
`log.py` and `errors.py` are leaf modules: they sit at the root of the package
because every other package needs them, and they import nothing from the project
themselves. A leaf module cannot take part in an import cycle by construction.

The persistence package is named `data`, not `io`: `io` is a standard library
module name, and shadowing it in the project tree causes confusion when reading
imports, even though Python 3's absolute imports make it technically safe. The
same reasoning applies to `log.py` rather than `logging.py`.

| Rule | Reason |
|---|---|
| `log.py` imports nothing from the project | leaf module: everything may depend on it, it depends on nothing |
| `errors.py` imports nothing from the project | leaf module, same reason; importing it must never create a cycle |
| `core` imports nothing from `render` or `ui` | headless execution, REQ-022 |
| `core` imports nothing from `data` | config is plain data; `pacman/game.py` translates `Config` into `GameSettings`/`LevelSpec` |
| `data/` imports nothing from `core` | config and highscores are plain data |
| only `pacman/game.py` imports both `core` and `data` | single composition point, no scattered glue |
| Only `maze/` imports `mazegenerator` | REQ-058; the adapter is the only place that knows the package |
| Only the graphics facade in `render/` imports pygame | the facade rule in `graphics-library.md` |

---

## 8. Work split enabled by these contracts

Once this document is agreed, both workstreams can proceed without blocking.

| A works on | B works on |
|---|---|
| config loader against the `Config` contract | graphics facade and main loop |
| maze adapter against the `Maze` contract | renderer against the `Maze` and `GameState` contracts |
| entities and rules producing `GameState` | screens against the `AppState` contract |
| highscore persistence | input translation producing `InputEvent` |

B is not blocked waiting for A: a hand-written fake `Maze` and a hand-written
fake `GameState` are enough to build and test the entire renderer. Building
those two fakes is the first task on B's list.

---

## 9. Contract: exception hierarchy

All project-specific exceptions live in `pacman/errors.py` and derive from a
single root, so that any layer can catch "everything our code raises" with one
`except` while still letting genuine programming errors propagate.

| Exception | Raised when | Caught where |
|---|---|---|
| `PacmanError` | never raised directly; the common root | the boundary handler in `pac-man.py` |
| `ConfigError` | the configuration cannot be read or parsed at all | the boundary handler |
| `MazeError` | the generator fails or a maze invariant cannot be satisfied | the boundary handler |
| `HighscoreError` | highscores cannot be persisted | locally, degrade and continue |

### Rules

1. Errors from third-party code never escape their module. The maze adapter
   catches whatever `mazegenerator` raises and re-raises `MazeError` with a
   readable message (see PKG-5).
2. Exceptions are caught at the boundary — in the entry point — not scattered
   across the codebase. The boundary handler prints the message and returns a
   non-zero exit code. This is what guarantees REQ-034: a clear message, never
   a traceback.
3. Invalid configuration *values* do not raise. They are clamped and logged per
   subject V.3. `ConfigError` is reserved for cases where there is nothing to
   clamp: the file is missing, unreadable, or not JSON at all.
4. `HighscoreError` is the exception to rule 2. Failing to save a score must not
   end the game, so it is handled where it occurs: log a warning and continue
   (REQ-064).

---

## 10. Randomness

The assigned generator calls `random.seed()` on the global `random` module
(PKG-4), which resets any global randomness the game relies on. Generating a
level would therefore silently reshuffle anything else that used the global
module.

The game consequently uses its own `Random` instances and never the module-level
functions. One instance is created per run and passed explicitly to everything
that needs randomness: pacgum placement, and the seed of every level after the
first. Tests pass a seeded instance, so a whole run is reproducible from a single
point.

Ghost AI draws from that instance only when a ghost enters a new cell
(or stands still), never once per frame: the number of draws depends on
intersections crossed, not on the frame rate (pinned by
`test_rng_use_is_frame_rate_independent`).

Reproducibility holds for a fixed logic timestep. Ghosts sample the
player's cell at the moment they reach an intersection, so changing
the step size changes which cell they see. The main loop therefore
drives tick at a constant dt, as D1 requires; the frame rate may
vary, the logic step may not.

---
## 11. Open points

Recorded here so they are not silently decided by whoever writes the code first.

| # | Question | Depends on |
|---|---|---|
| 1 | Exact tile size in pixels, and therefore sprite dimensions | D2, asset authoring |
| 2 | Player and ghost movement speed, in cells per second | player 8.0, ghost 7.0, frightened 4.0 (`GameSettings`), pending playtesting |
| 3 | Duration of the frightened state | provisionally 7.0 s (`GameSettings.fright_duration`), pending playtesting |
| 4 | Ghost respawn delay within the 5–10 s range | provisionally 7.0 s (`GameSettings.respawn_delay`), pending playtesting |
| 5 | Ghost chase behaviour | resolved: greedy Manhattan chase with per-ghost randomness, see the REQ-091 decision in the requirements matrix |
| 6 | Behaviour when a level's time limit expires | REQ-104, resolved: time-up costs one life, respawns everybody at home, resets the timer to full; pacgums stay eaten (see the Session contract) |
| 7 | Highscore name rules and storage | resolved in Phase 9, see section 12 |

---

## 12. Contract: highscores

One table shared across runs. A owns the format, the rules and
the file; B owns the two screens (menu list, name entry) that
show it and fill it.

### `HighscoreEntry`

| Field | Type | Meaning |
|---|---|---|
| `name` | `str` | player name, ASCII letters/digits/spaces, 1–10 chars |
| `score` | `int` | non-negative points total of one finished run |

The file holds a JSON list of `{"name", "score"}` objects with
`indent=2` (REQ-063: human-readable, diffable). No dates, no
levels — V.5 asks for names and scores only.

### Name rules (decisions A and B)

Pattern `[A-Za-z0-9 ]{1,10}` matched with `fullmatch`. ASCII,
not Unicode, for two reasons that hold regardless of the font.
First, "alphanumeric" in V.5 most directly reads as ASCII
letters and digits, matching the subject's own example table.
Second, the menu font is chosen by B and not yet fixed:
allowing Unicode now would let names into the saved file that
a Latin-only font cannot draw in the menu (REQ-070).
Widening the pattern later is a one-line change; narrowing it
after scores already exist is not.

`normalise_name` fixes instead of rejecting: strip the edges,
cut to 10 chars, fall back to `"PLAYER"` when empty or still
off-pattern. It never raises and never returns `""`, so B
passes whatever the entry screen collected with no error path.
There is deliberately no separate "is this name acceptable"
check: live feedback during typing belongs to Phase 10 at the
earliest, and V.5 never asks for it.

File rows go the other way: a name that is not already valid
means tampering or corruption, so the record is dropped like
any other corrupt field.

### File behaviour

`load(path)` never raises. A missing file is a normal first
launch (empty table, no warning); an unreadable, non-JSON or
non-list file degrades to an empty table with a warning.
Corrupt records drop individually: three bad rows out of fifty
leave forty-seven. Whatever survives is re-sorted and cut to
ten, because file content is never trusted.

`save(path, entries)` writes atomically (decision D): payload
to a temporary file in the target's own directory (same
filesystem, so the final `os.replace` stays one indivisible
step on POSIX and Windows alike), `flush`, then the rename. A
crash mid-write leaves the previous table untouched. Missing
parent folders are created. Failures are logged and reported
as `False`, never raised — the game continues either way. No
`os.fsync`: flush plus the rename already survive a process
crash; power-loss durability is beyond the subject.

### Who does what, when (REQ-068)

`pacman/game.py` exposes both ends: `load_highscores(config)`
once at startup (the table lives next to the session in
`pac-man.py`, not inside `Session` — it outlives any single
run), `save_score(config, entries, name, score)` after the
player types a name on the Game Over / Victory screen. The
path always comes from `config.highscore_filename` (REQ-040).
B reads the loaded tuple for the menu (REQ-070) and hands the
typed string to `save_score`; it never touches the file
directly.
