"""Application shell: owns the root window, fonts and theme lifecycle."""

import tkinter as tk

from cubalite_poster import resources
from cubalite_poster.config import constants
from cubalite_poster.ui.fonts import FontManager
from cubalite_poster.ui.icons import IconRenderer
from cubalite_poster.ui.main_window import MainWindow
from cubalite_poster.ui.theme import ThemeController


class App:
    """Wires the Tk root, the Sun-Valley theme, the UI font and the view."""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._configure_window()

        self._fonts = FontManager(self._root, resources.FONTS_DIR)
        self._icons = IconRenderer()
        self._theme = ThemeController()

        # Load fonts, apply the theme, then bind fonts to the widgets. Fonts
        # are applied last so the theme cannot override them.
        self._fonts.load()
        self._theme.initialize()
        self._fonts.apply()

        MainWindow(self._root, self._fonts, self._theme, self._icons)

    def _configure_window(self) -> None:
        self._root.title(constants.WINDOW_TITLE)
        self._root.geometry(f"{constants.WINDOW_WIDTH}x{constants.WINDOW_HEIGHT}")
        self._root.resizable(constants.WINDOW_RESIZABLE, constants.WINDOW_RESIZABLE)

    def run(self) -> None:
        self._root.mainloop()


def main() -> None:
    App().run()
