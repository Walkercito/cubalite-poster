"""Text layout helpers for the poster engine (UI-agnostic)."""

from __future__ import annotations

from pathlib import Path

from PIL import ImageDraw, ImageFont

from cubalite_poster import resources


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Word-wrap ``text`` so each line fits within ``max_width`` pixels."""
    normalized = " ".join(text.replace("\u00a0", " ").split())
    if not normalized:
        return []

    words = normalized.split(" ")
    lines: list[str] = []
    current: list[str] = []

    for word in words:
        trial = " ".join([*current, word])
        if _text_width(draw, trial, font) <= max_width or not current:
            current.append(word)
            # Single word wider than max_width: keep it on its own line.
            if len(current) == 1 and _text_width(draw, current[0], font) > max_width:
                lines.append(current[0])
                current = []
        else:
            lines.append(" ".join(current))
            current = [word]

    if current:
        lines.append(" ".join(current))
    return lines


def line_height(font: ImageFont.ImageFont | ImageFont.FreeTypeFont) -> int:
    """Pixel line height for stacked wrapped lines (ascent + descent)."""
    if isinstance(font, ImageFont.FreeTypeFont):
        ascent, descent = font.getmetrics()
        return ascent + descent
    box = font.getbbox("Ay")
    return int(box[3] - box[1])


def load_font(
    font_file: str, size: int
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font by file name (under assets/fonts) or absolute/relative path."""
    path = _resolve_font_path(font_file)
    if path is not None and path.is_file():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def fit_headline(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    font_file: str,
    preferred_size: int,
    min_size: int,
    max_width: int,
    max_height: int,
    max_lines: int,
    auto_fit: bool,
) -> tuple[ImageFont.ImageFont | ImageFont.FreeTypeFont, list[str]]:
    """Choose font size and wrap so the headline fits the box when possible.

    With ``auto_fit``, the size steps down from ``preferred_size`` to
    ``min_size`` until the wrap uses at most ``max_lines`` and fits
    ``max_height``. Otherwise the preferred size is used and lines are clipped.
    """
    if not text.strip():
        return load_font(font_file, preferred_size), []

    sizes = (
        range(preferred_size, min_size - 1, -1)
        if auto_fit
        else range(preferred_size, preferred_size - 1, -1)
    )
    last_font = load_font(font_file, preferred_size)
    last_lines: list[str] = []

    for size in sizes:
        font = load_font(font_file, size)
        lines = wrap_text(draw, text, font, max_width)
        if not lines:
            return font, []
        lh = line_height(font)
        fits_lines = len(lines) <= max_lines
        fits_height = len(lines) * lh <= max_height
        last_font, last_lines = font, lines
        if fits_lines and fits_height:
            return font, lines

    # Could not fit: keep smallest (or preferred) and clip to max_lines.
    return last_font, last_lines[: max(0, max_lines)]


def _resolve_font_path(font_file: str) -> Path | None:
    stripped = font_file.strip()
    if not stripped:
        return None
    candidate = Path(stripped).expanduser()
    if candidate.is_file():
        return candidate
    bundled = resources.FONTS_DIR / stripped
    if bundled.is_file():
        return bundled
    return candidate if candidate.suffix else bundled


def _text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return int(box[2] - box[0])
