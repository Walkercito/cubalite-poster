"""Tunable poster appearance (UI-agnostic plain data)."""

from __future__ import annotations

from dataclasses import dataclass

from cubalite_poster.config import constants
from cubalite_poster.core.colors import Rgb


@dataclass(frozen=True)
class PosterStyle:
    """Advanced styling for the Post engine (defaults match Figma node 5:151)."""

    # --- Gradient scrim ----------------------------------------------------
    gradient_rgb: Rgb = constants.POSTER_GRADIENT_RGB
    gradient_start_y: float = constants.POSTER_GRADIENT_START_Y
    gradient_end_y: float = constants.POSTER_GRADIENT_END_Y
    gradient_alpha_start: int = constants.POSTER_GRADIENT_ALPHA_START
    gradient_alpha_end: int = constants.POSTER_GRADIENT_ALPHA_END

    # --- Content insets (drive headline width + bottom limit) --------------
    content_padding_left: int = constants.POSTER_CONTENT_PADDING_LEFT
    content_padding_right: int = constants.POSTER_CONTENT_PADDING_RIGHT
    content_padding_bottom: int = constants.POSTER_CONTENT_PADDING_BOTTOM
    content_item_spacing: int = constants.POSTER_CONTENT_ITEM_SPACING

    # --- Wordmark badge ----------------------------------------------------
    badge_x: int = constants.POSTER_BADGE_X
    badge_y: int = constants.POSTER_BADGE_Y
    badge_width: int = constants.POSTER_BADGE_WIDTH
    badge_height: int = constants.POSTER_BADGE_HEIGHT
    badge_fill: Rgb = constants.POSTER_BADGE_FILL
    badge_stroke: Rgb = constants.POSTER_BADGE_STROKE
    badge_stroke_width: int = constants.POSTER_BADGE_STROKE_WIDTH
    badge_label: str = constants.POSTER_BADGE_LABEL
    badge_font_file: str = constants.POSTER_BADGE_FONT_FILE
    badge_font_size: int = constants.POSTER_BADGE_FONT_SIZE
    badge_text_color: Rgb = constants.POSTER_BADGE_TEXT_COLOR

    # --- Headline ----------------------------------------------------------
    headline_font_file: str = constants.POSTER_HEADLINE_FONT_FILE
    headline_font_size: int = constants.POSTER_HEADLINE_FONT_SIZE
    headline_min_font_size: int = constants.POSTER_HEADLINE_MIN_FONT_SIZE
    headline_color: Rgb = constants.POSTER_HEADLINE_COLOR
    headline_max_height: int = constants.POSTER_HEADLINE_MAX_HEIGHT
    headline_max_lines: int = constants.POSTER_HEADLINE_MAX_LINES
    headline_auto_fit: bool = constants.POSTER_HEADLINE_AUTO_FIT

    @property
    def headline_x(self) -> int:
        return self.content_padding_left

    @property
    def headline_width(self) -> int:
        return (
            constants.POSTER_WIDTH
            - self.content_padding_left
            - self.content_padding_right
        )

    @property
    def headline_top(self) -> int:
        return self.badge_y + self.badge_height + self.content_item_spacing

    @property
    def headline_bottom_limit(self) -> int:
        """Bottom edge of the headline box (canvas Y, exclusive of pad below)."""
        by_height = self.headline_top + self.headline_max_height
        by_padding = constants.POSTER_HEIGHT - self.content_padding_bottom
        return min(by_height, by_padding, constants.POSTER_HEIGHT)
