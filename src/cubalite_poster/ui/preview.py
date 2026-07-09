"""Preview texture helpers: PIL ↔ DearPyGUI dynamic texture."""

from __future__ import annotations

from PIL import Image

from cubalite_poster.config import constants


def blank_preview_rgba() -> list[float]:
    """Opaque dark-grey placeholder matching preview dimensions."""
    w = constants.PREVIEW_WIDTH
    h = constants.PREVIEW_HEIGHT
    # Slightly lighter than pure black so the empty state is visible.
    r = g = b = 40 / 255
    a = 1.0
    pixel = (r, g, b, a)
    return [c for _ in range(w * h) for c in pixel]


def pil_to_preview_floats(image: Image.Image) -> list[float]:
    """Downscale to the fixed preview size and flatten to float RGBA 0–1."""
    preview = image.convert("RGBA").resize(
        (constants.PREVIEW_WIDTH, constants.PREVIEW_HEIGHT),
        Image.Resampling.LANCZOS,
    )
    raw = preview.tobytes()
    return [byte / 255.0 for byte in raw]
