"""Locations of bundled assets.

Centralising the paths here keeps asset lookups DRY and free of hard-coded
directory names scattered across the code base.

When frozen with PyInstaller, assets live under ``sys._MEIPASS``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final


def _package_root() -> Path:
    """Return the install/package root (source tree or frozen extract dir)."""
    if getattr(sys, "frozen", False):
        # PyInstaller one-dir / one-file: datas are extracted under _MEIPASS.
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass is not None:
            return Path(meipass) / "cubalite_poster"
    return Path(__file__).resolve().parent


_PACKAGE_ROOT: Final[Path] = _package_root()

ASSETS_DIR: Final[Path] = _PACKAGE_ROOT / "assets"
FONTS_DIR: Final[Path] = ASSETS_DIR / "fonts"
