"""Fixed dark theme for the application shell."""

import dearpygui.dearpygui as dpg

from cubalite_poster.config import constants


def apply_dark_theme() -> int | str:
    """Build the global dark theme, bind it, and return its id."""
    with (
        dpg.theme(tag=constants.TAG_GLOBAL_THEME) as theme_id,
        dpg.theme_component(dpg.mvAll),
    ):
        dpg.add_theme_color(
            dpg.mvThemeCol_WindowBg,
            constants.COLOR_WINDOW_BG,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_ChildBg,
            constants.COLOR_CHILD_BG,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_Text,
            constants.COLOR_TEXT,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_Button,
            constants.COLOR_BUTTON,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_ButtonHovered,
            constants.COLOR_BUTTON_HOVERED,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_ButtonActive,
            constants.COLOR_BUTTON_ACTIVE,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_Border,
            constants.COLOR_BORDER,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_FrameBg,
            constants.COLOR_FRAME_BG,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_style(
            dpg.mvStyleVar_FrameRounding,
            constants.FRAME_ROUNDING,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_style(
            dpg.mvStyleVar_FramePadding,
            constants.FRAME_PADDING_X,
            constants.FRAME_PADDING_Y,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_style(
            dpg.mvStyleVar_WindowBorderSize,
            constants.WINDOW_BORDER_SIZE,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_style(
            dpg.mvStyleVar_WindowPadding,
            constants.WINDOW_PADDING_X,
            constants.WINDOW_PADDING_Y,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_style(
            dpg.mvStyleVar_ItemSpacing,
            constants.ITEM_SPACING_X,
            constants.ITEM_SPACING_Y,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_style(
            dpg.mvStyleVar_CellPadding,
            constants.CELL_PADDING_X,
            constants.CELL_PADDING_Y,
            category=dpg.mvThemeCat_Core,
        )

    dpg.bind_theme(theme_id)
    return theme_id


def build_accent_theme() -> int | str:
    """Theme for the primary action button (does not bind globally)."""
    with (
        dpg.theme(tag=constants.TAG_ACCENT_THEME) as theme_id,
        dpg.theme_component(dpg.mvButton),
    ):
        dpg.add_theme_color(
            dpg.mvThemeCol_Button,
            constants.COLOR_ACCENT,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_ButtonHovered,
            constants.COLOR_ACCENT_HOVERED,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_ButtonActive,
            constants.COLOR_ACCENT_ACTIVE,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_color(
            dpg.mvThemeCol_Text,
            constants.COLOR_ACCENT_TEXT,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_style(
            dpg.mvStyleVar_FrameRounding,
            constants.FRAME_ROUNDING,
            category=dpg.mvThemeCat_Core,
        )
        dpg.add_theme_style(
            dpg.mvStyleVar_FramePadding,
            constants.FRAME_PADDING_X,
            constants.FRAME_PADDING_Y,
            category=dpg.mvThemeCat_Core,
        )
    return theme_id


def build_inspector_theme() -> int | str:
    """Equal inner L/R/T/B padding for the bordered inspector form.

    ImGui applies WindowPadding on every side of a child window. Using it
    (instead of left-only spacer rows) is what keeps the right inset intact.
    """
    pad = constants.INSPECTOR_INNER_PAD
    with dpg.theme() as theme_id, dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(
            dpg.mvStyleVar_WindowPadding,
            pad,
            pad,
            category=dpg.mvThemeCat_Core,
        )
    return theme_id


def build_zero_pad_theme() -> int | str:
    """No WindowPadding — for layout chrome like the inspector scroll track."""
    with dpg.theme() as theme_id, dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(
            dpg.mvStyleVar_WindowPadding,
            0,
            0,
            category=dpg.mvThemeCat_Core,
        )
    return theme_id


def build_tight_stack_theme() -> int | str:
    """Zero vertical ItemSpacing so title/subtitle stacks stay compact.

    Global ITEM_SPACING_Y otherwise inserts a gap between every text line and
    spacer, which makes Title → Subtitle look double-spaced.
    """
    with dpg.theme() as theme_id, dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(
            dpg.mvStyleVar_ItemSpacing,
            constants.ITEM_SPACING_X,
            0,
            category=dpg.mvThemeCat_Core,
        )
    return theme_id


def build_zero_item_spacing_theme() -> int | str:
    """No ItemSpacing — for centering spacers that must sit flush against content."""
    with dpg.theme() as theme_id, dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(
            dpg.mvStyleVar_ItemSpacing,
            0,
            0,
            category=dpg.mvThemeCat_Core,
        )
    return theme_id
