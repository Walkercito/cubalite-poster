"""Editor main view: preview left, stepped inspector right."""

from __future__ import annotations

import threading
from dataclasses import replace
from pathlib import Path

import dearpygui.dearpygui as dpg
from PIL import Image, ImageDraw, ImageFont

from cubalite_poster import resources
from cubalite_poster.config import constants
from cubalite_poster.core.colors import Rgb
from cubalite_poster.core.text import wrap_text
from cubalite_poster.models import PosterDraft
from cubalite_poster.ui.fonts import FontManager
from cubalite_poster.ui.native_dialogs import ask_open_image, ask_save_poster
from cubalite_poster.ui.preview import blank_preview_rgba
from cubalite_poster.ui.render_worker import RenderJob, RenderResult, RenderWorker
from cubalite_poster.ui.theme import (
    build_accent_theme,
    build_inspector_theme,
    build_tight_stack_theme,
    build_zero_item_spacing_theme,
    build_zero_pad_theme,
)


class MainWindow:
    """Canvas-left / inspector-right editor for non-technical operators."""

    def __init__(self, worker: RenderWorker, fonts: FontManager) -> None:
        self._worker = worker
        self._fonts = fonts
        self._draft = PosterDraft()
        self._generation_id = 0
        self._last_full_image: Image.Image | None = None
        self._debounce_timer: threading.Timer | None = None
        self._debounce_lock = threading.Lock()
        self._tight_stack_theme: int | str | None = None
        self._zero_item_spacing_theme: int | str | None = None
        self._preview_left_pad = -1
        self._preview_top_pad = -1
        self._headline_input_width = -1
        self._headline_wrap_font: (
            ImageFont.FreeTypeFont | ImageFont.ImageFont | None
        ) = None
        self._headline_wrap_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        self._build()
        self._apply_bg_mode_visibility(use_image=False)
        self._schedule_render()

    def poll_results(self) -> None:
        """Called each frame from the App render loop (UI thread only)."""
        self._center_preview()
        self._sync_headline_wrap_if_resized()
        result = self._worker.poll()
        if result is None:
            return
        if result.generation_id < self._generation_id:
            return
        self._apply_result(result)

    def shutdown(self) -> None:
        with self._debounce_lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
                self._debounce_timer = None

    def _build(self) -> None:
        self._build_texture()
        self._tight_stack_theme = build_tight_stack_theme()
        self._zero_item_spacing_theme = build_zero_item_spacing_theme()
        with (
            dpg.window(
                tag=constants.TAG_PRIMARY_WINDOW,
                no_title_bar=True,
                no_collapse=True,
                no_close=True,
                no_move=True,
            ),
            dpg.group(horizontal=True),
        ):
            self._build_preview_panel()
            self._build_inspector_panel()

    def _build_texture(self) -> None:
        with dpg.texture_registry():
            dpg.add_dynamic_texture(
                width=constants.PREVIEW_WIDTH,
                height=constants.PREVIEW_HEIGHT,
                default_value=blank_preview_rgba(),
                tag=constants.TAG_PREVIEW_TEXTURE,
            )

    def _build_preview_panel(self) -> None:
        """Poster canvas centered in the remaining space left of the inspector."""
        inspector_total = (
            constants.INSPECTOR_PANE_WIDTH + constants.INSPECTOR_SCROLLBAR_WIDTH
        )
        with (
            dpg.child_window(
                width=-inspector_total,
                autosize_y=True,
                border=True,
                horizontal_scrollbar=False,
                tag=constants.TAG_PREVIEW_PANE,
            ),
            dpg.group() as outer,
        ):
            if self._zero_item_spacing_theme is not None:
                dpg.bind_item_theme(outer, self._zero_item_spacing_theme)
            dpg.add_spacer(height=0, tag=constants.TAG_PREVIEW_TOP_SPACER)
            with dpg.group(horizontal=True) as row:
                if self._zero_item_spacing_theme is not None:
                    dpg.bind_item_theme(row, self._zero_item_spacing_theme)
                dpg.add_spacer(width=0, tag=constants.TAG_PREVIEW_LEFT_SPACER)
                with dpg.group(tag=constants.TAG_PREVIEW_CONTENT):
                    label = dpg.add_text(constants.LABEL_PREVIEW)
                    self._fonts.bind_section(label)
                    dpg.add_spacer(height=constants.FIELD_GAP)
                    dpg.add_image(
                        constants.TAG_PREVIEW_TEXTURE,
                        tag=constants.TAG_PREVIEW_IMAGE,
                        width=constants.PREVIEW_WIDTH,
                        height=constants.PREVIEW_HEIGHT,
                    )
                    dpg.add_spacer(height=constants.TIGHT_GAP)
                    dpg.add_text(
                        constants.LABEL_STATUS_READY,
                        tag=constants.TAG_STATUS_TEXT,
                    )

    def _center_preview(self) -> None:
        """Keep the preview block centered as the window resizes."""
        pane = constants.TAG_PREVIEW_PANE
        content = constants.TAG_PREVIEW_CONTENT
        if not dpg.does_item_exist(pane) or not dpg.does_item_exist(content):
            return

        pane_w, pane_h = dpg.get_item_rect_size(pane)
        content_w, content_h = dpg.get_item_rect_size(content)
        if pane_w <= 0 or pane_h <= 0 or content_w <= 0 or content_h <= 0:
            return

        # Content region is inset by the child window's padding.
        inner_w = max(0.0, pane_w - 2 * constants.WINDOW_PADDING_X)
        inner_h = max(0.0, pane_h - 2 * constants.WINDOW_PADDING_Y)
        left = max(0, int((inner_w - content_w) / 2))
        top = max(0, int((inner_h - content_h) / 2))

        if left != self._preview_left_pad:
            dpg.configure_item(constants.TAG_PREVIEW_LEFT_SPACER, width=left)
            self._preview_left_pad = left
        if top != self._preview_top_pad:
            dpg.configure_item(constants.TAG_PREVIEW_TOP_SPACER, height=top)
            self._preview_top_pad = top

    def _build_inspector_panel(self) -> None:
        """Bordered form with equal inner L/R pad; scrollbar outside the box.

        Padding comes from WindowPadding on the pane theme (all four sides),
        so the right inset matches the left. Scrollbar track sits outside.
        """
        form_w = constants.INSPECTOR_PANE_WIDTH
        track_w = form_w + constants.INSPECTOR_SCROLLBAR_WIDTH

        with dpg.child_window(
            width=track_w,
            autosize_y=True,
            border=False,
            horizontal_scrollbar=False,
            tag="inspector_scroll",
        ):
            # No outer padding so the bordered form + scrollbar track align flush.
            dpg.bind_item_theme("inspector_scroll", build_zero_pad_theme())
            with dpg.child_window(
                width=form_w,
                border=True,
                auto_resize_y=True,
                horizontal_scrollbar=False,
                tag="inspector_pane",
            ):
                dpg.bind_item_theme("inspector_pane", build_inspector_theme())
                self._section_headline()
                self._divider()
                self._section_background()
                self._divider()
                self._section_advanced()
                self._divider()
                self._section_export()

    def _divider(self) -> None:
        dpg.add_spacer(height=constants.SECTION_GAP)
        dpg.add_separator()
        dpg.add_spacer(height=constants.SECTION_GAP)

    def _section_title(self, text: str) -> None:
        """Section title — larger bold face."""
        item = dpg.add_text(text)
        self._fonts.bind_section(item)

    def _subtitle(self, text: str) -> None:
        """Section subtitle — smaller regular face, muted colour."""
        item = dpg.add_text(text, color=constants.COLOR_TEXT_MUTED)
        self._fonts.bind_caption(item)

    def _title_block(self, title: str, subtitle: str | None = None) -> None:
        """Compact title stack: Title / Subtitle, then control via item spacing.

        Zero vertical ItemSpacing inside the group so global spacing cannot
        double-space title → subtitle. The next widget (the control) still
        gets the normal ITEM_SPACING_Y gap after the group.
        """
        with dpg.group() as block:
            if self._tight_stack_theme is not None:
                dpg.bind_item_theme(block, self._tight_stack_theme)
            self._section_title(title)
            if subtitle:
                dpg.add_spacer(height=constants.TITLE_TO_SUBTITLE_GAP)
                self._subtitle(subtitle)

    def _field_label(self, text: str) -> None:
        """Label stacked tightly above its control."""
        with dpg.group() as block:
            if self._tight_stack_theme is not None:
                dpg.bind_item_theme(block, self._tight_stack_theme)
            dpg.add_text(text)
            dpg.add_spacer(height=constants.TIGHT_GAP)

    def _color_row(
        self,
        label: str,
        tag: str,
        rgba: tuple[int, ...],
        *,
        channels: bool = False,
    ) -> None:
        """Colour control: swatch only, or swatch + RVA channel inputs."""
        if channels:
            self._color_row_with_channels(label, tag, rgba)
            return
        with dpg.group(horizontal=True):
            dpg.add_text(label)
            dpg.add_spacer(width=constants.FIELD_GAP)
            dpg.add_color_edit(
                default_value=rgba,
                tag=tag,
                no_alpha=True,
                no_inputs=True,
                no_label=True,
                width=constants.COLOR_SWATCH_WIDTH,
                callback=self._on_form_changed,
            )

    def _color_row_with_channels(
        self,
        label: str,
        tag: str,
        rgba: tuple[int, ...],
    ) -> None:
        """Label above a swatch + integer R/V/A fields (rojo / verde / azul)."""
        red = int(rgba[0])
        green = int(rgba[1])
        blue = int(rgba[2])
        self._field_label(label)
        with dpg.group(horizontal=True):
            dpg.add_color_edit(
                default_value=rgba,
                tag=tag,
                no_alpha=True,
                no_inputs=True,
                no_label=True,
                width=constants.COLOR_SWATCH_WIDTH,
                callback=self._on_color_swatch_changed,
                user_data=tag,
            )
            dpg.add_spacer(width=constants.FIELD_GAP)
            self._channel_input(
                tag,
                constants.TAG_CHANNEL_R_SUFFIX,
                constants.LABEL_CHANNEL_R,
                red,
            )
            self._channel_input(
                tag,
                constants.TAG_CHANNEL_V_SUFFIX,
                constants.LABEL_CHANNEL_V,
                green,
            )
            self._channel_input(
                tag,
                constants.TAG_CHANNEL_A_SUFFIX,
                constants.LABEL_CHANNEL_A,
                blue,
            )

    def _channel_input(
        self,
        color_tag: str,
        suffix: str,
        label: str,
        default: int,
    ) -> None:
        """One labelled integer channel (0–255) synced to a colour swatch."""
        dpg.add_text(label)
        dpg.add_input_int(
            default_value=default,
            tag=f"{color_tag}{suffix}",
            width=constants.COLOR_CHANNEL_INPUT_WIDTH,
            min_value=constants.COLOR_CHANNEL_MIN,
            max_value=constants.COLOR_CHANNEL_MAX,
            min_clamped=True,
            max_clamped=True,
            step=constants.COLOR_CHANNEL_STEP,
            callback=self._on_color_channel_changed,
            user_data=color_tag,
        )

    def _on_color_swatch_changed(
        self,
        _sender: object,
        _app_data: object,
        user_data: object,
    ) -> None:
        """Keep RVA fields in sync when the swatch/picker changes."""
        if not isinstance(user_data, str):
            return
        color_tag = user_data
        red, green, blue = _dpg_color_to_rgb(dpg.get_value(color_tag))
        dpg.set_value(f"{color_tag}{constants.TAG_CHANNEL_R_SUFFIX}", red)
        dpg.set_value(f"{color_tag}{constants.TAG_CHANNEL_V_SUFFIX}", green)
        dpg.set_value(f"{color_tag}{constants.TAG_CHANNEL_A_SUFFIX}", blue)
        self._on_form_changed()

    def _on_color_channel_changed(
        self,
        _sender: object,
        _app_data: object,
        user_data: object,
    ) -> None:
        """Push RVA field edits into the linked colour swatch."""
        if not isinstance(user_data, str):
            return
        color_tag = user_data
        red = _clamp_channel(
            dpg.get_value(f"{color_tag}{constants.TAG_CHANNEL_R_SUFFIX}")
        )
        green = _clamp_channel(
            dpg.get_value(f"{color_tag}{constants.TAG_CHANNEL_V_SUFFIX}")
        )
        blue = _clamp_channel(
            dpg.get_value(f"{color_tag}{constants.TAG_CHANNEL_A_SUFFIX}")
        )
        dpg.set_value(color_tag, (red, green, blue, 255))
        self._on_form_changed()

    def _slider_field(
        self,
        label: str,
        tag: str,
        *,
        default: int,
        min_value: int,
        max_value: int,
    ) -> None:
        """Label above full-width slider — side labels clip in narrow panes."""
        self._field_label(label)
        dpg.add_slider_int(
            default_value=default,
            min_value=min_value,
            max_value=max_value,
            tag=tag,
            width=-1,
            callback=self._on_form_changed,
        )

    def _section_headline(self) -> None:
        self._title_block(
            constants.LABEL_SECTION_TEXT,
            constants.LABEL_HEADLINE_HINT,
        )
        dpg.add_input_text(
            tag=constants.TAG_HEADLINE_INPUT,
            default_value=self._draft.headline,
            multiline=True,
            height=constants.HEADLINE_INPUT_HEIGHT,
            width=-1,
            # DPG has no native soft-wrap; we reflow in the callback.
            no_horizontal_scroll=True,
            callback=self._on_headline_changed,
        )

    def _on_headline_changed(self, *_args: object) -> None:
        """Soft-wrap the headline field, then refresh the poster draft."""
        self._apply_headline_soft_wrap()
        self._on_form_changed()

    def _sync_headline_wrap_if_resized(self) -> None:
        """Re-flow headline text when the input width changes."""
        if not dpg.does_item_exist(constants.TAG_HEADLINE_INPUT):
            return
        width = int(dpg.get_item_rect_size(constants.TAG_HEADLINE_INPUT)[0])
        if width <= 0 or width == self._headline_input_width:
            return
        self._headline_input_width = width
        self._apply_headline_soft_wrap()

    def _apply_headline_soft_wrap(self) -> None:
        """Reflow the headline input so long lines break inside the field.

        DearPyGUI multiline inputs do not soft-wrap; without this the cursor
        scrolls horizontally and typed text looks like a single line.
        """
        tag = constants.TAG_HEADLINE_INPUT
        if not dpg.does_item_exist(tag):
            return
        raw = dpg.get_value(tag)
        if not isinstance(raw, str):
            return
        wrapped = self._soft_wrap_for_input(raw)
        if wrapped != raw:
            dpg.set_value(tag, wrapped)

    def _soft_wrap_for_input(self, text: str) -> str:
        """Word-wrap ``text`` to the current headline input width."""
        width = int(dpg.get_item_rect_size(constants.TAG_HEADLINE_INPUT)[0])
        if width <= 0:
            return text
        max_width = max(
            1,
            width
            - int(2 * constants.FRAME_PADDING_X)
            - constants.HEADLINE_INPUT_WRAP_INSET,
        )
        font = self._get_headline_wrap_font()
        lines = wrap_text(self._headline_wrap_draw, text, font, max_width)
        return "\n".join(lines)

    def _get_headline_wrap_font(
        self,
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if self._headline_wrap_font is None:
            path = resources.FONTS_DIR / constants.BASE_FONT_FILE
            if path.is_file():
                self._headline_wrap_font = ImageFont.truetype(
                    str(path), constants.BASE_FONT_SIZE
                )
            else:
                self._headline_wrap_font = ImageFont.load_default()
        return self._headline_wrap_font

    def _section_background(self) -> None:
        self._title_block(constants.LABEL_SECTION_BACKGROUND)
        dpg.add_radio_button(
            items=[constants.LABEL_BG_COLOR, constants.LABEL_BG_IMAGE],
            default_value=constants.LABEL_BG_COLOR,
            horizontal=True,
            tag=constants.TAG_BG_MODE,
            callback=self._on_bg_mode_changed,
        )
        dpg.add_spacer(height=constants.FIELD_GAP)

        with dpg.group(tag=constants.TAG_BG_COLOR_PANEL, show=True):
            self._color_row(
                constants.LABEL_BG_COLOR,
                constants.TAG_BG_COLOR,
                (*self._draft.fill_color, 255),
            )

        with dpg.group(tag=constants.TAG_BG_IMAGE_PANEL, show=False):
            name = dpg.add_text(
                constants.LABEL_NO_PHOTO,
                tag=constants.TAG_BG_IMAGE_NAME,
            )
            self._fonts.bind_caption(name)
            dpg.add_input_text(
                tag=constants.TAG_BG_IMAGE_PATH,
                default_value="",
                show=False,
            )
            dpg.add_spacer(height=constants.TIGHT_GAP)
            dpg.add_button(
                label=constants.LABEL_CHOOSE_PHOTO,
                tag=constants.TAG_CHOOSE_PHOTO_BUTTON,
                width=-1,
                callback=self._on_choose_photo,
            )

    def _section_advanced(self) -> None:
        self._title_block(
            constants.LABEL_SECTION_ADVANCED,
            constants.LABEL_SECTION_ADVANCED_HINT,
        )
        with dpg.collapsing_header(
            label=constants.LABEL_SHOW_OPTIONS,
            tag=constants.TAG_ADVANCED_HEADER,
            default_open=False,
        ):
            style = self._draft.style
            dpg.add_spacer(height=constants.TIGHT_GAP)

            self._field_label(constants.LABEL_ADV_WORDMARK)
            self._color_row(
                constants.LABEL_WORDMARK_FILL,
                constants.TAG_ADV_WORDMARK_FILL,
                (*style.badge_fill, 255),
                channels=True,
            )
            self._color_row(
                constants.LABEL_WORDMARK_STROKE,
                constants.TAG_ADV_WORDMARK_STROKE,
                (*style.badge_stroke, 255),
                channels=True,
            )

            dpg.add_spacer(height=constants.FIELD_GAP)
            self._field_label(constants.LABEL_ADV_GRADIENT)
            self._color_row(
                constants.LABEL_GRADIENT_COLOR,
                constants.TAG_ADV_GRADIENT_COLOR,
                (*style.gradient_rgb, 255),
                channels=True,
            )

            dpg.add_spacer(height=constants.FIELD_GAP)
            self._field_label(constants.LABEL_ADV_HEADLINE_STYLE)
            self._color_row(
                constants.LABEL_HEADLINE_COLOR,
                constants.TAG_ADV_HEADLINE_COLOR,
                (*style.headline_color, 255),
                channels=True,
            )
            dpg.add_spacer(height=constants.FIELD_GAP)
            self._slider_field(
                constants.LABEL_HEADLINE_SIZE,
                constants.TAG_ADV_HEADLINE_SIZE,
                default=style.headline_font_size,
                min_value=style.headline_min_font_size,
                max_value=72,
            )
            dpg.add_spacer(height=constants.FIELD_GAP)
            self._slider_field(
                constants.LABEL_HEADLINE_MAX_LINES,
                constants.TAG_ADV_HEADLINE_MAX_LINES,
                default=style.headline_max_lines,
                min_value=1,
                max_value=6,
            )
            dpg.add_spacer(height=constants.FIELD_GAP)
            self._slider_field(
                constants.LABEL_PADDING_BOTTOM,
                constants.TAG_ADV_PADDING_BOTTOM,
                default=style.content_padding_bottom,
                min_value=0,
                max_value=300,
            )
            dpg.add_spacer(height=constants.FIELD_GAP)
            dpg.add_checkbox(
                label=constants.LABEL_AUTO_FIT,
                default_value=style.headline_auto_fit,
                tag=constants.TAG_ADV_AUTO_FIT,
                callback=self._on_form_changed,
            )

    def _section_export(self) -> None:
        dpg.add_button(
            label=constants.LABEL_EXPORT,
            tag=constants.TAG_EXPORT_BUTTON,
            width=-1,
            height=constants.EXPORT_BUTTON_HEIGHT,
            callback=self._on_export,
        )
        dpg.bind_item_theme(constants.TAG_EXPORT_BUTTON, build_accent_theme())

    def _on_form_changed(self, *_args: object) -> None:
        self._read_form_into_draft()
        self._schedule_render()

    def _on_bg_mode_changed(self, *_args: object) -> None:
        mode = dpg.get_value(constants.TAG_BG_MODE)
        use_image = mode == constants.LABEL_BG_IMAGE
        self._apply_bg_mode_visibility(use_image=use_image)
        self._on_form_changed()

    def _apply_bg_mode_visibility(self, *, use_image: bool) -> None:
        dpg.configure_item(constants.TAG_BG_COLOR_PANEL, show=not use_image)
        dpg.configure_item(constants.TAG_BG_IMAGE_PANEL, show=use_image)

    def _on_choose_photo(self, *_args: object) -> None:
        path = ask_open_image()
        if path is None:
            return
        dpg.set_value(constants.TAG_BG_IMAGE_PATH, str(path))
        dpg.set_value(constants.TAG_BG_IMAGE_NAME, path.name)
        dpg.set_value(constants.TAG_BG_MODE, constants.LABEL_BG_IMAGE)
        dpg.configure_item(
            constants.TAG_CHOOSE_PHOTO_BUTTON,
            label=constants.LABEL_CHANGE_PHOTO,
        )
        self._apply_bg_mode_visibility(use_image=True)
        self._on_form_changed()

    def _on_export(self, *_args: object) -> None:
        image = self._last_full_image
        if image is None:
            self._set_status(constants.LABEL_STATUS_NOTHING_TO_EXPORT)
            return
        path = ask_save_poster()
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path, format=constants.POSTER_OUTPUT_FORMAT)
            self._set_status(constants.LABEL_STATUS_SAVED.format(name=path.name))
        except OSError as exc:
            self._set_status(constants.LABEL_STATUS_EXPORT_FAILED.format(error=exc))

    def _read_form_into_draft(self) -> None:
        headline = dpg.get_value(constants.TAG_HEADLINE_INPUT)
        self._draft.headline = headline if isinstance(headline, str) else ""

        mode = dpg.get_value(constants.TAG_BG_MODE)
        self._draft.use_color_background = mode == constants.LABEL_BG_COLOR
        self._draft.fill_color = _dpg_color_to_rgb(
            dpg.get_value(constants.TAG_BG_COLOR)
        )

        path_val = dpg.get_value(constants.TAG_BG_IMAGE_PATH)
        if isinstance(path_val, str) and path_val.strip():
            self._draft.image_path = Path(path_val.strip()).expanduser()
        else:
            self._draft.image_path = None

        self._draft.style = replace(
            self._draft.style,
            badge_fill=_dpg_color_to_rgb(
                dpg.get_value(constants.TAG_ADV_WORDMARK_FILL)
            ),
            badge_stroke=_dpg_color_to_rgb(
                dpg.get_value(constants.TAG_ADV_WORDMARK_STROKE)
            ),
            gradient_rgb=_dpg_color_to_rgb(
                dpg.get_value(constants.TAG_ADV_GRADIENT_COLOR)
            ),
            headline_color=_dpg_color_to_rgb(
                dpg.get_value(constants.TAG_ADV_HEADLINE_COLOR)
            ),
            headline_font_size=int(dpg.get_value(constants.TAG_ADV_HEADLINE_SIZE)),
            headline_max_lines=int(dpg.get_value(constants.TAG_ADV_HEADLINE_MAX_LINES)),
            content_padding_bottom=int(dpg.get_value(constants.TAG_ADV_PADDING_BOTTOM)),
            headline_auto_fit=bool(dpg.get_value(constants.TAG_ADV_AUTO_FIT)),
        )

    def _schedule_render(self) -> None:
        delay = constants.PREVIEW_DEBOUNCE_MS / 1000.0

        def _fire() -> None:
            self._enqueue_render()

        with self._debounce_lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
            timer = threading.Timer(delay, _fire)
            timer.daemon = True
            self._debounce_timer = timer
            timer.start()

        self._set_status(constants.LABEL_STATUS_RENDERING)

    def _enqueue_render(self) -> None:
        self._generation_id += 1
        draft = self._draft
        image_path = (
            draft.image_path
            if not draft.use_color_background and draft.image_path is not None
            else None
        )
        self._worker.submit(
            RenderJob(
                generation_id=self._generation_id,
                headline=draft.headline,
                fill_color=draft.fill_color,
                image_path=image_path,
                style=draft.style,
            )
        )

    def _apply_result(self, result: RenderResult) -> None:
        dpg.set_value(constants.TAG_PREVIEW_TEXTURE, result.preview_floats)
        self._last_full_image = result.full_image
        if result.error:
            self._set_status(constants.LABEL_STATUS_ERROR.format(error=result.error))
        else:
            self._set_status(constants.LABEL_STATUS_READY)

    def _set_status(self, message: str) -> None:
        if dpg.does_item_exist(constants.TAG_STATUS_TEXT):
            dpg.set_value(constants.TAG_STATUS_TEXT, message)


def _dpg_color_to_rgb(value: object) -> Rgb:
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        return constants.POSTER_BACKGROUND_COLOR
    channels: list[int] = []
    for component in value[:3]:
        if isinstance(component, (int, float)):
            channels.append(_clamp_channel(component))
        else:
            return constants.POSTER_BACKGROUND_COLOR
    return (channels[0], channels[1], channels[2])


def _clamp_channel(value: object) -> int:
    if isinstance(value, (int, float)):
        return int(
            max(
                constants.COLOR_CHANNEL_MIN,
                min(constants.COLOR_CHANNEL_MAX, round(float(value))),
            )
        )
    return constants.COLOR_CHANNEL_MIN
