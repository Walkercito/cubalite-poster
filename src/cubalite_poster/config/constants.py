"""Single source of truth for fixed values (No Magic Values principle).

Every size, label, colour or theme name used by the UI is named here so that
call sites read as intent, not as arbitrary literals.
"""

from typing import Final

# --- Application identity --------------------------------------------------
APP_SLUG: Final[str] = "cubalite-poster"

# --- Window ----------------------------------------------------------------
WINDOW_TITLE: Final[str] = "Cubalite Poster"
WINDOW_WIDTH: Final[int] = 480
WINDOW_HEIGHT: Final[int] = 320
WINDOW_RESIZABLE: Final[bool] = False

# --- Layout ----------------------------------------------------------------
CONTENT_PADDING: Final[int] = 24
WIDGET_SPACING: Final[int] = 16

# --- Theme -----------------------------------------------------------------
# sv-ttk ships a "light" and a "dark" variant of the Sun-Valley theme.
THEME_LIGHT: Final[str] = "light"
THEME_DARK: Final[str] = "dark"
DEFAULT_THEME: Final[str] = THEME_LIGHT

# --- Typography ------------------------------------------------------------
# Geist is bundled in assets/fonts and registered with the OS at start-up.
# FALLBACK_FONT_FAMILY is used only if Geist cannot be resolved (e.g. a Tk
# build without TrueType support).
UI_FONT_FAMILY: Final[str] = "Geist"
FALLBACK_FONT_FAMILY: Final[str] = "Segoe UI"
BASE_FONT_SIZE: Final[int] = 11
HEADING_FONT_SIZE: Final[int] = 20
HEADING_FONT_WEIGHT: Final[str] = "bold"

# Tk named fonts shared by every ttk widget; retargeting them applies the UI
# font globally instead of per-widget (DRY).
NAMED_FONTS: Final[tuple[str, ...]] = (
    "TkDefaultFont",
    "TkTextFont",
    "TkMenuFont",
    "TkHeadingFont",
    "TkCaptionFont",
    "TkSmallCaptionFont",
    "TkIconFont",
    "TkTooltipFont",
)

# --- Main view content -----------------------------------------------------
GREETING_TEXT: Final[str] = "Hello world!"
TOUCH_ME_BUTTON_TEXT: Final[str] = "Touch me"

# --- ttk styles ------------------------------------------------------------
# Style name provided by sv-ttk for accent (primary) buttons.
ACCENT_BUTTON_STYLE: Final[str] = "Accent.TButton"

# --- Theme-toggle icon -----------------------------------------------------
ICON_SIZE: Final[int] = 20
# Icon colour must contrast with the button background of the active theme:
# a dark glyph on the light theme, a light glyph on the dark theme.
ICON_COLOR_ON_LIGHT: Final[str] = "#1c1c1c"
ICON_COLOR_ON_DARK: Final[str] = "#fafafa"

# Icons are pre-rasterised to PNG so they render on any Tk 8.6+ (the SVG photo
# format only exists in Tk 8.7+). The SVG sources remain the source of truth;
# regenerate the PNGs with `scripts/render_icons.py`.
MOON_ICON_FILE: Final[str] = "moon.png"
SUN_ICON_FILE: Final[str] = "sun.png"
