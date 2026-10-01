# Blocking Points and Conflicts

Honest record: no blocking conflict occurred. Points that cost time:

1. **Ghost color flashing (29.09).** Renderer assumed two sheet rows per
   ghost color; pixel audit showed one row × 4 phases. Fixed same day by
   regenerating `assets/gen/` (37 frames) — no logic change.
2. **Pac-Man direction art missing.** The sheet ships right-facing mouths
   only (verified per-pixel). Stop-gap: neutral closed mouth off-axis;
   contract documents the `pm_left/up/down_*` filenames for later art.
3. **TileSet unusable for thin walls (verified by scan).** The assigned art
   kit has no tileable thin-wall set for generated mazes, so walls stayed
   vector in sheet palette + neon rim on blocks. No requirement broken
   (subject is silent on wall style).
4. **Makefile merge conflict.** Resolved; `make lint` (flake8 + mypy flags
   verbatim) is green.
5. **Speed tuning (8→5 cells/s).** Playtest-driven, recorded as matrix open
   point #2 pending A's sign-off.
6. **Turnaround latency.** D1 literal reading cost up to a full cell;
   instant-reverse exception added to `movement.py`, owner to review.

Interpersonal conflicts: none.
