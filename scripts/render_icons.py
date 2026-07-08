"""Rasterise the theme-toggle SVG icons to PNG.

Run with a Tk 8.7+ interpreter (the uv-managed CPython ships Tk 9):

    uv run python scripts/render_icons.py

The PNGs are what the app loads at runtime, so it works on Tk 8.6 too. Rerun
this whenever the SVG sources or the icon colour/size constants change.
"""

import tkinter as tk

from cubalite_poster import resources
from cubalite_poster.config import constants
from cubalite_poster.ui import icons

# (SVG source, tint colour, output file) for each rendered icon.
_TARGETS = (
    (icons.MOON_SVG, constants.ICON_COLOR_ON_LIGHT, constants.MOON_ICON_FILE),
    (icons.SUN_SVG, constants.ICON_COLOR_ON_DARK, constants.SUN_ICON_FILE),
)


def main() -> None:
    root = tk.Tk()
    root.withdraw()
    resources.ICONS_DIR.mkdir(parents=True, exist_ok=True)

    for svg, color, file_name in _TARGETS:
        tinted = svg.replace(icons.CURRENT_COLOR_TOKEN, color)
        image = tk.PhotoImage(
            data=tinted, format=f"svg -scaletoheight {constants.ICON_SIZE}"
        )
        destination = resources.ICONS_DIR / file_name
        image.write(str(destination), format="png")
        print(f"wrote {destination} ({image.width()}x{image.height()})")

    root.destroy()


if __name__ == "__main__":
    main()
