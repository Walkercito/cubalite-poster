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

**Versioned release** (this is what operators auto-update to — see
[Auto-update](#auto-update)):

1. Bump `version` in `pyproject.toml` (e.g. `0.1.0` → `0.2.0`).
2. Commit, then tag and push:

```bash
git tag v0.2.0
git push origin v0.2.0
```

CI **fails the release if the tag doesn't match `pyproject.toml`**, so the
frozen app's reported version always equals its tag. The build also publishes a
`CubalitePoster.zip.sha256` sidecar that the auto-updater verifies.

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

## Auto-update

The frozen Windows build updates itself from tagged GitHub releases. It never
runs from a source checkout (`uv run`), so development is unaffected.

**How it works** (`src/cubalite_poster/updater.py`):

1. On startup a background thread asks GitHub for the newest tagged release
   (`GET /releases/latest`, which already ignores the rolling `latest`
   pre-release). If it's **strictly newer** than the running version, the zip
   is downloaded, its `.sha256` verified, and extracted to a sibling
   `CubalitePoster.new` folder while the operator keeps working. A small green
   *“Actualización lista”* notice appears when it's ready.
2. On the **next app exit**, a tiny `cmd` script swaps folders with **renames
   only** (`CubalitePoster` → `.old`, `.new` → `CubalitePoster`), then runs
   `CubalitePoster.exe --selfcheck`. If the new build fails to launch it **rolls
   back** to `.old` and records the bad tag in
   `%LOCALAPPDATA%\CubalitePoster\skip-versions.txt` so it isn't retried.

Every failure (offline, GitHub rate limit, bad download, read-only folder) is a
**silent no-op** — it never blocks startup and never bricks the install. The
swap only ever renames complete, verified trees, so any interruption leaves a
launchable app plus a `.old` backup.

**Publishing an update:** just do a [versioned release](#build-windows-exe)
(bump `pyproject.toml`, tag `vX.Y.Z`, push). Operators pick it up on their next
launch.

**Required once — Windows hand-test of the swap.** The pure logic is covered by
`tests/test_updater.py`, but the `cmd` swap script can only be exercised on
Windows. Before relying on it in production, tag a throwaway `vX.Y.Z`, install
the previous version, and confirm the swap survives this failure matrix:

- Normal case: new version applies on restart, `.old` is cleaned up.
- The install folder is open in Explorer during the swap (retry/backoff).
- A deliberately broken build → `--selfcheck` fails → rolls back to `.old` and
  writes a `skip-versions.txt` entry (the bad tag isn't re-downloaded).
- The `CubalitePoster` folder sits on a OneDrive-synced Desktop.

**Operator recovery (last resort).** If an update ever leaves the app unable to
start, recovery is the same action used to install it: download
`CubalitePoster.zip` from [Releases](../../releases) and unzip it fresh.
