"""Locations of bundled assets.

Centralising the paths here keeps asset lookups DRY and free of hard-coded
directory names scattered across the code base.
"""

from pathlib import Path
from typing import Final

_PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent

ASSETS_DIR: Final[Path] = _PACKAGE_ROOT / "assets"
FONTS_DIR: Final[Path] = ASSETS_DIR / "fonts"
ICONS_DIR: Final[Path] = ASSETS_DIR / "icons"
