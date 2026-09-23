"""Graphics facade: the only module that imports pygame.

Every operation here has a documented MLX equivalent (see
project-management/graphics_library.md). No other module in the
project may import pygame directly — checked by grep at review time.
"""
from __future__ import annotations


from dataclasses import dataclass

from pathlib import Path

import pygame

Color = tuple[int, int, int]


class GraphicsFacade:
    """Thin wrapper around pygame, restricted to the MLX-equivalent subset.

    Owns the window and the font used for text. Everything else in
    ``render/`` and ``ui/`` talks to pygame only through this class.
    """

    def __init__(self, width: int, height: int, title: str = "Pac-Man", font_size: int = 32) -> None:
        """Initialise pygame and open the window.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            title: Text shown in the window's title bar.
            font_size: Point size for the text drawn via draw_text.
        """
        pygame.init()
        self._screen: pygame.Surface = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self._font: pygame.font.Font = pygame.font.SysFont(None, font_size)

    def close(self) -> None:
        """Shut down pygame. Safe to call more than once."""
        pygame.quit()

    def new_buffer(self, width: int, height: int) -> pygame.Surface:
        """Create an off-screen image buffer of the given size."""
        return pygame.Surface((width, height))

    def clear(self, buffer: pygame.Surface, color: Color) -> None:
        """Fill an entire buffer with one colour.

        Only ever used to clear a whole surface — never to draw a
        rectangle at an offset, which would exceed the MLX equivalence
        agreed with staff.
        """
        buffer.fill(color)

    def put_pixel(self, buffer: pygame.Surface, x: int, y: int, color: Color) -> None:
        """Write a single pixel into a buffer."""
        buffer.set_at((x, y), color)

    def blit(
        self, source: pygame.Surface, position: tuple[int, int] = (0, 0), dest: pygame.Surface | None = None
    ) -> None:
        """Draw a buffer into another buffer, or into the window if dest is None.

        Args:
            source: The buffer being drawn.
            position: Top-left position in the destination.
            dest: Target buffer. Defaults to the window itself.
        """
        target = dest if dest is not None else self._screen
        target.blit(source, position)

    def load_image(self, path: Path) -> pygame.Surface:
        """Load a PNG file from disk into a new buffer."""
        return pygame.image.load(path).convert_alpha()

    def draw_text(
        self, buffer: pygame.Surface, text: str, position: tuple[int, int], color: Color
    ) -> None:
        """Render a text string and blit it into a buffer."""
        rendered = self._font.render(text, False, color)
        buffer.blit(rendered, position)

    def poll_events(self) -> list[RawEvent]:
        """Return this frame's window events, translated out of pygame types."""
        events: list[RawEvent] = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events.append(RawEvent(kind="quit"))
            elif event.type == pygame.KEYDOWN:
                events.append(RawEvent(kind="keydown", key=pygame.key.name(event.key), unicode=event.unicode))
            elif event.type == pygame.KEYUP:
                events.append(RawEvent(kind="keyup", key=pygame.key.name(event.key)))
        return events

    def present(self) -> None:
        """Push the completed frame to the window."""
        pygame.display.flip()


@dataclass(frozen=True)
class RawEvent:
    """A window event, stripped of pygame types.

    Args:
        kind: One of "quit", "keydown", "keyup".
        key: Key name as a lowercase string (e.g. "up", "escape"), or None.
        unicode: The actual typed character for this key, respecting
            shift/layout (pygame's event.unicode). Empty for non-text keys.
    """
    kind: str
    key: str | None = None
    unicode: str = ""