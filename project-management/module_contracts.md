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

The single object the renderer reads. **The renderer never mutates it.** This is
the seam between A and B, and the reason the game can run headless.

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

### `Entity`

| Field | Type | Meaning |
|---|---|---|
| `cell` | `Cell` | the cell being moved into |
| `prev_cell` | `Cell` | the cell being moved out of |
| `progress` | `float` | 0.0 to 1.0 along the transition, per D1 |
| `direction` | `Direction` | current direction of travel |
| `kind` | `EntityKind` | `PLAYER` or one of the four ghost identities |
| `mode` | `EntityMode` | `NORMAL`, `FRIGHTENED`, `EATEN`, `RESPAWNING` |

The renderer computes the world position by interpolating between `prev_cell`
and `cell` using `progress`, then converts to screen coordinates. It needs
nothing else.

### Enumerations

| Enum | Members |
|---|---|
| `Direction` | `UP`, `DOWN`, `LEFT`, `RIGHT` |
| `EntityKind` | `PLAYER`, `GHOST_1`, `GHOST_2`, `GHOST_3`, `GHOST_4` |
| `EntityMode` | `NORMAL`, `FRIGHTENED`, `EATEN`, `RESPAWNING` |
| `AppState` | `MAIN_MENU`, `INSTRUCTIONS`, `HIGHSCORES`, `PLAYING`, `PAUSED`, `GAME_OVER`, `VICTORY`, `NAME_ENTRY`, `EXIT` |

`AppState` is taken directly from subject IV and VI.8. No states beyond these.

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
├── core/     A   entities, movement, ghost behaviour, rules, scoring, timer
├── maze/     A   adapter to mazegenerator, normalisation, invariant checks
├── io/       A   config loading and validation, highscore persistence
├── render/   B   graphics facade, renderer, sprite loading
└── ui/       B   application state machine, screens, input translation
```

| Rule | Reason |
|---|---|
| `core` imports nothing from `render` or `ui` | headless execution, REQ-022 |
| Only `maze/` imports `mazegenerator` | REQ-058; the adapter is the only place that knows the package |
| Only the graphics facade in `render/` imports pygame | the facade rule in `graphics-library.md` |
| `io/` imports nothing from `core` | config and highscores are plain data |

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

## 9. Open points

Recorded here so they are not silently decided by whoever writes the code first.

| # | Question | Depends on |
|---|---|---|
| 1 | Exact tile size in pixels, and therefore sprite dimensions | D2, asset authoring |
| 2 | Player and ghost movement speed, in cells per second | playtesting |
| 3 | Duration of the frightened state | playtesting, REQ-087 |
| 4 | Ghost respawn delay within the 5–10 s range | REQ-093 |
| 5 | Ghost chase behaviour | REQ-091, still open in the matrix |
| 6 | Behaviour when a level's time limit expires | REQ-104, still open in the matrix |