"""Frame pacing for the main loop.

pygame.time.Clock is outside the approved primitives (no MLX
equivalent, see graphics_library.md), so pacing uses time.monotonic
and time.sleep from the standard library.
"""

import time

from pacman.core.movement import MAX_DT

TARGET_FPS = 60


class FrameLimiter:
    """Sleeps out the rest of each frame and reports the frame's true dt."""

    def __init__(self, fps: int = TARGET_FPS) -> None:
        """Set the target frame rate.

        Args:
            fps: Frames per second to hold, at least 1.

        Raises:
            ValueError: If fps is below 1.
        """
        if fps < 1:
            raise ValueError(f"fps {fps} must be >= 1")
        self._period = 1.0 / fps
        self._last = time.monotonic()

    def wait(self) -> float:
        """Sleep until the frame period has passed, then return its dt.

        Call once at the top of every loop iteration. The returned dt
        is clamped to MAX_DT, so it can go straight into tick() and
        renderer.advance(): a hitch (drag, breakpoint) never eats the
        level timer beyond one clamped step.

        Returns:
            Clamped seconds since the previous call.
        """
        remaining = self._period - (time.monotonic() - self._last)
        if remaining > 0.0:
            time.sleep(remaining)
        now = time.monotonic()
        dt = now - self._last
        self._last = now
        return min(dt, MAX_DT)
