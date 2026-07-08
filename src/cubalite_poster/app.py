"""Application shell: owns the root window and the theme lifecycle."""

import tkinter as tk

import sv_ttk

from cubalite_poster.config import constants
from cubalite_poster.ui.main_window import MainWindow


class App:
    """Wires the Tk root, applies the Sun-Valley theme and mounts the view."""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._configure_window()
        sv_ttk.set_theme(constants.THEME_MODE)
        MainWindow(self._root)

    def _configure_window(self) -> None:
        self._root.title(constants.WINDOW_TITLE)
        self._root.geometry(f"{constants.WINDOW_WIDTH}x{constants.WINDOW_HEIGHT}")
        self._root.resizable(constants.WINDOW_RESIZABLE, constants.WINDOW_RESIZABLE)

    def run(self) -> None:
        self._root.mainloop()


def main() -> None:
    App().run()
