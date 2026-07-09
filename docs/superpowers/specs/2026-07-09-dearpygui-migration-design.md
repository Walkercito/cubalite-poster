# Design: Migrate UI from Tkinter to DearPyGUI

**Date:** 2026-07-09  
**Status:** Approved for planning  
**Scope:** 1:1 scaffold parity on DearPyGUI; dark theme only

## Context

Cubalite Poster is a desktop app that will generate on-brand news-channel
posters. Today the repo is a **scaffold**: a small themed window (Geist font,
greeting, accent button, light/dark toggle) built with Tkinter + Sun-Valley
(`sv-ttk`). Poster logic in `core/` / `models/` is empty.

This work replaces the GUI toolkit with [DearPyGUI](https://dearpygui.readthedocs.io/en/latest/)
while preserving the project’s OOP/DRY/No-Magic-Values principles and the
GUI-free boundary for `core/` and `models/`.

## Goals

1. Run the same operator-facing scaffold on DearPyGUI (window, greeting, accent
   button, Geist typography).
2. Use a **single dark theme** — no runtime theme switching.
3. Load Geist from bundled TTFs via DPG’s font registry (no OS font registration).
4. Remove all Tk / `sv-ttk` dependencies and related platform workarounds.
5. Keep the class-based shell so later poster views fit the same pattern.

## Non-goals

- Poster generation, form fields, or `core/` / `models/` implementation.
- Pixel-perfect Sun-Valley / Windows 11 styling.
- Light theme, theme toggle, or moon/sun icon UI.
- Dual Tk + DPG backends.
- New automated test suite (none exists today); quality gate remains ruff + ty.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Migration style | Surgical rewrite of `ui/` + `app.py` | Same module map and responsibilities; least churn for a scaffold |
| Visual fidelity | Functional parity, DPG-native dark look | Avoid reimplementing Sun-Valley |
| Font loading | DPG font registry only | DPG loads TTF directly; OS registration is unnecessary |
| Architecture | Class-based shell over DPG tags/IDs | Matches project OOP principles |
| Theme | Fixed dark only | Operator preference; simplifies UI and code |
| Icons | Remove toggle icons and pipeline | No theme toggle; YAGNI until poster UI needs images |

## Architecture

**Boundary (unchanged):** `core/` and `models/` never import DearPyGUI. The UI
depends on core when it exists; never the reverse.

### Lifecycle (`App`)

```
create_context()
  → FontManager.load()       # font_registry + Geist TTFs
  → apply_dark_theme()       # one global dark theme, bind once
  → MainWindow.build()       # primary window + widgets
  → create_viewport(...)     # title, size, non-resizable
  → setup_dearpygui()
  → show_viewport()
  → set_primary_window(...)
  → start_dearpygui()
  → destroy_context()
```

### Class / module map

| Piece | Responsibility under DPG |
|-------|---------------------------|
| `App` | Context, viewport, run loop; wires collaborators |
| `FontManager` | Load Geist sizes into a font registry; global `bind_font`; heading via `bind_item_font` |
| `apply_dark_theme()` | Build and bind a single dark global theme (`ui/theme.py`) |
| `MainWindow` | Primary window: greeting + accent “Touch me” button |

**Removed modules / types:**

- `ThemeController` (no theme state, no observers)
- `ThemeToggle`
- `IconRenderer`
- Theme-toggle icon assets and SVG sources used only for that toggle
- `scripts/render_icons.py` (only served the toggle PNG pipeline)

**Tags:** Stable string tags live as named constants (in `config/constants.py` or
a small `ui/tags.py` if constants becomes crowded), e.g. `TAG_PRIMARY_WINDOW`,
`TAG_GREETING`, `TAG_TOUCH_ME_BUTTON`. No bare tag strings at call sites.

### Folder structure after migration

```
src/cubalite_poster/
├── __init__.py
├── __main__.py
├── app.py                 # App: DPG context + viewport lifecycle
├── resources.py           # FONTS_DIR only (ICONS_DIR removed)
├── config/
│   └── constants.py       # window, layout, fonts, tags, labels, theme colours
├── ui/
│   ├── fonts.py           # FontManager (DPG font registry)
│   ├── theme.py           # apply_dark_theme() only
│   └── main_window.py     # MainWindow (no widgets/ package until needed)
├── core/                  # unchanged (empty, no GUI)
├── models/                # unchanged (empty, no GUI)
└── assets/
    └── fonts/             # Geist TTFs + OFL (assets/icons/ deleted)
```

## Theming

- One dark theme built with DPG theme colors and a few styles (e.g. frame
  rounding, window padding). Clean modern dark UI; not a Sun-Valley clone.
- Applied once at startup via `bind_theme`.
- Accent “Touch me” button: item-level theme (or theme component) so the
  primary action reads as accent against the dark chrome — equivalent intent to
  the old `Accent.TButton`, not the same stylesheet.

No light theme, no `toggle()`, no observer list.

## Fonts

- Load from `resources.FONTS_DIR`:
  - Base UI: `Geist-Regular.ttf` at `BASE_FONT_SIZE`
  - Heading: `Geist-Bold.ttf` at `HEADING_FONT_SIZE`
- Global `bind_font(base)`; greeting uses `bind_item_font(..., heading)`.
- If a face file is missing or load fails: fall back to DPG’s default font
  without crashing.
- **Delete** OS registration paths (Windows `AddFontResourceExW`, fontconfig
  copy + `fc-cache`), `NAMED_FONTS`, and Tk-specific fallback family wiring.
  A single constant for “we tried Geist” is enough; document default-font
  fallback in code comments if useful.

Geist works the same on Windows and Linux under DPG; drop README notes about
system Tk / Xft for the UI font.

## Main view

| Element | Behavior |
|---------|----------|
| Viewport | Title `WINDOW_TITLE`, size `WINDOW_WIDTH` × `WINDOW_HEIGHT`, non-resizable |
| Primary window | Fills viewport (primary window); app title on the viewport, not a second chrome bar if avoidable |
| Greeting | `GREETING_TEXT` (“Hello world!”), heading font, visually centered |
| Touch me | Accent-styled button; `_on_touch_me` remains a no-op placeholder |
| Theme toggle | **Absent** |

Layout uses DPG groups/spacers (and positioning only if needed) without a heavy
layout framework.

## Dependencies & tooling

| Item | Change |
|------|--------|
| `pyproject.toml` dependencies | `dearpygui`; remove `sv-ttk` |
| `python-preference` | May stay `managed`; update the comment (no longer about Tk bundles) |
| `AGENTS.md` / `CLAUDE.md` / `README.md` | Stack = DearPyGUI; rewrite fonts/theming; remove theme toggle, icon pipeline, Linux Tk/Geist workaround |
| Quality gate | Unchanged: `uv run ruff format`, `ruff check`, `ty check` |
| Entry points | Unchanged: `cubalite-poster`, `python -m cubalite_poster` |

## Constants cleanup

Remove or replace Tk/theme-toggle-specific constants, including but not limited
to: `THEME_LIGHT`, `THEME_DARK`, `DEFAULT_THEME`, `NAMED_FONTS`,
`ACCENT_BUTTON_STYLE`, `ICON_*`, `MOON_ICON_FILE`, `SUN_ICON_FILE`, and
icon colour constants.

Keep: window geometry/title, layout paddings/spacings, font family/size names,
greeting and button labels. Add: DPG tag names, dark theme colour tokens as
named constants (no magic hex at call sites).

## Success criteria

1. `uv run cubalite-poster` opens a 480×320 non-resizable window titled
   “Cubalite Poster”.
2. UI is dark only; no theme switcher.
3. Geist is used when fonts load; otherwise DPG default font, no crash.
4. Greeting uses a larger/bolder face than body controls.
5. Accent “Touch me” is visually primary and does not crash when clicked.
6. No `tkinter`, `ttk`, or `sv_ttk` imports or dependencies remain.
7. Theme toggle, icon renderer, and toggle icon assets are gone.
8. `ruff format`, `ruff check`, and `ty check` pass.
9. Project docs describe DearPyGUI and the dark-only shell.

## Implementation notes (for the plan, not open questions)

- Prefer string tags from constants for anything configured after creation.
- Prefer composition: `MainWindow` builds widgets; it does not own the viewport.
- `FontManager` exposes what callers need (e.g. heading font id) without leaking
  DPG registry details beyond the UI layer.
- Commit style remains Conventional Commits; no AI co-author trailers.

## Open questions

None — design approved in session (Approach A, dark-only, drop icon pipeline).
