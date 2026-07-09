"""Application shell: owns the DearPyGUI context, viewport and lifecycle."""

import dearpygui.dearpygui as dpg

from cubalite_poster import resources
from cubalite_poster.config import constants
from cubalite_poster.ui.fonts import FontManager
from cubalite_poster.ui.main_window import MainWindow
from cubalite_poster.ui.theme import apply_dark_theme


class App:
    """Wires fonts, theme, main view and the viewport run loop."""

    def __init__(self) -> None:
        dpg.create_context()

        self._fonts = FontManager(resources.FONTS_DIR)
        self._fonts.load()
        apply_dark_theme()
        MainWindow(self._fonts)

        self._configure_viewport()

    def _configure_viewport(self) -> None:
        dpg.create_viewport(
            title=constants.WINDOW_TITLE,
            width=constants.WINDOW_WIDTH,
            height=constants.WINDOW_HEIGHT,
            resizable=constants.WINDOW_RESIZABLE,
        )
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(constants.TAG_PRIMARY_WINDOW, True)

    def run(self) -> None:
        dpg.start_dearpygui()
        dpg.destroy_context()


def main() -> None:
    App().run()
