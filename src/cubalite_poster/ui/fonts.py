"""Registers the bundled Geist font with the OS and applies it to the UI.

Font loading is inherently platform-specific:

* **Windows** (the primary target): each face is registered privately for the
  process with ``AddFontResourceExW`` — no admin rights, no install.
* **POSIX / fontconfig** (Linux, XQuartz): faces are copied into the user font
  directory and the fontconfig cache is refreshed, so any Xft-enabled Tk can
  resolve them.

If the family cannot be resolved after loading, the UI falls back to
``FALLBACK_FONT_FAMILY`` instead of failing.
"""

import platform
import shutil
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont

from cubalite_poster.config import constants

_WINDOWS = "Windows"
_FR_PRIVATE = 0x10
_FONT_GLOB = "*.ttf"


class FontManager:
    """Loads the UI font and retargets Tk's named fonts to it."""

    def __init__(self, root: tk.Misc, fonts_dir: Path) -> None:
        self._root = root
        self._fonts_dir = fonts_dir
        self._family = constants.FALLBACK_FONT_FAMILY

    @property
    def family(self) -> str:
        """The font family actually in use (Geist, or the fallback)."""
        return self._family

    def load(self) -> None:
        """Register the bundled faces and resolve the usable family."""
        self._register_faces()
        if constants.UI_FONT_FAMILY in tkfont.families(self._root):
            self._family = constants.UI_FONT_FAMILY

    def apply(self) -> None:
        """Point every shared named font at the resolved family.

        Call after the theme is applied so these fonts are not overridden.
        """
        for name in constants.NAMED_FONTS:
            try:
                tkfont.nametofont(name).configure(
                    family=self._family, size=constants.BASE_FONT_SIZE
                )
            except tk.TclError:
                continue

    def heading_font(self) -> tuple[str, int, str]:
        return (
            self._family,
            constants.HEADING_FONT_SIZE,
            constants.HEADING_FONT_WEIGHT,
        )

    def _register_faces(self) -> None:
        if platform.system() == _WINDOWS:
            self._register_windows()
        else:
            self._register_fontconfig()

    def _register_windows(self) -> None:
        import ctypes

        gdi32 = ctypes.WinDLL("gdi32")  # ty: ignore[unresolved-attribute]
        for path in sorted(self._fonts_dir.glob(_FONT_GLOB)):
            gdi32.AddFontResourceExW(str(path), _FR_PRIVATE, 0)

    def _register_fontconfig(self) -> None:
        target = Path.home() / ".local" / "share" / "fonts" / constants.APP_SLUG
        try:
            target.mkdir(parents=True, exist_ok=True)
            for path in self._fonts_dir.glob(_FONT_GLOB):
                destination = target / path.name
                if not destination.exists():
                    shutil.copy2(path, destination)
            subprocess.run(
                ["fc-cache", "-f", str(target)],
                check=False,
                capture_output=True,
            )
        except (OSError, FileNotFoundError):
            # No fontconfig / unwritable home: fall back gracefully.
            return
