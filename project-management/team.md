# Team Organization

| Role | Owner | Scope |
|---|---|---|
| A — Core/Systems | myaroshu | config, maze adapter, entities, movement, ghost AI, rules, timer, highscores, cheats, packaging scripts |
| B — Presentation/Interaction | ilobov | graphics facade, renderer, sprites, input, state machine, screens, HUD, README, PM docs, itch.io build |

Rules actually followed:

- **Contracts first.** Shapes in `module_contracts.md` were agreed before
  implementation; a one-sided contract change is a joint-review item.
- **Dependency rule.** `core/` never imports `render/` or `ui/`; only the
  facade imports pygame. Both are grep-verifiable at any commit.
- **Single-writer files.** `core/*` + `data/*` + `maze/*` = A,
  `render/*` + `ui/*` = B, composition (`pac-man.py`, `game.py`) jointly.
  Cross-border fixes (e.g. instant 180° reversal in `movement.py`) are
  proposed with a repro and reviewed by the owner.
- **No conflicts worth naming.** No overwritten work, no disputed decisions;
  disagreements (speed tuning 8→5 cells/s, wall style) were settled by
  playtest + matrix decision records.
