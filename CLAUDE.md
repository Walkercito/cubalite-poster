# CLAUDE.md

## Project

**Cubalite Poster** is a desktop application that automatically generates poster
images for a news channel. Every poster follows the channel's strict, fixed
design (layout, typography, colours, safe zones), so the operator only supplies
the variable content — a headline, a photo, a date — and the app renders a
finished, on-brand image ready to publish.

The goal is speed and consistency: no manual design work, no off-brand posters.

### Stack

- **Language:** Python 3.12+
- **GUI:** Tkinter + [Sun-Valley ttk theme](https://github.com/rdbende/Sun-Valley-ttk-theme)
  (`sv-ttk`) to match the native Windows 11 look, since this app is used mainly
  on Windows.
- **Package manager:** [`uv`](https://docs.astral.sh/uv/) — pinned to a
  uv-managed CPython (`python-preference = "only-managed"`) because managed
  builds bundle Tkinter on every OS.
- **Type checker:** [`ty`](https://github.com/astral-sh/ty) — `uv run ty check`
- **Formatter / linter:** [`ruff`](https://docs.astral.sh/ruff/) —
  `uv run ruff format` and `uv run ruff check`

### Running

```bash
uv run cubalite-poster        # via the project script
uv run python -m cubalite_poster   # via the module entry point
```

### Quality gate

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
```

## Folder structure

```
cubalite-poster/
├── src/cubalite_poster/
│   ├── __init__.py          # exposes main()
│   ├── __main__.py          # `python -m cubalite_poster`
│   ├── app.py               # App: owns root window, fonts + theme lifecycle
│   ├── resources.py         # bundled-asset paths (fonts, ...)
│   ├── config/
│   │   ├── __init__.py
│   │   └── constants.py     # every fixed value lives here (No Magic Values)
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py   # the main view (a ttk.Frame)
│   │   ├── fonts.py         # FontManager: register + apply the Geist font
│   │   ├── theme.py         # ThemeController: light/dark state over sv-ttk
│   │   ├── icons.py         # SVG icon sources + IconRenderer (Tk-native SVG)
│   │   └── widgets/
│   │       └── theme_toggle.py   # ThemeToggle: icon button that flips theme
│   ├── core/                # poster-generation logic (no Tk imports here)
│   │   └── __init__.py
│   ├── models/              # plain data models (poster spec, etc.)
│   │   └── __init__.py
│   └── assets/
│       ├── fonts/           # bundled Geist TTFs + OFL licence
│       └── icons/           # PNGs rasterised from the SVG sources
├── scripts/
│   └── render_icons.py      # regenerate assets/icons from the SVG sources
├── tests/
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

**Key boundary:** `core/` and `models/` must never import Tkinter. The UI
depends on the core, never the reverse — this keeps the poster engine testable
and reusable (CLI, batch, server) independent of the GUI.

### Fonts & theming

- **Geist** (Vercel, OFL) is bundled in `assets/fonts` and registered with the
  OS at start-up by `FontManager` — privately per-process via
  `AddFontResourceExW` on Windows, or copied into the user font directory and
  `fc-cache`-refreshed on Linux/fontconfig. `FontManager` retargets Tk's shared
  named fonts so every widget inherits Geist (DRY), and falls back to a system
  sans if the family cannot be resolved.
- **Theme** is Sun-Valley (`sv-ttk`), light by default, switchable at runtime
  via the Moon/Sun toggle in the top-right corner. `ThemeController` owns the
  state and notifies observers; `IconRenderer` loads the per-theme icon.
- **Icons** ship as PNGs pre-rasterised from the SVG sources
  (`scripts/render_icons.py`), so they load on any Tk 8.6+ — the native SVG
  photo format only exists in Tk 8.7+, which neither Ubuntu's system Tk nor
  python.org on Windows provides. The SVG sources stay in `ui/icons.py` as the
  design's source of truth; rerun the script after changing them or the icon
  colour/size constants.
- **Linux note:** Geist needs a Tk built with Xft/fontconfig. Distro Tk (8.6)
  has it, but the uv-managed CPython's Tk does not on Linux, so Geist falls back
  there. Run against the system interpreter (`python3-tk`) to get Geist — see
  the README. On **Windows** — the primary target — the managed Tk renders
  Geist via GDI with no extra setup.

## Principles

### OOP

- Model the domain with classes that own their state and behaviour. Each view is
  a class (a `ttk.Frame` subclass); the application shell is a class; the poster
  engine is a class.
- One responsibility per class. A window builds and wires its widgets; it does
  not also generate images. A generator produces images; it knows nothing about
  buttons.
- Prefer composition over inheritance for wiring things together; use
  inheritance only for genuine "is-a" relationships (e.g. a custom widget *is a*
  `ttk.Frame`).

### DRY

- Never copy-paste layout, styling, or logic. Factor repeated widget setups into
  reusable helpers or custom widget classes under `ui/widgets/`.
- A value or rule is defined **once**. If two places need it, they import it from
  one source of truth.

### No Magic Values

- No bare numbers or string literals in logic or layout. Sizes, paddings,
  colours, titles, font names, file paths, and labels all live as named
  constants in `config/constants.py` (or a class-level constant when strictly
  local).
- Names explain intent: `WINDOW_WIDTH`, not `900`; `GREETING_TEXT`, not
  `"Hello world!"`. Reading the call site should tell you *why*, not just *what*.

## Commits

Industry-standard, not changelog essays.

- **Conventional Commits**: `type(scope): subject` — e.g. `feat(hotkeys): grab a single
  combo via XGrabKey`. Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`,
  `build`, `ci`.
- Subject in the imperative mood, ≤ 72 chars, no trailing period.
- Body only when it adds signal: what changed and why, wrapped at ~72 cols. A few lines,
  not a hundred. Reference issues (`Closes #12`) when relevant.
- **No AI/assistant references of any kind.** No "Generated with", no
  `Co-Authored-By: Claude`, no tool credits, no emoji robots. Commits read as if written
  by the maintainer.
- Commit only when asked. Branch off `main` for feature work; never commit straight to a
  shared branch without being told to.
