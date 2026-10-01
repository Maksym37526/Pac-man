# Acceptance Test Plan

How each MUST was verified. Unit level: `pytest tests/` (161 tests).
System level: scripted headless runs + live playthrough before freeze.

## Playthrough script (must pass twice: win path via skips, lose path)

1. `python3 pac-man.py config.json` opens the main menu, no traceback.
2. Start Game → maze renders, HUD shows score/lives/level/time.
3. Eat pacgums (score grows), super-pacgum (ghosts edible, blink at end),
   edible ghost (+points, respawns at corner).
4. Ghost touch → life lost, respawn center; 3rd death → Game Over screen.
5. Name entry accepts ASCII ≤10, saves; entry appears in Highscores + menu top-3.
6. Pause (P/Esc) freezes timer and animation; resume continues; Esc abandons.
7. Cheats 1–7: master gate, invincible, fast, skip/clear level, fright,
   lose life; cheated run shows the warning and is not saved.
8. T cycles 10 themes, G toggles ghost party + disco walls.
9. Faulty configs (missing keys, junk, `[]` levels) → clamp + log, no traceback.
10. Fresh clone + `make install/run/lint` green.

## Bugs found and fixed

| Bug | Fix |
|---|---|
| Ghosts passed through the player | collision radius/swap check, rules loop |
| Score not saved after game end | capture name before buffer clear → `confirmed_name` flag |
| Second run reused dead session (ghosts harmless) | fresh `Session` on every START |
| Cyrillic names silently became PLAYER | ASCII-only filter at entry screen |
| Highscore screen text overlap | spacing derived from `font_size` |
| Ghosts flashed other colors | one sheet row per color, 4 phases |
| Pac-Man always faced right / chewed air | chomp only while moving; directional sets stubbed |
| Death shake leaked into the new run | `reset_fx()` on START |
| P dead on RU layout | JCUKEN homologs in key map |
| Turnaround waited a full cell | instant 180° reversal in `advance()` |
| Pygame API outside facade (`get_width`) | removed, exact-size blits (D2) |
| Wall-clock animation ran during pause | game-clock `advance()` |
| Sprite fallback ignored super size/color | distinct fallback |
| `assert`s vanish under `python -O` | explicit `TypeError` |
| Stale `view_state` duplicates of core fields | single source through `core` |
| Makefile merge conflict | resolved |
