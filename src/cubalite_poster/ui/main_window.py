"""The main view of the application."""

import tkinter as tk
from tkinter import ttk

from cubalite_poster.config import constants
from cubalite_poster.ui.fonts import FontManager
from cubalite_poster.ui.icons import IconRenderer
from cubalite_poster.ui.theme import ThemeController
from cubalite_poster.ui.widgets.theme_toggle import ThemeToggle


class MainWindow(ttk.Frame):
    """Root view: the theme toggle, a greeting and the accent action button.

    A view is responsible only for building and wiring its own widgets. It
    holds no poster-generation logic — that belongs in ``core``.
    """

    def __init__(
        self,
        master: tk.Misc,
        fonts: FontManager,
        theme: ThemeController,
        icons: IconRenderer,
    ) -> None:
        super().__init__(master)
        self._fonts = fonts
        self._theme = theme
        self._icons = icons
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self) -> None:
        toggle = ThemeToggle(self, self._theme, self._icons)
        toggle.place(
            relx=1.0,
            x=-constants.CONTENT_PADDING,
            y=constants.CONTENT_PADDING,
            anchor="ne",
        )

        content = ttk.Frame(self)
        content.place(relx=0.5, rely=0.5, anchor="center")

        greeting = ttk.Label(
            content,
            text=constants.GREETING_TEXT,
            font=self._fonts.heading_font(),
        )
        touch_me = ttk.Button(
            content,
            text=constants.TOUCH_ME_BUTTON_TEXT,
            style=constants.ACCENT_BUTTON_STYLE,
            command=self._on_touch_me,
        )

        greeting.pack(pady=(0, constants.WIDGET_SPACING))
        touch_me.pack()

    def _on_touch_me(self) -> None:
        """Placeholder action for the accent button."""
