# Graphical Library Choice

Record of the graphics library selected for this project and of its compliance
with the constraint in subject IV.

## The constraint

Subject IV requires a simple graphical library, MLX or similar, and defines
"similar" narrowly: every function we actually use must have an equivalent in
MLX. A function without an MLX equivalent is not allowed.

The constraint applies to the functions we call, not to the library as a whole.
A rich library is therefore acceptable provided we restrict ourselves to the
subset that maps onto MLX.

## Decision

| Field | Value |
|---|---|
| Library | pygame |
| Version | 2.6.1 |
| MLX reference |  MiniLibX (the MLX distributed by 42) |
| Confirmed by | Alex|
| Confirmed on | 08.09.2026 |

The mapping holds for MLX42 as well; only the function names differ
(`mlx_put_pixel`, `mlx_image_to_window`, `mlx_put_string`, `mlx_load_png`).
The set of available primitives is the same in both implementations.

## Rationale

## Rationale

pygame is installable through pip, ships prebuilt wheels for Linux, macOS and
Windows, and is the de-facto standard 2D library for Python, which matters for
the packaging requirement in subject VII. Under the hood it wraps SDL2, so it is
a C extension rather than pure Python; this is invisible to us but relevant when
freezing the game, since PyInstaller must bundle the native SDL libraries.

Its surface-and-blit model maps directly onto the MLX image model: an off-screen
buffer that is drawn into and then pushed to the window in one call. The
restricted subset below is therefore a natural way to use the library rather
than a workaround.

## Approved primitives

The game is written exclusively against a thin facade that exposes the
operations below. Each one has a documented MLX counterpart.

| Facade operation | pygame call | MLX equivalent |
|---|---|---|
| Initialise the graphics context | `pygame.init` | `mlx_init` |
| Create a window | `pygame.display.set_mode` | `mlx_new_window` |
| Destroy the window / shut down | `pygame.quit` | `mlx_destroy_window` |
| Create an off-screen image buffer | `pygame.Surface` | `mlx_new_image` |
| Write a single pixel into a buffer | `Surface.set_at` | `mlx_pixel_put` |
| Clear a surface to a single colour | `Surface.fill` | `mlx_clear_window` |
| Blit a buffer into the window | `Surface.blit` | `mlx_put_image_to_window` |
| Load an image from a file | `pygame.image.load` | `mlx_png_file_to_image` |
| Draw a text string | `Font.render` + `blit` | `mlx_string_put` |
| Receive key events | iterate `pygame.event.get()` | `mlx_key_hook` / `mlx_hook` |
| Receive the window-close event | `QUIT` event | `mlx_hook` (destroy event) |
| Advance the main loop | our own loop | `mlx_loop` / `mlx_loop_hook` |

`Surface.fill` was explicitly raised with staff, since it can also fill an
arbitrary rectangle rather than only clear a surface. It was confirmed as an
acceptable equivalent of `mlx_clear_window`. We use it only to clear a whole
surface to one colour, never to draw rectangular shapes.

## Excluded

The following pygame features have no MLX equivalent and are not used anywhere
in the project.

| Excluded | Why | What we do instead |
|---|---|---|
| `pygame.draw.*` (rect, line, circle, polygon) | MLX has no drawing primitives beyond a single pixel | write pixels into an image buffer, or use a loaded sprite |
| `pygame.transform.*` (scale, rotate, flip) | no MLX equivalent | pre-size and pre-orient assets, or compose them pixel by pixel |
| `pygame.sprite.*` (Sprite, Group) | MLX has no sprite system | our own entity model in `pacman/core` |
| `pygame.mixer` | MLX has no audio at all | no sound in the game |
| `Rect.colliderect` and other collision helpers | MLX has no collision detection | grid-based collision, a bit test on the current maze cell |
| `pygame.time.Clock` as the timing source | MLX drives timing through its loop hook | `time.monotonic` in our own main loop |

## Facade rule

Only the facade module imports pygame. Every other module in the project talks
to the facade.

This is enforced at review: a grep for the library name outside the facade
module must return nothing. The rule gives us three things — a single file to
present at the defense as the complete list of primitives in use, the ability
to swap the backend without touching game logic, and the guarantee that the
excluded list above cannot be violated by accident.

## Consequences for the design

The restriction is not merely bureaucratic; it shapes the renderer.

1. Maze walls are drawn by writing pixels into an image buffer, not by drawing
   lines. Since the maze is static for the duration of a level, it is rendered
   once into a cached background buffer and blitted every frame.
2. Pacgums and super-pacgums are either small pixel patterns or loaded sprites,
   not filled circles.
3. Because no scaling is available, tile size is fixed at asset-authoring time
   or assets are composed at the required size.
4. Per-pixel writes are expensive in Python, so everything static is cached and
   only dynamic entities are redrawn each frame.