"""FontManager loads bundled Geist faces into a DearPyGUI font registry."""

import dearpygui.dearpygui as dpg

from cubalite_poster import resources
from cubalite_poster.config import constants
from cubalite_poster.ui.fonts import FontManager


def test_font_manager_loads_base_and_heading() -> None:
    dpg.create_context()
    try:
        fonts = FontManager(resources.FONTS_DIR)
        fonts.load()

        assert fonts.base_font is not None
        assert fonts.heading_font is not None
        assert dpg.does_item_exist(constants.TAG_BASE_FONT)
        assert dpg.does_item_exist(constants.TAG_HEADING_FONT)
    finally:
        dpg.destroy_context()


def test_font_manager_missing_dir_falls_back() -> None:
    dpg.create_context()
    try:
        fonts = FontManager(resources.FONTS_DIR / "does-not-exist")
        fonts.load()

        assert fonts.base_font is None
        assert fonts.heading_font is None
    finally:
        dpg.destroy_context()
