from typing import Protocol, Final
WALL_N: Final[int] = 1
WALL_E: Final[int] = 2
WALL_S: Final[int] = 4
WALL_W: Final[int] = 8
ALL_WALLS: Final[int] = WALL_N | WALL_E | WALL_S | WALL_W


class MazeSource(Protocol):
    """An object holding one generated maze in the package's raw format."""

    @property
    def maze(self) -> list[list[int]]:
        """The generated grid, indexed row first as ``grid[row][col]``.

        Each value is a bit mask of the walls closing that cell:
        north 1, east 2, south 4, west 8. A set bit means a wall is
        present, so 0 is an open crossroads and 15 is a fully enclosed
        cell used for the generator's decorative blocks.

        Wall data is symmetric between neighbours, so a move can be
        tested from the current cell alone.

        The grid's real dimensions are read from this value, never from
        the size that was requested: the package may return a grid whose
        shape does not match the arguments it was given.
        """
        ...


class MazeSourceFactory(Protocol):
    """Anything that produces a MazeSource: the package class, or a fake."""

    def __call__(self,
                 *,  # Всі аргументи після зірочки стають СУТО іменованими
                 size: tuple[int, int],
                 perfect: bool,
                 seed: int) -> MazeSource:
        """Generate one maze.

        Protocols describe instances rather than constructors, so
        creation is expressed as a call: a class is callable, and so is
        a fake factory used in tests.

        Args:
            size: Requested grid size as (width, height). Treated as a
                request, not a guarantee.
            perfect: Must be a real bool. A truthy string is accepted
                silently by the package and yields a perfect maze, which
                is full of dead ends and unusable for Pac-Man. The game
                always passes False, as subject V.4 requires.
            seed: Must be >= 1. The package treats 0 and negative values
                as "seed from system entropy", which makes the maze
                irreproducible.

        Returns:
            An object exposing the generated grid through ``maze``.

        Raises:
            Exception: The package raises bare IndexError or TypeError on
                invalid arguments, with no package-specific type. The
                adapter catches broadly and re-raises MazeError.
        """
        ...
