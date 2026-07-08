# Cubalite Poster

Automatic poster image generator for a news channel. Every poster follows the
channel's strict, fixed design — the operator supplies only the variable content
(headline, photo, date) and the app renders a finished, on-brand image.

Built with Python + Tkinter and the [Sun-Valley ttk theme](https://github.com/rdbende/Sun-Valley-ttk-theme)
to match the native Windows look.

## Requirements

- [`uv`](https://docs.astral.sh/uv/)

## Run

```bash
uv run cubalite-poster
```

## Development

```bash
uv run ruff format      # format
uv run ruff check       # lint
uv run ty check         # type-check
```

See [CLAUDE.md](CLAUDE.md) for architecture, folder structure and conventions.
