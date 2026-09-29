"""Graphics facade: the only module that imports pygame.

Every operation here has a documented MLX equivalent (see
project-management/graphics_library.md), with open exceptions still
to be cleared with staff the same way Surface.fill was:
``pygame.display.flip()`` and blitting into an arbitrary buffer (not
just the window) via the ``dest`` parameter of ``blit``.

No other module in the project may import pygame directly; this is
checked by grep at review time.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import pygame

Color = tuple[int, int, int]

Buffer: TypeAlias = pygame.Surface
"""Image buffer type. Other modules annotate with this, never with pygame."""

_TEXT_CACHE_LIMIT = 256
"""Rendered strings kept before the text cache is flushed."""


@dataclass(frozen=True)
class RawEvent:
    """A window event, stripped of pygame types.

    Attributes:
        kind: One of "quit", "keydown", "keyup".
        key: Key name as a lowercase string (e.g. "up", "escape"), or None.
        unicode: The typed character for this key, respecting shift and
            layout. Empty for keys that produce no text.
    """

    kind: str
    key: str | None = None
    unicode: str = ""


class GraphicsFacade:
    """Thin wrapper around pygame, restricted to the MLX-equivalent subset.

    Owns the window and the font used for text. Everything else in
    ``render/`` and ``ui/`` talks to pygame only through this class.
    """

    def __init__(
        self,
        width: int,
        height: int,
        title: str = "Pac-Man",
        font_size: int = 16,
    ) -> None:
        """Initialise pygame and open the window.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            title: Text shown in the window's title bar.
            font_size: Point size for text drawn via draw_text.
        """
        pygame.init()
        self._screen: pygame.Surface = pygame.display.set_mode(
            (width, height)
        )
        pygame.display.set_caption(title)
        self._font: pygame.font.Font = pygame.font.SysFont(None, font_size)
        self._image_cache: dict[Path, pygame.Surface] = {}
        self._text_cache: dict[tuple[str, Color], pygame.Surface] = {}

    def close(self) -> None:
        """Shut down pygame. Safe to call more than once."""
        pygame.quit()

    def new_buffer(self, width: int, height: int) -> Buffer:
        """Create an off-screen image buffer of the given size."""
        return pygame.Surface((width, height))

    def clear(self, buffer: Buffer, color: Color) -> None:
        """Fill an entire buffer with one colour.

        Only ever used to clear a whole surface, never to draw a
        rectangle at an offset, which would exceed the MLX equivalence
        agreed with staff.
        """
        buffer.fill(color)

    def put_pixel(self, buffer: Buffer, x: int, y: int, color: Color) -> None:
        """Write a single pixel into a buffer."""
        buffer.set_at((x, y), color)

    def blit(
        self,
        source: Buffer,
        position: tuple[int, int] = (0, 0),
        dest: Buffer | None = None,
    ) -> None:
        """Draw a buffer into another buffer, or into the window.

        Args:
            source: The buffer being drawn.
            position: Top-left position in the destination.
            dest: Target buffer. Defaults to the window itself.
        """
        target = dest if dest is not None else self._screen
        target.blit(source, position)

    def load_image(self, path: Path) -> Buffer:
        """Load a PNG file into a buffer, cached by path."""
        image = self._image_cache.get(path)
        if image is None:
            image = pygame.image.load(path).convert_alpha()
            self._image_cache[path] = image
        return image

    def draw_text(
        self,
        buffer: Buffer,
        text: str,
        position: tuple[int, int],
        color: Color,
    ) -> None:
        """Render a text string and blit it into a buffer.

        Rendered text is cached by (text, colour): most strings repeat
        from frame to frame and Font.render is the expensive part.
        """
        key = (text, color)
        rendered = self._text_cache.get(key)
        if rendered is None:
            if len(self._text_cache) >= _TEXT_CACHE_LIMIT:
                self._text_cache.clear()
            rendered = self._font.render(text, False, color)
            self._text_cache[key] = rendered
        buffer.blit(rendered, position)

    def poll_events(self) -> list[RawEvent]:
        """Return this frame's window events, without pygame types."""
        events: list[RawEvent] = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events.append(RawEvent(kind="quit"))
            elif event.type == pygame.KEYDOWN:
                events.append(
                    RawEvent(
                        kind="keydown",
                        key=pygame.key.name(event.key),
                        unicode=event.unicode,
                    )
                )
            elif event.type == pygame.KEYUP:
                events.append(
                    RawEvent(kind="keyup", key=pygame.key.name(event.key))
                )
        return events

    def present(self) -> None:
        """Push the completed frame to the window."""
        pygame.display.flip()
