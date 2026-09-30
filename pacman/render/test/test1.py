import pytest

from pacman.render.layout import MIN_TILE, TILE_SIZES, fit_layout, make_layout


@pytest.mark.parametrize("tile", [MIN_TILE, 9, 16, 24, 32, 100])
def test_derived_sizes_stay_consistent(tile: int) -> None:
    layout = make_layout(tile, 15, 11)
    assert layout.entity_margin * 2 < tile
    assert layout.wall < tile
    assert layout.super_radius * 2 + 1 <= tile
    assert layout.pacgum_radius <= layout.super_radius
    assert layout.window_width == 15 * tile
    assert layout.window_height == 11 * tile + layout.hud_height


def test_maze_is_centred_in_a_bigger_window() -> None:
    layout = make_layout(16, 21, 21)
    assert layout.maze_origin(21, 21) == (0, 0)
    expected = ((21 - 15) * 16 // 2, (21 - 11) * 16 // 2)
    assert layout.maze_origin(15, 11) == expected


def test_fit_prefers_largest_tile_that_fits() -> None:
    assert fit_layout(15, 11).tile == max(TILE_SIZES)


def test_fit_falls_back_to_smallest_when_nothing_fits() -> None:
    assert fit_layout(200, 200).tile == min(TILE_SIZES)


def test_too_small_tile_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_layout(MIN_TILE - 1, 5, 5)
