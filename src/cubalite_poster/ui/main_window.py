"""The main view of the application."""

import tkinter as tk
from tkinter import ttk

from cubalite_poster.config import constants


class MainWindow(ttk.Frame):
    """Root view: a greeting label and the accent action button.

    A view is responsible only for building and wiring its own widgets. It
    holds no poster-generation logic — that belongs in ``core``.
    """

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=constants.CONTENT_PADDING)
        self._build()

    def _build(self) -> None:
        greeting = ttk.Label(self, text=constants.GREETING_TEXT)
        touch_me = ttk.Button(
            self,
            text=constants.TOUCH_ME_BUTTON_TEXT,
            style=constants.ACCENT_BUTTON_STYLE,
            command=self._on_touch_me,
        )

        greeting.pack(pady=(0, constants.WIDGET_SPACING))
        touch_me.pack()

        # Centre the content block within the window.
        self.pack(expand=True)

    def _on_touch_me(self) -> None:
        """Placeholder action for the accent button."""
