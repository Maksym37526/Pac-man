*This project has been created as part of the 42 curriculum by myaroshu, ilobov.*

# Pac-Man — Ghosts! More ghosts!

## Description

A complete, playable Pac-Man clone in Python: procedurally generated mazes,
4 ghosts with chase/flee AI, power pellets, 10 levels with a timer, persistent
top-10 highscores, a cheat mode for reviewers, and a polished pygame UI
(main menu, HUD, pause, game-over/victory, name entry). Ships as an
unlisted free build on itch.io.

## Instructions

Requirements: Python 3.10+.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
python3 pac-man.py config.json
```

Or via Make: `make install`, `make run`, `make lint` (flake8 + mypy with the
subject flags), `make debug`, `make clean`.

Controls: arrows/WASD to move (Cyrillic layout works too), P/Esc pauses,
Enter/Space confirms, Esc goes back. Cheats: `1` master switch (required
first), `2` invincible, `3` double speed, `4` skip level, `5` clear level,
`6` fright now, `7` lose a life, `8` freeze ghosts, `9` extra life. Fun:
`T` cycles 10 color themes, `G` toggles ghost party (color shuffle +
disco walls).

## Resources

- Pac-Man dossier (pacman dossier by J. Pittman) — ghost AI personalities
  and maze logic of the 1980 original.
- MiniLibX / MLX42 documentation — the primitive set our graphics subset
  maps onto (see `project-management/graphics_library.md`).
- pygame-ce documentation (SDL2 backend) — surfaces, fonts, event queue.
- `mazegenerator` 2.1.0 package docs + our notes in
  `project-management/maze-package.md`.

How AI was used: an AI coding assistant acted as a pair programmer for role
B (presentation/interaction) — debugging (ghost collisions, highscore save
flow, sprite slicing), drafting repetitive code (theme palettes, screens),
systematic audits (MLX-equivalence sweep, edge-case review of `render/` and
`ui/`), and drafting docs (this README, PM records). Every suggestion was
read, tested headless or in-game, and lint-checked before commit; all
design decisions (ASCII names, JSON scores, greedy chase, tile-64 sprites)
were taken by the team and recorded in the matrix.

## Configuration

`python3 pac-man.py <file.json>`. Lines starting with `#` (plus `//` and
`/* */`) are comments. Missing/invalid values clamp to defaults with a log
line; unknown keys are ignored; the game never prints a traceback.

| Key | Default | Range | Notes |
|---|---|---|---|
| `highscore_filename` | `highscore.json` | any path | created on first save |
| `lives` | `3` | 1–9 | per run |
| `points_per_pacgum` | `10` | 0–10000 | |
| `points_per_super_pacgum` | `50` | 0–10000 | also starts fright |
| `points_per_ghost` | `200` | 0–10000 | edible ghost |
| `seed` | `42` | 1–999999999 | level 1 is fixed from it |
| `levels` | `[]` (→ 10 defaults) | list | per-level below |
| `levels[].width` | `21` | 15–51, odd | even is rounded down |
| `levels[].height` | `21` | 11–51 | |
| `levels[].pacgum` | `42` | 0–1000 | clamped to free cells |
| `levels[].level_max_time` | `90` | 1–600 s | timeout costs one life |

## Highscore

Top 10 `(name, score)` rows in a human-readable, diffable JSON file.
Names: ASCII letters/digits/spaces, 1–10 chars — anything else is fixed,
not rejected (trimmed, cut, blank → `PLAYER`), so the victory screen never
blocks on a name. Scores: non-negative ints. Loading tolerates any file
state (missing → empty table, corrupt rows dropped individually); saving is
atomic (temp file + `os.replace`), never raising into the game. Cheated
runs show the name screen but are never stored (`cheats_used` never lowers).
JSON over pickle deliberately: a tampered score file must not become code
execution.

## Maze Generation

We must not write our own generator: mazes come from the assigned
`mazegenerator` 2.1.0 package, used as-is (vendored wheel, reinstalled at
review). Our adapter (`pacman/maze/adapter.py`) is the only module importing
it: `PERFECT=False` for Pac-Man-compatible corridors, dimensions read back
from the returned grid (never trusted), walls decoded from bit flags,
connectivity verified by flood fill, the center logo blocks worked around
(nearest walkable centre, guaranteed walkable corners). Level 1 derives
from the config seed; later levels draw fresh seeds from the run RNG (our
own `Random` instances — the package reseeds global `random`). Generator
failures surface as `MazeError` with a message, never a traceback.

## Implementation

- Movement is discrete (cell/prev-cell/progress, D1): logic commits per
  cell, the renderer interpolates — collisions become exact, input applies
  at boundaries, 180° reversals are instant.
- `tick()` order is load-bearing: timer → fright → eaten-ghost timers →
  player move/eat → ghost AI (greedy Manhattan + per-ghost randomness) →
  collisions (one life per tick max) → victory check.
- `Session` owns the run: levels, score/lives carry-over, timer, cheats
  (`apply_cheat` reuses the same paths as honest play, no second
  implementation). Cheated runs are flagged, never stored.
- Rendering is pygame-ce through a thin facade restricted to the
  MLX-equivalent subset (full mapping table in `graphics_library.md`).
  Sprites are pre-sliced/upscaled offline (`assets/upscale.py`) and blitted
  1:1 — no runtime scaling. Walls use sheet palette + neon rim; 10 runtime
  color themes; party mode, confetti, screen shake and score popups run on
  the game clock (frozen by pause).
- Playtest tuning: 5.0/4.5/3.0 cells/s (player/ghost/frightened).

## General Software Architecture

```
pac-man.py          entry point: parse → validate → run loop
pacman/game.py      composition layer: the ONLY module importing core+data
pacman/core/        entities, movement, ghost AI, rules, session, cheats
pacman/maze/        vendor adapter, normalisation, layout (dots/corners)
pacman/data/        config pipeline (spec → validate → build), highscores
pacman/render/     facade (sole pygame importer), renderer, layout, theme
pacman/ui/         input translation, state machine, screens payloads
```

Data flows one way: `Config → GameSettings/LevelSpec → Session → tick() →
RenderGameState → Renderer`. The renderer never mutates game state; `core`
never imports `render`, `ui` or `data`, so the game runs headless (161+
tests). Full module map and contracts: `project-management/`.

## Project Management

Two roles (A core/systems — myaroshu, B presentation — ilobov), contracts
agreed before code, single-writer files, matrix-gated scope (no row → not
built). Timeline, risks, team rules, acceptance plan and blocking points:
[`project-management/`](project-management/).
