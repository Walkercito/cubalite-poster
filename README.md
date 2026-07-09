# Cubalite Poster

Automatic poster image generator for a news channel. Every poster follows the
channel's strict, fixed design — the operator supplies only the variable content
(headline, photo, date) and the app renders a finished, on-brand image.

Built with Python and [DearPyGUI](https://dearpygui.readthedocs.io/en/latest/).

## Requirements

- [`uv`](https://docs.astral.sh/uv/)

## Run (development)

```bash
uv run cubalite-poster
```

## Development

```bash
uv run ruff format      # format
uv run ruff check       # lint
uv run ty check         # type-check
uv run pytest           # unit tests
```

See [AGENTS.md](AGENTS.md) for architecture, folder structure and conventions.

## Build Windows `.exe`

The supported distribution is a **folder** with `CubalitePoster.exe` (PyInstaller
*onedir*), not a single self-extracting binary. That keeps the payload smaller
to download as a zip, starts faster, and is far less likely to be flagged as
malware than a *onefile* + UPX pack.

### GitHub Actions (recommended)

A real Windows runner builds the zip for you — no local Windows machine required.

| Trigger | What happens |
|---------|----------------|
| Push to `main` | Tests + Windows build → **Releases → “Latest build”** (pre-release) |
| Pull request | Tests + build artifact only (no release) |
| Manual | **Actions → Build Windows → Run workflow** |
| Tag `v*` (e.g. `v0.1.0`) | Versioned **GitHub Release** with the zip |

**Download (easiest):** repo → [Releases](../../releases) → *Latest build* → `CubalitePoster.zip`  
Unzip and run `CubalitePoster\CubalitePoster.exe` (whole folder).

Versioned release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

### On a Windows machine (local)

```powershell
# From the repo root
powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
```

Outputs:

| Path | What it is |
|------|------------|
| `dist/CubalitePoster/CubalitePoster.exe` | Launcher — run this |
| `dist/CubalitePoster/*` | Required DLLs + assets (ship the whole folder) |
| `dist/CubalitePoster.zip` | Ready-to-send archive of that folder |

### Design choices (size + SmartScreen)

- **Runtime deps only:** DearPyGUI + Pillow (no Tk/Tcl on Windows — file dialogs
  use the Win32 common dialog via `ctypes`).
- **Fonts:** only `Geist-Regular`, `Geist-Bold`, and `LibreBaskerville-Bold`
  are bundled (unused Geist weights are left out of the package).
- **No UPX:** packing with UPX is a common antivirus false-positive trigger.
- **No console window:** GUI subsystem (`console=False`).
- **VERSIONINFO resource:** product name / version embedded in the PE.
- **Bytecode optimize=2** for a slightly leaner archive.

### Optional: Authenticode signing

Unsigned Python-frozen exes often get a SmartScreen “unknown publisher” prompt
even when clean. To minimise that for real operators, sign after the build:

```powershell
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
  /a dist\CubalitePoster\CubalitePoster.exe
```

(Requires a code-signing certificate from a CA.)

### Do not use (for this project)

| Flag / mode | Why we avoid it |
|-------------|-----------------|
| `--onefile` | Unpacks to `%TEMP%` at runtime → AV heuristics + slower start |
| `--upx` / UPX | Classic false-positive magnet |
| Bundling Medium/SemiBold Geist | Unused by the app, pure bloat |
