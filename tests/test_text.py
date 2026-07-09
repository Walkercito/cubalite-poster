"""Word-wrap and auto-fit helpers for headline layout."""

from PIL import Image, ImageDraw, ImageFont

from cubalite_poster.config import constants
from cubalite_poster.core.text import fit_headline, line_height, load_font, wrap_text


def _font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return load_font(
        constants.POSTER_HEADLINE_FONT_FILE, constants.POSTER_HEADLINE_FONT_SIZE
    )


def test_wrap_text_respects_max_width() -> None:
    image = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(image)
    font = _font()
    max_width = constants.POSTER_HEADLINE_WIDTH

    sample = (
        "Lorem Ipsum is simply dummy text of the printing and typesetting industry."
    )
    lines = wrap_text(draw, sample, font, max_width)
    assert len(lines) >= 2
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        assert box[2] - box[0] <= max_width


def test_wrap_text_empty() -> None:
    image = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(image)
    assert wrap_text(draw, "   ", _font(), 100) == []


def test_line_height_positive() -> None:
    assert line_height(_font()) > 0


def test_fit_headline_long_title_stays_two_lines() -> None:
    """Long Spanish titles shrink to fit max_lines=2 instead of overflowing."""
    long_title = (
        "Regresará a la Serie Nacional pitcher cubano que vive en México "
        "y ha jugado en varias ligas allí"
    )
    image = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(image)
    font, lines = fit_headline(
        draw,
        long_title,
        font_file=constants.POSTER_HEADLINE_FONT_FILE,
        preferred_size=constants.POSTER_HEADLINE_FONT_SIZE,
        min_size=constants.POSTER_HEADLINE_MIN_FONT_SIZE,
        max_width=constants.POSTER_HEADLINE_WIDTH,
        max_height=constants.POSTER_HEADLINE_MAX_HEIGHT,
        max_lines=2,
        auto_fit=True,
    )
    assert 1 <= len(lines) <= 2
    assert line_height(font) * len(lines) <= constants.POSTER_HEADLINE_MAX_HEIGHT
    # Prefer a smaller-than-default size for this long string.
    if isinstance(font, ImageFont.FreeTypeFont):
        assert font.size <= constants.POSTER_HEADLINE_FONT_SIZE
