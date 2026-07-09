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
# Sample headline so the first preview is never blank.
POSTER_HEADLINE_DEFAULT: Final[str] = (
    "Lorem Ipsum es simplemente el texto de relleno "
    "de las imprentas y archivos de texto."
)

# Hex colour strings (CLI -c / --color) omit the leading '#'.
POSTER_HEX_COLOR_LENGTH: Final[int] = 6
# Empty path means “use the bundled default font file name from constants”.
POSTER_FONT_PATH_DEFAULT: Final[str] = ""

# --- Window / viewport -----------------------------------------------------
WINDOW_TITLE: Final[str] = "Cubalite Poster"
# Preview pane (~672) + inspector pane (fixed) + window chrome.
WINDOW_WIDTH: Final[int] = 1120
WINDOW_HEIGHT: Final[int] = 720
WINDOW_RESIZABLE: Final[bool] = True

# --- Layout (editor) -------------------------------------------------------
# Tight rhythm so Title sits close to its subtitle and control.
SECTION_GAP: Final[int] = 10
FIELD_GAP: Final[int] = 6
TIGHT_GAP: Final[int] = 2
# Optical gap inside a zero-ItemSpacing title stack (title → subtitle).
# Gap from the stack to the control uses global ITEM_SPACING_Y.
TITLE_TO_SUBTITLE_GAP: Final[int] = 2
# Padding *inside* the bordered form (left and right must match).
INSPECTOR_INNER_PAD: Final[int] = 16
# Strip to the right of the bordered form for the scrollbar only.
INSPECTOR_SCROLLBAR_WIDTH: Final[int] = 16
# Fixed width of the bordered form column (scrollbar is extra, outside).
INSPECTOR_PANE_WIDTH: Final[int] = 340
HEADLINE_INPUT_HEIGHT: Final[int] = 110
# Inset when soft-wrapping the headline field (frame pad + cursor room).
HEADLINE_INPUT_WRAP_INSET: Final[int] = 20
EXPORT_BUTTON_HEIGHT: Final[int] = 44
COLOR_SWATCH_WIDTH: Final[int] = 48
# Per-channel inputs next to the swatch (RVA = Rojo / Verde / Azul).
COLOR_CHANNEL_MIN: Final[int] = 0
COLOR_CHANNEL_MAX: Final[int] = 255
COLOR_CHANNEL_INPUT_WIDTH: Final[int] = 52
COLOR_CHANNEL_STEP: Final[int] = 0

# Live preview texture (fixed size for dpg dynamic_texture; 4:3).
PREVIEW_WIDTH: Final[int] = 640
PREVIEW_HEIGHT: Final[int] = 480
PREVIEW_DEBOUNCE_MS: Final[int] = 200

# --- Typography ------------------------------------------------------------
# Readable scale: section title (bold) > body > caption/hint (thin + muted).
UI_FONT_FAMILY: Final[str] = "Geist"
BASE_FONT_FILE: Final[str] = "Geist-Regular.ttf"
HEADING_FONT_FILE: Final[str] = "Geist-Bold.ttf"
BASE_FONT_SIZE: Final[int] = 16
SECTION_FONT_SIZE: Final[int] = 20
CAPTION_FONT_SIZE: Final[int] = 14
HEADING_FONT_SIZE: Final[int] = 22

# --- Editor copy (Spanish UI for operators) --------------------------------
LABEL_PREVIEW: Final[str] = "Vista previa"
LABEL_SECTION_TEXT: Final[str] = "Titular"
LABEL_SECTION_BACKGROUND: Final[str] = "Fondo"
LABEL_SECTION_ADVANCED: Final[str] = "Avanzado"
LABEL_SECTION_ADVANCED_HINT: Final[str] = "Ajustes opcionales"
LABEL_SHOW_OPTIONS: Final[str] = "Mostrar opciones"
LABEL_HEADLINE_HINT: Final[str] = "¿Qué debe decir el póster?"
LABEL_BG_COLOR: Final[str] = "Color sólido"
LABEL_BG_IMAGE: Final[str] = "Foto"
LABEL_CHOOSE_PHOTO: Final[str] = "Elegir foto…"
LABEL_CHANGE_PHOTO: Final[str] = "Cambiar foto…"
LABEL_NO_PHOTO: Final[str] = "Ninguna foto seleccionada"
LABEL_EXPORT: Final[str] = "Exportar PNG"
LABEL_STATUS_READY: Final[str] = "Vista previa actualizada"
LABEL_STATUS_RENDERING: Final[str] = "Actualizando vista previa…"
LABEL_STATUS_NOTHING_TO_EXPORT: Final[str] = (
    "Aún no hay nada que exportar — espera la vista previa."
)
LABEL_STATUS_SAVED: Final[str] = "Guardado {name}"
LABEL_STATUS_EXPORT_FAILED: Final[str] = "Error al exportar: {error}"
LABEL_STATUS_ERROR: Final[str] = "Error: {error}"
LABEL_ADV_WORDMARK: Final[str] = "Logotipo"
LABEL_ADV_GRADIENT: Final[str] = "Degradado"
LABEL_ADV_HEADLINE_STYLE: Final[str] = "Estilo del titular"
LABEL_WORDMARK_FILL: Final[str] = "Relleno"
LABEL_WORDMARK_STROKE: Final[str] = "Borde"
LABEL_GRADIENT_COLOR: Final[str] = "Color"
LABEL_HEADLINE_COLOR: Final[str] = "Color"
LABEL_HEADLINE_SIZE: Final[str] = "Tamaño"
LABEL_HEADLINE_MAX_LINES: Final[str] = "Líneas máximas"
LABEL_PADDING_BOTTOM: Final[str] = "Margen inferior"
LABEL_AUTO_FIT: Final[str] = "Ajustar texto al espacio"
# RVA = Rojo / Verde / Azul (Spanish for RGB).
LABEL_CHANNEL_R: Final[str] = "R"
LABEL_CHANNEL_V: Final[str] = "V"
LABEL_CHANNEL_A: Final[str] = "A"
TAG_CHANNEL_R_SUFFIX: Final[str] = "_r"
TAG_CHANNEL_V_SUFFIX: Final[str] = "_v"
TAG_CHANNEL_A_SUFFIX: Final[str] = "_a"

DIALOG_OPEN_IMAGE_TITLE: Final[str] = "Elegir foto de fondo"
DIALOG_SAVE_POSTER_TITLE: Final[str] = "Exportar póster como PNG"
IMAGE_FILETYPES: Final[tuple[tuple[str, str], ...]] = (
    ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp *.gif"),
    ("Todos los archivos", "*.*"),
)
PNG_FILETYPES: Final[tuple[tuple[str, str], ...]] = (
    ("Imagen PNG", "*.png"),
    ("Todos los archivos", "*.*"),
)

# --- DPG item tags ---------------------------------------------------------
TAG_PRIMARY_WINDOW: Final[str] = "primary_window"
TAG_BASE_FONT: Final[str] = "font_base"
TAG_HEADING_FONT: Final[str] = "font_heading"
TAG_SECTION_FONT: Final[str] = "font_section"
TAG_CAPTION_FONT: Final[str] = "font_caption"
TAG_GLOBAL_THEME: Final[str] = "theme_global_dark"
TAG_ACCENT_THEME: Final[str] = "theme_accent_button"
TAG_PREVIEW_TEXTURE: Final[str] = "preview_texture"
TAG_PREVIEW_IMAGE: Final[str] = "preview_image"
TAG_PREVIEW_PANE: Final[str] = "preview_pane"
TAG_PREVIEW_TOP_SPACER: Final[str] = "preview_top_spacer"
TAG_PREVIEW_LEFT_SPACER: Final[str] = "preview_left_spacer"
TAG_PREVIEW_CONTENT: Final[str] = "preview_content"
TAG_HEADLINE_INPUT: Final[str] = "headline_input"
TAG_BG_MODE: Final[str] = "bg_mode"
TAG_BG_COLOR_PANEL: Final[str] = "bg_color_panel"
TAG_BG_IMAGE_PANEL: Final[str] = "bg_image_panel"
TAG_BG_COLOR: Final[str] = "bg_color"
TAG_BG_IMAGE_NAME: Final[str] = "bg_image_name"
TAG_BG_IMAGE_PATH: Final[str] = "bg_image_path"
TAG_CHOOSE_PHOTO_BUTTON: Final[str] = "choose_photo_button"
TAG_ADVANCED_HEADER: Final[str] = "advanced_header"
TAG_EXPORT_BUTTON: Final[str] = "export_button"
TAG_STATUS_TEXT: Final[str] = "status_text"
TAG_ADV_WORDMARK_FILL: Final[str] = "adv_wordmark_fill"
TAG_ADV_WORDMARK_STROKE: Final[str] = "adv_wordmark_stroke"
TAG_ADV_GRADIENT_COLOR: Final[str] = "adv_gradient_color"
TAG_ADV_HEADLINE_COLOR: Final[str] = "adv_headline_color"
TAG_ADV_HEADLINE_SIZE: Final[str] = "adv_headline_size"
TAG_ADV_HEADLINE_MAX_LINES: Final[str] = "adv_headline_max_lines"
TAG_ADV_PADDING_BOTTOM: Final[str] = "adv_padding_bottom"
TAG_ADV_AUTO_FIT: Final[str] = "adv_auto_fit"

BG_MODE_COLOR: Final[str] = "color"
BG_MODE_IMAGE: Final[str] = "image"

# --- Dark theme colours (R, G, B, A) 0–255 ---------------------------------
COLOR_WINDOW_BG: Final[tuple[int, int, int, int]] = (30, 30, 30, 255)
COLOR_CHILD_BG: Final[tuple[int, int, int, int]] = (30, 30, 30, 255)
COLOR_TEXT: Final[tuple[int, int, int, int]] = (240, 240, 240, 255)
# Secondary copy (subtitles/hints) — thinner visual weight than body text.
COLOR_TEXT_MUTED: Final[tuple[int, int, int, int]] = (160, 160, 160, 255)
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
FRAME_PADDING_X: Final[float] = 12.0
FRAME_PADDING_Y: Final[float] = 8.0
WINDOW_BORDER_SIZE: Final[float] = 0.0
WINDOW_PADDING_X: Final[float] = 12.0
WINDOW_PADDING_Y: Final[float] = 12.0
ITEM_SPACING_X: Final[float] = 8.0
# Keep vertical rhythm tight so section titles don't float above subtitles.
ITEM_SPACING_Y: Final[float] = 4.0
CELL_PADDING_X: Final[float] = 10.0
CELL_PADDING_Y: Final[float] = 8.0
