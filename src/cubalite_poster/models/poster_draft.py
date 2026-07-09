"""Mutable form state for the poster editor (UI-agnostic data only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cubalite_poster.config import constants
from cubalite_poster.core.colors import Rgb
from cubalite_poster.models.poster_style import PosterStyle


@dataclass
class PosterDraft:
    """What the operator is editing — maps to engine inputs + style."""

    headline: str = constants.POSTER_HEADLINE_DEFAULT
    # When True use solid fill_color; when False use image_path (if set).
    use_color_background: bool = True
    fill_color: Rgb = constants.POSTER_BACKGROUND_COLOR
    image_path: Path | None = None
    style: PosterStyle = field(default_factory=PosterStyle)
