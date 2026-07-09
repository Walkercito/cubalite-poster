"""PosterGenerator composites image fill + scrim + badge + headline."""

from pathlib import Path

from PIL import Image

from cubalite_poster.config import constants
from cubalite_poster.core import PosterGenerator, parse_hex_color
from cubalite_poster.core.generator import _gradient_alpha


def _rgb(image: Image.Image, xy: tuple[int, int]) -> tuple[int, int, int]:
    pixel = image.getpixel(xy)
    assert isinstance(pixel, tuple)
    return int(pixel[0]), int(pixel[1]), int(pixel[2])


def test_render_size_and_aspect() -> None:
    image = PosterGenerator().render()

    assert image.size == (constants.POSTER_WIDTH, constants.POSTER_HEIGHT)
    assert image.mode == constants.POSTER_COLOR_MODE
    width, height = image.size
    assert (
        width * constants.POSTER_ASPECT_RATIO[1]
        == height * constants.POSTER_ASPECT_RATIO[0]
    )


def test_default_white_image_fill_with_scrim() -> None:
    image = PosterGenerator().render()
    width, height = image.size

    top = _rgb(image, (width // 2, 0))
    mid = _rgb(image, (width // 2, height // 2))
    bottom = _rgb(image, (width // 2, height - 1))

    assert top == constants.POSTER_BACKGROUND_COLOR
    assert mid == constants.POSTER_BACKGROUND_COLOR
    assert bottom[0] < mid[0]
    assert bottom[1] < mid[1]
    assert bottom[2] < mid[2]


def test_fill_color_overrides_image_slot_not_badge() -> None:
    red = (255, 0, 0)
    image = PosterGenerator(fill_color=red).render()
    width = constants.POSTER_WIDTH

    assert _rgb(image, (width // 2, 0)) == red

    bx = constants.POSTER_BADGE_X + 6
    by = constants.POSTER_BADGE_Y + 6
    assert _rgb(image, (bx, by)) == constants.POSTER_BADGE_FILL


def test_badge_fill_sits_above_scrim() -> None:
    image = PosterGenerator().render()
    x = constants.POSTER_BADGE_X + 6
    y = constants.POSTER_BADGE_Y + 6
    assert _rgb(image, (x, y)) == constants.POSTER_BADGE_FILL


def test_empty_headline_draws_no_text() -> None:
    image = PosterGenerator(fill_color=(0, 0, 0), headline="").render()
    x0 = constants.POSTER_HEADLINE_X
    y0 = (
        constants.POSTER_BADGE_Y
        + constants.POSTER_BADGE_HEIGHT
        + constants.POSTER_CONTENT_ITEM_SPACING
    )
    # Default empty headline: no bright white glyphs in the text box.
    r, g, b = _rgb(image, (x0 + 8, y0 + 8))
    assert r < 40 and g < 40 and b < 40


def test_headline_draws_white_pixels_in_text_box() -> None:
    # Solid dark fill so white glyphs are easy to detect.
    image = PosterGenerator(fill_color=(0, 0, 0), headline="Hello").render()
    x0 = constants.POSTER_HEADLINE_X
    y0 = (
        constants.POSTER_BADGE_Y
        + constants.POSTER_BADGE_HEIGHT
        + constants.POSTER_CONTENT_ITEM_SPACING
    )
    x1 = x0 + constants.POSTER_HEADLINE_WIDTH
    y1 = constants.POSTER_HEIGHT - constants.POSTER_CONTENT_PADDING_BOTTOM

    whites = 0
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 4):
            r, g, b = _rgb(image, (x, y))
            if r > 200 and g > 200 and b > 200:
                whites += 1
    assert whites > 20


def test_headline_fits_full_sample_in_two_lines() -> None:
    """Figma sample wraps to two lines and both must render (not one-line clip)."""
    sample = (
        "Lorem Ipsum is simply dummy text of the printing and typesetting industry."
    )
    image = PosterGenerator(fill_color=(0, 0, 0), headline=sample).render()
    top = (
        constants.POSTER_BADGE_Y
        + constants.POSTER_BADGE_HEIGHT
        + constants.POSTER_CONTENT_ITEM_SPACING
    )
    # Sample through the middle of each rendered line (line height ≈ 50).
    y1 = top + 20
    y2 = top + 70
    whites_line1 = 0
    whites_line2 = 0
    for x in range(
        constants.POSTER_HEADLINE_X,
        constants.POSTER_HEADLINE_X + constants.POSTER_HEADLINE_WIDTH,
        4,
    ):
        r1, g1, b1 = _rgb(image, (x, y1))
        if r1 > 200 and g1 > 200 and b1 > 200:
            whites_line1 += 1
        r2, g2, b2 = _rgb(image, (x, y2))
        if r2 > 200 and g2 > 200 and b2 > 200:
            whites_line2 += 1
    assert whites_line1 > 10
    assert whites_line2 > 10


def test_headline_stays_within_max_height_box() -> None:
    long = "word " * 200
    image = PosterGenerator(fill_color=(0, 0, 0), headline=long).render()
    top = (
        constants.POSTER_BADGE_Y
        + constants.POSTER_BADGE_HEIGHT
        + constants.POSTER_CONTENT_ITEM_SPACING
    )
    below_box_y = top + constants.POSTER_HEADLINE_MAX_HEIGHT + 2
    for x in range(
        constants.POSTER_HEADLINE_X,
        constants.POSTER_HEADLINE_X + constants.POSTER_HEADLINE_WIDTH,
        16,
    ):
        r, g, b = _rgb(image, (x, below_box_y))
        assert r < 80 and g < 80 and b < 80


def test_gradient_alpha_curve_matches_figma_stops() -> None:
    kwargs = {
        "start": constants.POSTER_GRADIENT_START_Y,
        "end": constants.POSTER_GRADIENT_END_Y,
        "alpha_start": constants.POSTER_GRADIENT_ALPHA_START,
        "alpha_end": constants.POSTER_GRADIENT_ALPHA_END,
    }
    assert _gradient_alpha(0.0, **kwargs) == constants.POSTER_GRADIENT_ALPHA_START
    assert (
        _gradient_alpha(constants.POSTER_GRADIENT_START_Y, **kwargs)
        == constants.POSTER_GRADIENT_ALPHA_START
    )
    assert _gradient_alpha(1.0, **kwargs) > constants.POSTER_GRADIENT_ALPHA_START
    assert _gradient_alpha(1.0, **kwargs) > 150
    assert (
        _gradient_alpha(constants.POSTER_GRADIENT_END_Y, **kwargs)
        == constants.POSTER_GRADIENT_ALPHA_END
    )


def test_image_fill_covers_canvas() -> None:
    source = Image.new("RGB", (100, 400), (200, 10, 10))
    image = PosterGenerator(image=source).render()

    assert image.size == (constants.POSTER_WIDTH, constants.POSTER_HEIGHT)
    top = _rgb(image, (constants.POSTER_WIDTH // 2, 0))
    assert top[0] > 150
    assert top[1] < 40
    assert top[2] < 40


def test_parse_hex_color() -> None:
    assert parse_hex_color("FFFFFF") == constants.POSTER_BACKGROUND_COLOR
    assert parse_hex_color("#FEF7EC") == constants.POSTER_BADGE_FILL
    assert parse_hex_color("00aaff") == (0, 170, 255)


def test_parse_hex_color_rejects_bad_input() -> None:
    for bad in ("", "FFF", "GGGGGG", "12345", "1234567"):
        try:
            parse_hex_color(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")


def test_save_writes_png(tmp_path: Path) -> None:
    out = tmp_path / constants.POSTER_DEFAULT_FILENAME
    result = PosterGenerator().save(out)

    assert result == out
    assert out.is_file()
    assert out.stat().st_size > 0
