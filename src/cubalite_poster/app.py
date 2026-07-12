"""Application shell: DearPyGUI context, worker thread, manual render loop."""

from __future__ import annotations

import sys

import dearpygui.dearpygui as dpg

from cubalite_poster import resources, updater
from cubalite_poster.config import constants
from cubalite_poster.ui.fonts import FontManager
from cubalite_poster.ui.main_window import MainWindow
from cubalite_poster.ui.render_worker import RenderWorker
from cubalite_poster.ui.theme import apply_dark_theme


class App:
    """Wires fonts, theme, editor view, background renderer, and frame loop."""

    def __init__(self) -> None:
        dpg.create_context()

        self._fonts = FontManager(resources.FONTS_DIR)
        self._fonts.load()
        apply_dark_theme()

        self._worker = RenderWorker()
        self._worker.start()
        self._window = MainWindow(self._worker, self._fonts)

        self._configure_viewport()

        # Frozen builds check GitHub for a newer release in the background and
        # apply it on the next exit. No-op from a source checkout.
        self._update_notice_shown = False
        updater.start_background_check()

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
        try:
            while dpg.is_dearpygui_running():
                self._window.poll_results()
                self._maybe_show_update_notice()
                dpg.render_dearpygui_frame()
        finally:
            self._window.shutdown()
            self._worker.stop()
            dpg.destroy_context()
            # Last thing before exit: if a newer version finished downloading,
            # hand off to the detached swapper. Never raises.
            updater.launch_swapper_if_staged()

    def _maybe_show_update_notice(self) -> None:
        if self._update_notice_shown or not updater.update_is_ready():
            return
        self._window.show_update_ready()
        self._update_notice_shown = True


def main() -> None:
    # Hidden mode the swapper uses to prove a freshly-applied build launches.
    if constants.UPDATE_SELFCHECK_FLAG in sys.argv[1:]:
        raise SystemExit(updater.run_selfcheck())
    App().run()
