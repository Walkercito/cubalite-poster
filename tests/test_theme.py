"""Dark theme helpers build and bind DearPyGUI themes."""

import dearpygui.dearpygui as dpg

from cubalite_poster.config import constants
from cubalite_poster.ui.theme import apply_dark_theme, build_accent_theme


def test_apply_dark_theme_creates_global_theme() -> None:
    dpg.create_context()
    try:
        theme_id = apply_dark_theme()
        assert theme_id is not None
        assert dpg.does_item_exist(constants.TAG_GLOBAL_THEME)
    finally:
        dpg.destroy_context()


def test_build_accent_theme_creates_item_theme() -> None:
    dpg.create_context()
    try:
        theme_id = build_accent_theme()
        assert theme_id is not None
        assert dpg.does_item_exist(constants.TAG_ACCENT_THEME)
    finally:
        dpg.destroy_context()
