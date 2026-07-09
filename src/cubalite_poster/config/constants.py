"""Single source of truth for fixed values (No Magic Values principle).

Every size, label, colour or tag used by the UI is named here so that
call sites read as intent, not as arbitrary literals.
"""

from typing import Final

# --- Application identity --------------------------------------------------
APP_SLUG: Final[str] = "cubalite-poster"

# --- Window / viewport -----------------------------------------------------
WINDOW_TITLE: Final[str] = "Cubalite Poster"
WINDOW_WIDTH: Final[int] = 480
WINDOW_HEIGHT: Final[int] = 320
WINDOW_RESIZABLE: Final[bool] = False

# --- Layout ----------------------------------------------------------------
CONTENT_PADDING: Final[int] = 24
WIDGET_SPACING: Final[int] = 16
# Approximate vertical offset so the greeting+button sit near center.
CONTENT_TOP_SPACER: Final[int] = 100
# Horizontal spacer for rough centering of the content group.
CONTENT_LEFT_SPACER: Final[int] = 140

# --- Typography ------------------------------------------------------------
# DPG sizes are in pixels (not Tk points). Bundled faces live in assets/fonts.
UI_FONT_FAMILY: Final[str] = "Geist"
BASE_FONT_FILE: Final[str] = "Geist-Regular.ttf"
HEADING_FONT_FILE: Final[str] = "Geist-Bold.ttf"
BASE_FONT_SIZE: Final[int] = 16
HEADING_FONT_SIZE: Final[int] = 22

# --- Main view content -----------------------------------------------------
GREETING_TEXT: Final[str] = "Hello world!"
TOUCH_ME_BUTTON_TEXT: Final[str] = "Touch me"

# --- DPG item tags ---------------------------------------------------------
TAG_PRIMARY_WINDOW: Final[str] = "primary_window"
TAG_GREETING: Final[str] = "greeting_text"
TAG_TOUCH_ME_BUTTON: Final[str] = "touch_me_button"
TAG_BASE_FONT: Final[str] = "font_base"
TAG_HEADING_FONT: Final[str] = "font_heading"
TAG_GLOBAL_THEME: Final[str] = "theme_global_dark"
TAG_ACCENT_THEME: Final[str] = "theme_accent_button"

# --- Dark theme colours (R, G, B, A) 0–255 ---------------------------------
COLOR_WINDOW_BG: Final[tuple[int, int, int, int]] = (30, 30, 30, 255)
COLOR_CHILD_BG: Final[tuple[int, int, int, int]] = (30, 30, 30, 255)
COLOR_TEXT: Final[tuple[int, int, int, int]] = (240, 240, 240, 255)
COLOR_BUTTON: Final[tuple[int, int, int, int]] = (55, 55, 55, 255)
COLOR_BUTTON_HOVERED: Final[tuple[int, int, int, int]] = (70, 70, 70, 255)
COLOR_BUTTON_ACTIVE: Final[tuple[int, int, int, int]] = (45, 45, 45, 255)
COLOR_BORDER: Final[tuple[int, int, int, int]] = (60, 60, 60, 255)
COLOR_FRAME_BG: Final[tuple[int, int, int, int]] = (45, 45, 45, 255)

# Accent (primary action) button
COLOR_ACCENT: Final[tuple[int, int, int, int]] = (0, 120, 212, 255)
COLOR_ACCENT_HOVERED: Final[tuple[int, int, int, int]] = (26, 140, 224, 255)
COLOR_ACCENT_ACTIVE: Final[tuple[int, int, int, int]] = (0, 98, 176, 255)
COLOR_ACCENT_TEXT: Final[tuple[int, int, int, int]] = (255, 255, 255, 255)

# --- Theme styles ----------------------------------------------------------
FRAME_ROUNDING: Final[float] = 4.0
WINDOW_BORDER_SIZE: Final[float] = 0.0
WINDOW_PADDING_X: Final[float] = 24.0
WINDOW_PADDING_Y: Final[float] = 24.0
ITEM_SPACING_X: Final[float] = 8.0
ITEM_SPACING_Y: Final[float] = 16.0
