# Assigned Maze Generator Package

Reference record for the external A-Maze-ing package assigned to this project.
Required by the subject, section V.4: the package must be used as-is, without
modification, and will be re-installed during peer review.

## Identity

| Field   | Value                                     |
|---------|-------------------------------------------|
| Name    | mazegenerator                             |
| Version | 2.1.0                                     |
| Author  | ol <ol@42.fr>                             |
| License | MIT                                       |
| Wheel   | mazegenerator-2.1.0-py3-none-any.whl      |
| Tag     | py3-none-any (pure Python, any platform)  |

Changelog entry for this version: "Fix the pac-man compatibility".

## Origin

| Field          | Value                                                       |
|----------------|-------------------------------------------------------------|
| Source         | Provided with the project subject as a zip archive           |
| Package author | ol <ol@42.fr> (from dist-info/METADATA)                      |
| Contact        | Project staff                                                |
| Received on    | 2026-09-07                                                   |
| Received as    | Extracted wheel contents (see note below)                    |

The package arrived as the two directories `mazegenerator/` and
`mazegenerator-2.1.0.dist-info/` — the extracted contents of an installed
wheel — rather than as the `.whl` file itself. The wheel was reconstructed
from them, see Handling decisions.

Subject V.4 states that an A-Maze-ing package is assigned to each project at
project start and must be used as-is. This package, mazegenerator 2.1.0, is the
one assigned to us. Its changelog entry for 2.1.0 reads "Fix the pac-man
compatibility", indicating it was prepared for this project.

Should a different package be assigned later, only our adapter module needs to
change: the rest of the game depends on our own internal maze model, never on
the generator's interface directly.

## Integrity

The package source files are unmodified. Verified against the sha256 digests
recorded by the original author in dist-info/RECORD.

| File                          | Size | sha256 (hex)                                                     |
|-------------------------------|------|------------------------------------------------------------------|
| mazegenerator/__init__.py     |   70 | 6833189b4469e7ced6c5e441252b8d94864e03a3821b39cc832e9e44ad53125c |
| mazegenerator/mazegenerator.py| 8273 | 2a62ca4214d482d6017997c9838716662be8b79a6fcea96753aff366cd81202b |

Note: the .whl file itself is not hashed here. A wheel is a zip archive and
stores file timestamps, so rebuilding it produces a different archive digest
even when the contained source is byte-identical. The per-file digests above
are the stable proof of integrity.

To re-verify at any time:

    unzip -p vendor/mazegenerator-2.1.0-py3-none-any.whl \
        mazegenerator/mazegenerator.py | sha256sum

## Handling decisions

1. The two extracted directories were repackaged into a standard wheel
   (a wheel is a zip archive; the filename follows the tag in dist-info/WHEEL).
   Nothing inside was altered.
2. The wheel is committed to the repository under vendor/ so that the build
   environment is fully reproducible without network access.
3. It is installed as a real dependency into the project virtualenv, not
   imported from the repository root. Importing from the root would work only
   by accident (current directory on sys.path) and would break once the game
   is launched from another directory or frozen with PyInstaller.
4. The package source is never edited. Every adaptation required by our game
   lives in our own adapter module.

## Installation

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

requirements.txt points at the local wheel by path. `pip freeze` must not be
used to regenerate it: it would emit `mazegenerator==2.1.0`, which pip would
try to resolve from PyPI, where the package does not exist.

To re-install during peer review:

    pip uninstall -y mazegenerator
    pip install -r requirements.txt

## Verified behaviour

Observed by running the package directly, not taken from its README.

Constructor:

    MazeGenerator(size=(width, height), perfect=False,
                  entry_cell=(x, y), exit_cell=(x, y), seed=0)

Grid is indexed maze[y][x]. Each cell is an int; the four low bits mark walls:
North=1, East=2, South=4, West=8. A set bit means a wall is present.
Value 15 means a fully enclosed cell.

Wall data is symmetric between neighbours in every size tested, so collision
detection needs only a local bit test on the current cell.

## Known quirks

These are properties of the assigned package that our loader must absorb.

1. `seed=0` means full randomness, not "seed zero". Values <= 0 are not
   reproducible. Only seed >= 1 yields a repeatable maze.
2. The package calls `random.seed()` on the global random module, which resets
   any global randomness the game may rely on. Our game therefore uses its own
   Random instances exclusively.
3. A "42" logo of 18 enclosed cells (value 15) is inserted at the centre of the
   maze. Consequence: with an EVEN width the centre cell is always one of those
   blocks; with an ODD width it is always free. Verified across 108 sizes.
   The subject requires the player to start in the middle, so the loader
   falls back to the nearest walkable cell.
4. The four maze corners are never blocked, so super-pacgums and ghosts can
   always be placed there as the subject requires.
5. With perfect=False the braid pass removes dead ends, but it never opens a
   wall towards a logo block. Exactly two dead ends therefore remain, both
   inside the "42" shape, on every seed tested.
6. If width < 14 or height < 10 the logo is skipped and a warning is printed
   to stdout by the package itself.
7. Invalid arguments raise raw IndexError / TypeError with no package-specific
   exception type. Some invalid input fails silently instead: size=(1,1)
   returns a grid whose dimensions do not match the requested size, and a
   non-boolean truthy `perfect` value silently produces a perfect maze.
   All validation happens on our side, before the call.
8. Reported dimensions are not trustworthy. The loader always reads
   len(maze) and len(maze[0]) from the returned grid.
9. `shortest_path` is typed `str | bool` and can be an empty string when entry
   equals exit. Both False and "" are falsy, so a plain truthiness check is
   unsafe. Our game does not use entry/exit; connectivity is verified by our
   own flood fill from the player start cell.

## Documentation discrepancies

The package README (dist-info/METADATA) does not match the code:

- Quick Start shows `MazeGenerator(width=20, height=20)`. There are no such
  keyword arguments; that call raises TypeError.
- The default size is documented as (20,20); the code uses (15,15).
- `maze_entry` / `maze_exit` are documented as (row, col); they are (x, y).

The implementation is treated as the source of truth.