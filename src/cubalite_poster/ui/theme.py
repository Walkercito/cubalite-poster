"""Light/dark theme state and switching, on top of sv-ttk."""

from collections.abc import Callable

import sv_ttk

from cubalite_poster.config import constants

ThemeObserver = Callable[[str], None]


class ThemeController:
    """Owns the active theme and notifies observers when it changes.

    Views subscribe to react to theme changes (e.g. to swap an icon) without
    the controller needing to know about any specific widget.
    """

    def __init__(self, initial_theme: str = constants.DEFAULT_THEME) -> None:
        self._theme = initial_theme
        self._observers: list[ThemeObserver] = []

    @property
    def theme(self) -> str:
        return self._theme

    @property
    def is_dark(self) -> bool:
        return self._theme == constants.THEME_DARK

    def initialize(self) -> None:
        """Apply the initial theme to the Tk interpreter."""
        sv_ttk.set_theme(self._theme)

    def toggle(self) -> None:
        self._theme = constants.THEME_LIGHT if self.is_dark else constants.THEME_DARK
        sv_ttk.set_theme(self._theme)
        self._notify()

    def subscribe(self, observer: ThemeObserver) -> None:
        self._observers.append(observer)

    def _notify(self) -> None:
        for observer in self._observers:
            observer(self._theme)
