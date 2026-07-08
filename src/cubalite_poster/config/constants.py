"""Single source of truth for fixed values (No Magic Values principle).

Every size, label, colour or theme name used by the UI is named here so that
call sites read as intent, not as arbitrary literals.
"""

from typing import Final

# --- Theme -----------------------------------------------------------------
# sv-ttk ships a "light" and a "dark" variant of the Sun-Valley theme.
THEME_MODE: Final[str] = "light"

# --- Window ----------------------------------------------------------------
WINDOW_TITLE: Final[str] = "Cubalite Poster"
WINDOW_WIDTH: Final[int] = 480
WINDOW_HEIGHT: Final[int] = 320
WINDOW_RESIZABLE: Final[bool] = False

# --- Layout ----------------------------------------------------------------
CONTENT_PADDING: Final[int] = 24
WIDGET_SPACING: Final[int] = 16

# --- Main view content -----------------------------------------------------
GREETING_TEXT: Final[str] = "Hello world!"
TOUCH_ME_BUTTON_TEXT: Final[str] = "Touch me"

# --- ttk styles ------------------------------------------------------------
# Style name provided by sv-ttk for accent (primary) buttons.
ACCENT_BUTTON_STYLE: Final[str] = "Accent.TButton"
