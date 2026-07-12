"""Poster image generation (UI-agnostic).

Layer order matches the Figma Post component (node 5:151), bottom → top:

1. Image fill — Figma IMAGE scaleMode FILL (``image`` / ``-i``), or a solid
   background colour (default white; ``fill_color`` / ``-c``)
2. Gradient scrim — linear fade under UI chrome (colour/stops via PosterStyle)
3. Cubalite wordmark badge — fill, stroke, font via PosterStyle
4. Headline — wrapped/auto-fit text via PosterStyle
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from cubalite_poster.config import constants
from cubalite_poster.core import text as text_layout
from cubalite_poster.core.colors import Rgb
from cubalite_poster.models import PosterStyle

ImageSource = Path | Image.Image | None


class PosterGenerator:
    """Renders the fixed-design poster canvas.

    The generator knows only about canvas geometry and compositing. It never
    imports GUI toolkits so it can be used from CLI, batch jobs, or tests.
    """

    def __init__(
        self,
        image: ImageSource = None,
        *,
        fill_color: Rgb | None = None,
        headline: str = constants.POSTER_HEADLINE_DEFAULT,
        style: PosterStyle | None = None,
    ) -> None:
        self._image = image
        self._fill_color = (
            fill_color if fill_color is not None else constants.POSTER_BACKGROUND_COLOR
        )
        self._headline = headline
        self._style = style if style is not None else PosterStyle()

    def render(self) -> Image.Image:
        """Composite image fill + scrim + badge + headline into the 4:3 canvas."""
        canvas = self._image_fill_layer().convert(constants.POSTER_COLOR_MODE_RGBA)
        canvas = Image.alpha_composite(canvas, self._gradient_scrim_layer())
        self._draw_badge(canvas)
        self._draw_headline(canvas)
        return canvas.convert(constants.POSTER_COLOR_MODE)

    def save(self, path: Path) -> Path:
        """Render the poster and write it to ``path``. Returns ``path``."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        image = self.render()
        image.save(destination, format=constants.POSTER_OUTPUT_FORMAT)
        return destination

    def _image_fill_layer(self) -> Image.Image:
        """Layer 1: full-bleed image (FILL) or solid image-slot colour."""
        size = (constants.POSTER_WIDTH, constants.POSTER_HEIGHT)
        if self._image is None:
            return Image.new(constants.POSTER_COLOR_MODE, size, self._fill_color)

        source = self._load_image(self._image)
        return _cover_crop(
            source,
            constants.POSTER_WIDTH,
            constants.POSTER_HEIGHT,
            fallback_color=self._fill_color,
        )

    def _gradient_scrim_layer(self) -> Image.Image:
        """Layer 2: vertical gradient (stops/colour from style)."""
        style = self._style
        width = constants.POSTER_WIDTH
        height = constants.POSTER_HEIGHT
        alpha_strip = Image.new("L", (1, height))
        pixels = alpha_strip.load()
        assert pixels is not None
        for y in range(height):
            y_norm = y / (height - 1) if height > 1 else 0.0
            pixels[0, y] = _gradient_alpha(
                y_norm,
                start=style.gradient_start_y,
                end=style.gradient_end_y,
                alpha_start=style.gradient_alpha_start,
                alpha_end=style.gradient_alpha_end,
            )

        alpha = alpha_strip.resize((width, height), Image.Resampling.BILINEAR)
        solid = Image.new(
            constants.POSTER_COLOR_MODE,
            (width, height),
            style.gradient_rgb,
        )
        r, g, b = solid.split()
        return Image.merge(constants.POSTER_COLOR_MODE_RGBA, (r, g, b, alpha))

    def _draw_badge(self, canvas: Image.Image) -> None:
        """Layer 3: wordmark badge (fill, stroke, font from style)."""
        style = self._style
        x = style.badge_x
        y = style.badge_y
        w = style.badge_width
        h = style.badge_height
        box = (x, y, x + w - 1, y + h - 1)

        draw = ImageDraw.Draw(canvas)
        draw.rectangle(
            box,
            fill=(*style.badge_fill, 255),
            outline=(*style.badge_stroke, 255),
            width=style.badge_stroke_width,
        )

        font = text_layout.load_font(style.badge_font_file, style.badge_font_size)
        label = style.badge_label
        text_box = draw.textbbox((0, 0), label, font=font)
        text_w = text_box[2] - text_box[0]
        text_h = text_box[3] - text_box[1]
        text_x = x + (w - text_w) // 2 - text_box[0]
        text_y = y + (h - text_h) // 2 - text_box[1]
        draw.text(
            (text_x, text_y),
            label,
            font=font,
            fill=(*style.badge_text_color, 255),
        )

    def _draw_headline(self, canvas: Image.Image) -> None:
        """Layer 4: wrapped/auto-fit headline in the bottom content box."""
        style = self._style
        draw = ImageDraw.Draw(canvas)
        top = style.headline_top
        bottom_limit = style.headline_bottom_limit
        max_height = max(0, bottom_limit - top)
        if max_height <= 0:
            return

        font, lines = text_layout.fit_headline(
            draw,
            self._headline,
            font_file=style.headline_font_file,
            preferred_size=style.headline_font_size,
            min_size=style.headline_min_font_size,
            max_width=style.headline_width,
            max_height=max_height,
            max_lines=style.headline_max_lines,
            auto_fit=style.headline_auto_fit,
        )
        if not lines:
            return

        line_h = text_layout.line_height(font)
        y = top
        fill = (*style.headline_color, 255)
        x = style.headline_x
        for line in lines:
            # Draw while the line's *top* is inside the box. Guarding the
            # bottom (y + line_h) made a single line taller than the box vanish
            # entirely; a slight overflow into the bottom pad beats disappearing.
            if y >= bottom_limit:
                break
            draw.text((x, y), line, font=font, fill=fill)
            y += line_h

    @staticmethod
    def _load_image(image: Path | Image.Image) -> Image.Image:
        if isinstance(image, Image.Image):
            return image.convert(constants.POSTER_COLOR_MODE)
        with Image.open(image) as opened:
            return opened.convert(constants.POSTER_COLOR_MODE)


def _cover_crop(
    image: Image.Image,
    target_w: int,
    target_h: int,
    *,
    fallback_color: Rgb,
) -> Image.Image:
    """Scale so the shorter side fills the box, then center-crop (Figma FILL)."""
    src_w, src_h = image.size
    if src_w == 0 or src_h == 0:
        return Image.new(
            constants.POSTER_COLOR_MODE, (target_w, target_h), fallback_color
        )

    scale = max(target_w / src_w, target_h / src_h)
    new_w = max(1, round(src_w * scale))
    new_h = max(1, round(src_h * scale))
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = max(0, (new_w - target_w) // 2)
    top = max(0, (new_h - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def _gradient_alpha(
    y_norm: float,
    *,
    start: float,
    end: float,
    alpha_start: int,
    alpha_end: int,
) -> int:
    """Alpha at normalized Y (0 = top, 1 = bottom) for the scrim."""
    if y_norm <= start:
        return alpha_start
    if y_norm >= end:
        return alpha_end
    t = (y_norm - start) / (end - start)
    return int(round(alpha_start + t * (alpha_end - alpha_start)))
