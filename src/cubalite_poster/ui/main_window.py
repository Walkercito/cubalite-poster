"""The main view of the application."""

import dearpygui.dearpygui as dpg

from cubalite_poster.config import constants
from cubalite_poster.ui.fonts import FontManager
from cubalite_poster.ui.theme import build_accent_theme


class MainWindow:
    """Root view: greeting and accent action button.

    A view is responsible only for building and wiring its own widgets. It
    holds no poster-generation logic — that belongs in ``core``.
    """

    def __init__(self, fonts: FontManager) -> None:
        self._fonts = fonts
        self._build()

    def _build(self) -> None:
        with dpg.window(
            tag=constants.TAG_PRIMARY_WINDOW,
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            no_close=True,
        ):
            dpg.add_spacer(height=constants.CONTENT_TOP_SPACER)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=constants.CONTENT_LEFT_SPACER)
                with dpg.group():
                    dpg.add_text(
                        constants.GREETING_TEXT,
                        tag=constants.TAG_GREETING,
                    )
                    self._fonts.bind_heading(constants.TAG_GREETING)

                    dpg.add_spacer(height=constants.WIDGET_SPACING)

                    dpg.add_button(
                        label=constants.TOUCH_ME_BUTTON_TEXT,
                        tag=constants.TAG_TOUCH_ME_BUTTON,
                        callback=self._on_touch_me,
                    )
                    dpg.bind_item_theme(
                        constants.TAG_TOUCH_ME_BUTTON,
                        build_accent_theme(),
                    )

    @staticmethod
    def _on_touch_me(*_args: object) -> None:
        """Placeholder action for the accent button."""
