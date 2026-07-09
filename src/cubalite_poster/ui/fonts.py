"""Loads bundled Geist faces into DearPyGUI's font registry."""

from pathlib import Path

import dearpygui.dearpygui as dpg

from cubalite_poster.config import constants


class FontManager:
    """Registers UI fonts and exposes font item ids for binding."""

    def __init__(self, fonts_dir: Path) -> None:
        self._fonts_dir = fonts_dir
        self._base_font: int | str | None = None
        self._heading_font: int | str | None = None
        self._section_font: int | str | None = None
        self._caption_font: int | str | None = None

    @property
    def base_font(self) -> int | str | None:
        return self._base_font

    @property
    def heading_font(self) -> int | str | None:
        return self._heading_font

    def load(self) -> None:
        """Create a font registry and load Geist faces when files exist."""
        base_path = self._fonts_dir / constants.BASE_FONT_FILE
        heading_path = self._fonts_dir / constants.HEADING_FONT_FILE

        if not base_path.is_file() and not heading_path.is_file():
            return

        bold_path = heading_path if heading_path.is_file() else base_path
        regular_path = base_path if base_path.is_file() else heading_path

        with dpg.font_registry():
            if base_path.is_file():
                self._base_font = dpg.add_font(
                    str(base_path),
                    constants.BASE_FONT_SIZE,
                    tag=constants.TAG_BASE_FONT,
                )
            if heading_path.is_file():
                self._heading_font = dpg.add_font(
                    str(heading_path),
                    constants.HEADING_FONT_SIZE,
                    tag=constants.TAG_HEADING_FONT,
                )
            if bold_path.is_file():
                self._section_font = dpg.add_font(
                    str(bold_path),
                    constants.SECTION_FONT_SIZE,
                    tag=constants.TAG_SECTION_FONT,
                )
            if regular_path.is_file():
                self._caption_font = dpg.add_font(
                    str(regular_path),
                    constants.CAPTION_FONT_SIZE,
                    tag=constants.TAG_CAPTION_FONT,
                )

        if self._base_font is not None:
            dpg.bind_font(self._base_font)

    def bind_heading(self, item: int | str) -> None:
        """Bind the large heading face when available."""
        if self._heading_font is not None:
            dpg.bind_item_font(item, self._heading_font)

    def bind_section(self, item: int | str) -> None:
        """Bind the section title face (bold, larger than body)."""
        font = self._section_font or self._heading_font
        if font is not None:
            dpg.bind_item_font(item, font)

    def bind_caption(self, item: int | str) -> None:
        """Bind the smaller caption/hint face when available."""
        font = self._caption_font or self._base_font
        if font is not None:
            dpg.bind_item_font(item, font)
