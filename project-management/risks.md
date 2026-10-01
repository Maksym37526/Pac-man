# Risk Register

| # | Risk | Impact | Mitigation | Status |
|---|---|---|---|---|
| R1 | Assigned maze package misbehaves (raw exceptions, reseeds `random`, logo blocks) | Crash / unfair levels | Adapter shield (`MazeError`), own `Random` instances, flood-fill check, nearest-walkable centre | CLOSED — adversarial suite green |
| R2 | Config replaced during defense (V.3) | Crash on stage | Clamp-to-default + log + continue, ≥15 adversarial configs, never uniform level sizes assumed (D3) | CLOSED, re-verified before freeze |
| R3 | MLX-equivalence challenge at review | Fail on graphics rule | Facade-only pygame, mapping table in `graphics_library.md`, no `draw/transform/sprite/mixer` anywhere | CLOSED — grep-verifiable |
| R4 | Highscore file corrupt/missing at review | Lost table / crash | Degrade to empty table, per-record drop, atomic writes | CLOSED |
| R5 | Review machine without assets/network | Black squares / pip fail | `assets/gen/` committed, vendor wheel vendored, fonts fall back gracefully | CLOSED |
| R6 | Scope creep (faithful arcade clone) | Missed MUSTs | Traceability matrix rule: no row → not built | CLOSED — matrix is the gate |
| R7 | Single-editor conflicts in shared docs | Lost work | One owner per file, contracts change only jointly | OPEN — mitigated, watch at freeze |
