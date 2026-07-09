"""Single source of truth for fixed values (No Magic Values principle).

Every size, label, colour or tag used by the UI is named here so that
call sites read as intent, not as arbitrary literals.
"""

from typing import Final

# --- Application identity --------------------------------------------------
APP_SLUG: Final[str] = "cubalite-poster"

# --- Poster canvas (engine; UI-agnostic) ------------------------------------
# Fixed 4:3 output size — matches Figma Post component (node 5:151).
POSTER_WIDTH: Final[int] = 1152
POSTER_HEIGHT: Final[int] = 864
POSTER_ASPECT_RATIO: Final[tuple[int, int]] = (4, 3)
POSTER_COLOR_MODE: Final[str] = "RGB"
POSTER_COLOR_MODE_RGBA: Final[str] = "RGBA"
# Layer 1 image-slot fill when no -i/--image is supplied (the “white fill”).
# Overridable via CLI -c / --color (RRGGBB without '#').
# If both -i and -c are passed, the first flag on the command line wins.
POSTER_BACKGROUND_COLOR: Final[tuple[int, int, int]] = (255, 255, 255)
# Empty by default; pass -i / --image with a filesystem path for FILL.
POSTER_IMAGE_DEFAULT: Final[str] = ""
POSTER_OUTPUT_FORMAT: Final[str] = "PNG"
POSTER_DEFAULT_FILENAME: Final[str] = "poster.png"

# Layer order on Post (bottom → top), Figma node 5:151:
#   1) IMAGE FILL (background image placeholder, or solid colour)
#   2) black GRADIENT_LINEAR
#   3) Cubalite badge (children paint after fills; fixed cream fill)
#   4) Headline text (“Noticia”) — fixed width, bottom-capped

# Post content insets (auto-layout padding on the component).
POSTER_CONTENT_PADDING_LEFT: Final[int] = 45
POSTER_CONTENT_PADDING_RIGHT: Final[int] = 243
POSTER_CONTENT_PADDING_BOTTOM: Final[int] = 107
POSTER_CONTENT_ITEM_SPACING: Final[int] = 10

# Layer 2 — bottom scrim (GRADIENT_LINEAR on Post).
# Vertical black fade for headline legibility. Transparent through mid-frame,
# full black past the bottom edge (to 120.2% of height so the bottom is dark).
POSTER_GRADIENT_RGB: Final[tuple[int, int, int]] = (0, 0, 0)
POSTER_GRADIENT_START_Y: Final[float] = 0.5
POSTER_GRADIENT_END_Y: Final[float] = 1.202
POSTER_GRADIENT_ALPHA_START: Final[int] = 0
POSTER_GRADIENT_ALPHA_END: Final[int] = 255

# Layer 3 — Cubalite brand badge (child frame "Cubalite", node 4:11).
# Drawn *above* photo + scrim so the light fill stays fully visible.
POSTER_BADGE_X: Final[int] = 45
POSTER_BADGE_Y: Final[int] = 600  # Figma y ≈ 599.5
POSTER_BADGE_WIDTH: Final[int] = 203
POSTER_BADGE_HEIGHT: Final[int] = 61
POSTER_BADGE_FILL: Final[tuple[int, int, int]] = (254, 247, 236)  # #FEF7EC
POSTER_BADGE_STROKE: Final[tuple[int, int, int]] = (0, 0, 0)
POSTER_BADGE_STROKE_WIDTH: Final[int] = 1
POSTER_BADGE_LABEL: Final[str] = "Cubalite"
POSTER_BADGE_FONT_FILE: Final[str] = "LibreBaskerville-Bold.ttf"
POSTER_BADGE_FONT_SIZE: Final[int] = 40
POSTER_BADGE_TEXT_COLOR: Final[tuple[int, int, int]] = (0, 0, 0)

# Layer 4 — headline (text node "Noticia", 4:3).
# Fixed width = canvas − left − right padding (864). Vertical box starts
# below the badge (+ item spacing). Height matches the Figma text frame
# (100px), which reaches the lower content edge used as the height limit.
POSTER_HEADLINE_X: Final[int] = POSTER_CONTENT_PADDING_LEFT
POSTER_HEADLINE_WIDTH: Final[int] = (
    POSTER_WIDTH - POSTER_CONTENT_PADDING_LEFT - POSTER_CONTENT_PADDING_RIGHT
)
# Figma Noticia node height — room for two 40px lines of Libre Baskerville.
POSTER_HEADLINE_MAX_HEIGHT: Final[int] = 100
POSTER_HEADLINE_MAX_LINES: Final[int] = 2
POSTER_HEADLINE_FONT_FILE: Final[str] = "LibreBaskerville-Bold.ttf"
POSTER_HEADLINE_FONT_SIZE: Final[int] = 40
POSTER_HEADLINE_MIN_FONT_SIZE: Final[int] = 18
# When True, shrink headline size so text fits within max_lines × box height.
POSTER_HEADLINE_AUTO_FIT: Final[bool] = True
POSTER_HEADLINE_COLOR: Final[tuple[int, int, int]] = (255, 255, 255)
# Empty by default; pass -t / --text to set the headline.
POSTER_HEADLINE_DEFAULT: Final[str] = ""

# Hex colour strings (CLI -c / --color) omit the leading '#'.
POSTER_HEX_COLOR_LENGTH: Final[int] = 6
# Empty path means “use the bundled default font file name from constants”.
POSTER_FONT_PATH_DEFAULT: Final[str] = ""

# --- Window / viewport -----------------------------------------------------
WINDOW_TITLE: Final[str] = "Cubalite Poster"
WINDOW_WIDTH: Final[int] = 920
WINDOW_HEIGHT: Final[int] = 620
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
BASE_FONT_SIZE: Final[int] = 24
HEADING_FONT_SIZE: Final[int] = 42

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
# Inner padding inside buttons/inputs (text ↔ frame edge).
FRAME_PADDING_X: Final[float] = 16.0
FRAME_PADDING_Y: Final[float] = 8.0
WINDOW_BORDER_SIZE: Final[float] = 0.0
WINDOW_PADDING_X: Final[float] = 24.0
WINDOW_PADDING_Y: Final[float] = 24.0
ITEM_SPACING_X: Final[float] = 8.0
ITEM_SPACING_Y: Final[float] = 16.0
