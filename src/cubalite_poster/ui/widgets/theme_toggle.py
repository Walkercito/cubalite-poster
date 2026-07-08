"""An icon button that switches the application theme."""

import tkinter as tk
from tkinter import ttk

from cubalite_poster.ui.icons import IconRenderer
from cubalite_poster.ui.theme import ThemeController


class ThemeToggle(ttk.Button):
    """Toggles light/dark and shows the icon for the theme it switches to."""

    def __init__(
        self,
        master: tk.Misc,
        controller: ThemeController,
        icons: IconRenderer,
    ) -> None:
        super().__init__(master, command=controller.toggle, takefocus=False)
        self._controller = controller
        self._icons = icons
        controller.subscribe(self._on_theme_changed)
        self._on_theme_changed(controller.theme)

    def _on_theme_changed(self, theme: str) -> None:
        # Keep a reference on the instance so Tk does not discard the image.
        self._icon = self._icons.theme_toggle_icon(theme)
        self.configure(image=self._icon)
