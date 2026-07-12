"""Self-update for the frozen Windows build (UI-adjacent infra).

Flow (see docs — approved design):
  1. On startup a daemon thread checks GitHub for the newest tagged release.
  2. If it is strictly newer than the running build, the zip is downloaded and
     extracted to a *sibling* staging folder while the operator keeps working.
  3. On the next app exit a tiny ``cmd`` script swaps the folders with renames
     only (never an in-place copy), self-checks the new build, and rolls back
     to the ``.old`` backup if it fails to launch.

Design invariants that keep the operator from being bricked:
  * The swap never mutates files inside the running install dir — it only
    renames complete, verified trees. The previous version survives as
    ``<name>.old`` until the new one proves it launches.
  * Every failure (offline, rate-limited, bad download, no permission) is a
    silent no-op. This never raises into the app and never blocks startup.
  * Nothing here runs unless the app is frozen (PyInstaller); a source
    checkout (``uv run``) is never auto-updated.

This module may import networking/subprocess but MUST NOT be imported by
``core`` or ``models`` — it is application infrastructure, not the engine.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from cubalite_poster.config import constants

# Set once a newer version has finished staging (or a prior session left one
# ready). The UI polls this to show the "update ready" notice.
_ready = threading.Event()

# Read the zip in 1 MiB chunks; cap the JSON we accept from the API.
_CHUNK_BYTES = 1 << 20
_MAX_JSON_BYTES = 1 << 20


# --------------------------------------------------------------------------- #
# Data + path resolution
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ReleaseInfo:
    """The one release we care about: newest tagged ``v*`` on GitHub."""

    tag: str
    version: tuple[int, ...]
    zip_url: str
    sha256_url: str | None


@dataclass(frozen=True)
class UpdatePaths:
    """Sibling folders used by the swap, all on the install's volume."""

    install: Path
    parent: Path
    staging: Path
    tag_file: Path
    extract: Path
    backup: Path
    failed: Path
    zip_tmp: Path
    exe: Path


def resolve_paths(exe_path: str | os.PathLike[str] | None = None) -> UpdatePaths:
    """Derive staging/backup/extract siblings from the running exe location.

    Names are the install folder's own name + suffixes, so the swap still works
    if the operator renamed the unzipped folder.
    """
    exe = Path(exe_path) if exe_path is not None else Path(sys.executable)
    install = exe.parent
    parent = install.parent
    name = install.name
    return UpdatePaths(
        install=install,
        parent=parent,
        staging=parent / (name + constants.UPDATE_STAGING_SUFFIX),
        tag_file=parent / (name + constants.UPDATE_STAGING_TAG_SUFFIX),
        extract=parent / (name + constants.UPDATE_EXTRACT_SUFFIX),
        backup=parent / (name + constants.UPDATE_BACKUP_SUFFIX),
        failed=parent / (name + constants.UPDATE_FAILED_SUFFIX),
        zip_tmp=parent / (name + ".zip.tmp"),
        exe=install / constants.UPDATE_EXE_NAME,
    )


def state_dir() -> Path:
    """Per-user state (skip breadcrumbs) — %LOCALAPPDATA%, never the install."""
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home()
    return root / constants.UPDATE_STATE_DIR_NAME


def skip_file() -> Path:
    return state_dir() / constants.UPDATE_SKIP_FILE_NAME


# --------------------------------------------------------------------------- #
# Pure logic (no IO — covered by tests)
# --------------------------------------------------------------------------- #
def parse_version(text: str | None) -> tuple[int, ...] | None:
    """``"v0.2.0"`` -> ``(0, 2, 0)``; returns ``None`` if unparseable."""
    if not text:
        return None
    parts: list[int] = []
    for segment in text.strip().lstrip("vV").split("."):
        match = re.match(r"\d+", segment)
        if match is None:
            break
        parts.append(int(match.group()))
    return tuple(parts) if parts else None


def is_newer(candidate: tuple[int, ...], installed: tuple[int, ...]) -> bool:
    """Strictly-greater comparison, zero-padded so ``(0,2)`` == ``(0,2,0)``."""
    width = max(len(candidate), len(installed))
    padded_candidate = candidate + (0,) * (width - len(candidate))
    padded_installed = installed + (0,) * (width - len(installed))
    return padded_candidate > padded_installed


def parse_release_json(data: object) -> ReleaseInfo | None:
    """Extract tag + asset URLs from a GitHub ``/releases/latest`` payload."""
    if not isinstance(data, dict):
        return None
    tag = data.get("tag_name")
    version = parse_version(tag if isinstance(tag, str) else None)
    if version is None or not isinstance(tag, str):
        return None
    zip_url: str | None = None
    sha_url: str | None = None
    assets = data.get("assets")
    if isinstance(assets, list):
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = asset.get("name")
            url = asset.get("browser_download_url")
            if not isinstance(url, str):
                continue
            if name == constants.UPDATE_ASSET_NAME:
                zip_url = url
            elif name == constants.UPDATE_SHA256_ASSET_NAME:
                sha_url = url
    if zip_url is None:
        return None
    return ReleaseInfo(tag=tag, version=version, zip_url=zip_url, sha256_url=sha_url)


def should_update(
    info: ReleaseInfo | None,
    installed: tuple[int, ...] | None,
    skipped: set[str],
) -> bool:
    """Decide whether to stage ``info`` — pure, so it is directly testable."""
    if info is None or installed is None:
        return False
    if info.tag in skipped:
        return False
    return is_newer(info.version, installed)


def parse_sha256_text(text: str | None) -> str | None:
    """Pull the 64-hex digest out of a ``Get-FileHash``/``sha256sum`` sidecar."""
    if not text:
        return None
    match = re.search(r"\b[0-9a-fA-F]{64}\b", text)
    return match.group(0).lower() if match else None


def verify_sha256(path: Path, expected_hex: str) -> bool:
    """Integrity check of a downloaded file against the sidecar digest."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(_CHUNK_BYTES), b""):
                digest.update(chunk)
    except OSError:
        return False
    return digest.hexdigest().lower() == expected_hex.lower()


def find_payload_root(extract_dir: Path, exe_name: str) -> Path | None:
    """Locate the folder that directly contains the exe after extraction.

    ``Compress-Archive`` nests a top-level ``CubalitePoster/`` folder in the
    zip, but a future CI change could flatten it — handle both so a layout
    drift can't silently stage an empty shell.
    """
    if (extract_dir / exe_name).is_file():
        return extract_dir
    try:
        children = sorted(extract_dir.iterdir())
    except OSError:
        return None
    for child in children:
        if child.is_dir() and (child / exe_name).is_file():
            return child
    return None


def read_skipped(path: Path) -> set[str]:
    """Tags of releases that bricked the self-check and must not re-stage."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    return {line.strip() for line in text.splitlines() if line.strip()}


# --------------------------------------------------------------------------- #
# Network + filesystem IO
# --------------------------------------------------------------------------- #
def _http_get_json(url: str, timeout: float) -> object | None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": constants.UPDATE_USER_AGENT,
            "Accept": constants.UPDATE_API_ACCEPT,
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        raw = response.read(_MAX_JSON_BYTES)
    return json.loads(raw)


def _http_get_text(url: str, timeout: float) -> str:
    request = urllib.request.Request(
        url, headers={"User-Agent": constants.UPDATE_USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read(_MAX_JSON_BYTES).decode("utf-8", "replace")


def _download(url: str, dest: Path, max_bytes: int, timeout: float) -> None:
    request = urllib.request.Request(
        url, headers={"User-Agent": constants.UPDATE_USER_AGENT}
    )
    total = 0
    with (
        urllib.request.urlopen(request, timeout=timeout) as response,  # noqa: S310
        open(dest, "wb") as handle,
    ):
        while True:
            chunk = response.read(_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("download exceeded size cap")
            handle.write(chunk)


def _safe_rmtree(path: Path) -> None:
    """Best-effort recursive delete; never raises (cleanup must not brick)."""
    import shutil

    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink()
    except OSError:
        pass


def _safe_extract(zip_file: zipfile.ZipFile, dest: Path) -> None:
    """Extract, refusing any member that would escape ``dest`` (zip slip)."""
    dest_resolved = dest.resolve()
    for member in zip_file.namelist():
        target = (dest_resolved / member).resolve()
        if dest_resolved not in target.parents and target != dest_resolved:
            raise ValueError(f"unsafe path in zip: {member!r}")
    zip_file.extractall(dest_resolved)


def installed_version() -> tuple[int, ...] | None:
    try:
        return parse_version(metadata.version(constants.UPDATE_PACKAGE_NAME))
    except Exception:
        return None


def has_staged_update(paths: UpdatePaths) -> bool:
    # Require the tag sidecar too. If the app exits in the microsecond between
    # the staging rename and the tag write, a `.new` without its tag is treated
    # as incomplete and re-staged (rewriting the tag) rather than applied with
    # an empty skip tag — closing the only remaining re-download-loop window.
    exe_ready = (paths.staging / constants.UPDATE_EXE_NAME).is_file()
    return exe_ready and paths.tag_file.is_file()


def stage_update(info: ReleaseInfo, paths: UpdatePaths) -> bool:
    """Download, verify, and extract ``info`` into the staging sibling.

    Returns ``True`` only once ``staging`` holds a complete tree with the exe
    at its root. The final ``os.replace`` is a single rename, so ``staging``
    never exists half-populated.
    """
    for leftover in (
        paths.extract,
        paths.staging,
        paths.tag_file,
        paths.failed,
        paths.zip_tmp,
    ):
        _safe_rmtree(leftover)
    try:
        paths.parent.mkdir(parents=True, exist_ok=True)
        _download(
            info.zip_url,
            paths.zip_tmp,
            constants.UPDATE_MAX_DOWNLOAD_BYTES,
            constants.UPDATE_DOWNLOAD_TIMEOUT_S,
        )
        if info.sha256_url is not None:
            sidecar = _http_get_text(info.sha256_url, constants.UPDATE_HTTP_TIMEOUT_S)
            expected = parse_sha256_text(sidecar)
            if expected is None or not verify_sha256(paths.zip_tmp, expected):
                return False
        if not _extract_and_finalize(paths):
            return False
        # Record the tag next to the staged folder so the exit-time swapper can
        # skip it if the new build fails to launch. Written only after the
        # staging rename, so a tag file always implies a complete staged tree.
        paths.tag_file.write_text(info.tag, encoding="utf-8")
        return True
    except (OSError, ValueError, urllib.error.URLError, zipfile.BadZipFile):
        return False
    finally:
        _safe_rmtree(paths.zip_tmp)
        _safe_rmtree(paths.extract)


def _extract_and_finalize(paths: UpdatePaths) -> bool:
    paths.extract.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(paths.zip_tmp) as zip_file:
        _safe_extract(zip_file, paths.extract)
    payload = find_payload_root(paths.extract, constants.UPDATE_EXE_NAME)
    if payload is None:
        return False
    _safe_rmtree(paths.staging)
    os.replace(payload, paths.staging)
    # Only the tree is finalized here; the tag sidecar (which has_staged_update
    # also requires) is written by the caller once this returns True.
    return (paths.staging / constants.UPDATE_EXE_NAME).is_file()


# --------------------------------------------------------------------------- #
# Windows swap glue (frozen-only; not exercised on Linux/CI)
# --------------------------------------------------------------------------- #
def build_swapper_script(
    paths: UpdatePaths, pid: int, skip_path: Path, tag: str
) -> str:
    """Render the rename-only ``cmd`` script that applies the update on exit.

    Renames only — no in-place copy or in-place ``rmdir`` of the live install
    exists, so no partial operation can leave the install dir unlaunchable.
    Waits for the app PID, keeps the old tree as ``.old``, self-checks the new
    exe, and on failure moves the bad tree aside, restores ``.old``, and records
    ``tag`` in the skip file so it is never re-downloaded.
    """
    # Baked as a literal (never %TAG%, which would expand to empty on first
    # run). Sanitised because it lands unquoted in `echo <tag>`.
    safe_tag = re.sub(r"[^A-Za-z0-9._-]", "", tag)
    return _SWAPPER_TEMPLATE.format(
        pid=pid,
        exe_name=constants.UPDATE_EXE_NAME,
        install=paths.install,
        staging=paths.staging,
        backup=paths.backup,
        failed=paths.failed,
        tagfile=paths.tag_file,
        exe=paths.exe,
        skipfile=skip_path,
        tag=safe_tag,
        selfcheck=constants.UPDATE_SELFCHECK_FLAG,
        wait=constants.UPDATE_SWAP_WAIT_SECONDS,
    )


def launch_swapper_if_staged(
    exe_path: str | os.PathLike[str] | None = None,
) -> bool:
    """If a staged update is ready, spawn the detached swapper and return True.

    Called at app exit. The swapper runs from %TEMP% (never the install dir, so
    it holds no handle on the folder it must rename) and waits for us to die.
    """
    try:
        if not _is_frozen() or sys.platform != "win32":
            return False
        paths = resolve_paths(exe_path)
        if not has_staged_update(paths):
            return False
        _spawn_swapper(paths)
        return True
    except Exception:
        return False


def _spawn_swapper(paths: UpdatePaths) -> None:
    temp = Path(tempfile.gettempdir())
    script = temp / constants.UPDATE_SWAPPER_SCRIPT_NAME
    skip = skip_file()
    skip.parent.mkdir(parents=True, exist_ok=True)
    try:
        tag = paths.tag_file.read_text(encoding="utf-8").strip()
    except OSError:
        tag = ""
    script.write_text(
        build_swapper_script(paths, os.getpid(), skip, tag), encoding="utf-8"
    )
    flags = 0
    for name in ("CREATE_NO_WINDOW", "DETACHED_PROCESS"):
        flags |= getattr(subprocess, name, 0)
    subprocess.Popen(  # noqa: S603
        ["cmd", "/c", str(script)],
        cwd=str(temp),
        creationflags=flags,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )


def run_selfcheck() -> int:
    """``--selfcheck`` mode: prove the frozen build can load, then exit 0.

    Imports the full app graph (including the DearPyGUI binary) without opening
    a window, so a broken swap — missing DLL, loader failure — fails here and
    triggers the swapper's rollback before the operator ever sees it.

    A watchdog force-exits non-zero if an import *hangs* (rather than crashing),
    so the swapper never blocks forever on an unverified build. (A hang that
    holds the GIL could still outlast it; the batch has no reliable timeout, so
    this is the practical bound.)
    """
    watchdog = threading.Timer(constants.UPDATE_SELFCHECK_TIMEOUT_S, os._exit, (1,))
    watchdog.daemon = True
    watchdog.start()
    try:
        import dearpygui.dearpygui  # noqa: F401
        from PIL import Image  # noqa: F401

        import cubalite_poster.app  # noqa: F401
    except Exception:
        # Loader/import failure — the swap produced a broken build. Roll back.
        return 1
    finally:
        watchdog.cancel()
    # Version metadata missing is NOT a launch failure: never roll back over it
    # (it would only disable auto-update, which is a safe degrade).
    try:
        version = metadata.version(constants.UPDATE_PACKAGE_NAME)
    except Exception:
        version = "unknown"
    # The swapper only reads the exit code. The diagnostic line is for a manual
    # console `--selfcheck`; in the windowed frozen exe sys.stdout is None, and
    # writing to it would raise → the swapper would wrongly roll back every good
    # build. Guard it.
    if sys.stdout is not None:
        sys.stdout.write(f"cubalite-poster {version}\n")
    return 0


# --------------------------------------------------------------------------- #
# Orchestration (called by App)
# --------------------------------------------------------------------------- #
def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def update_is_ready() -> bool:
    """True once a newer version is staged and will apply on next restart."""
    return _ready.is_set()


def _run_check() -> None:
    try:
        paths = resolve_paths()
        if has_staged_update(paths):
            _ready.set()
            return
        installed = installed_version()
        if installed is None:
            return
        skipped = read_skipped(skip_file())
        data = _http_get_json(
            constants.UPDATE_API_LATEST_URL, constants.UPDATE_HTTP_TIMEOUT_S
        )
        info = parse_release_json(data)
        if info is None or not should_update(info, installed, skipped):
            return
        if stage_update(info, paths):
            _ready.set()
    except Exception:
        # An update check must never crash the app. Silent by design.
        return


def start_background_check() -> threading.Thread | None:
    """Start the daemon update check. No-op (returns None) unless frozen."""
    if not _is_frozen():
        return None
    thread = threading.Thread(
        target=_run_check, name="cubalite-update-check", daemon=True
    )
    thread.start()
    return thread


# Rename-only swap: the live install dir is never copied into or rmdir'd in
# place, so no partial operation can strand it unlaunchable — at every instant
# a complete tree exists at INSTALL or at BACKUP. `ping` is a portable ~1s
# sleep (`timeout` fails when stdin is redirected). :moveretry is defined first
# and skipped via `goto main`; `del "%~f0"` is the very last line so cmd never
# reads the script after deleting it.
_SWAPPER_TEMPLATE = """@echo off
setlocal enableextensions
goto main

:moveretry
rem %1 -> %2, retrying while AV / Explorer / OneDrive hold a transient handle.
set /a mrtries=0
:mrloop
move %1 %2 >nul 2>&1
if not errorlevel 1 exit /b 0
if %mrtries% geq {wait} exit /b 1
ping -n 2 127.0.0.1 >nul
set /a mrtries+=1
goto mrloop

:main
set "PID={pid}"
set "INSTALL={install}"
set "STAGING={staging}"
set "BACKUP={backup}"
set "FAILED={failed}"
set "EXE={exe}"
set "SKIPFILE={skipfile}"
set "TAGFILE={tagfile}"
set "TAG={tag}"

rem 1. wait for the running app to exit (match PID *and* image name)
set /a waited=0
:waitpid
tasklist /fi "PID eq %PID%" 2>nul | find /i "{exe_name}" >nul
if errorlevel 1 goto pidgone
if %waited% geq {wait} goto giveup
ping -n 2 127.0.0.1 >nul
set /a waited+=1
goto waitpid
:pidgone

rem 2. clear stale backup/failed dirs; abort if a lock leaves one behind
rem    (a leftover BACKUP would make `move INSTALL BACKUP` nest inside it).
if exist "%BACKUP%" rmdir /s /q "%BACKUP%"
if exist "%BACKUP%" goto giveup
if exist "%FAILED%" rmdir /s /q "%FAILED%"
if exist "%FAILED%" goto giveup

rem 3. install -> backup (retry)
call :moveretry "%INSTALL%" "%BACKUP%"
if errorlevel 1 goto giveup

rem 4. staging -> install (retry); if it fails, install is still at BACKUP
call :moveretry "%STAGING%" "%INSTALL%"
if errorlevel 1 goto restore

rem 5. prove the new build launches; roll back if it does not
"%EXE%" {selfcheck}
if errorlevel 1 goto rollback

rem success: new build verified, drop the backup + consumed staging tag
if exist "%BACKUP%" rmdir /s /q "%BACKUP%"
if exist "%TAGFILE%" del "%TAGFILE%" >nul 2>&1
goto done

:rollback
rem new build is bad: move it aside (rename, never in-place delete), restore
rem the backup, and record the tag so it is never re-downloaded.
call :moveretry "%INSTALL%" "%FAILED%"
if errorlevel 1 goto rollbacklocked
call :moveretry "%BACKUP%" "%INSTALL%"
if not "%TAG%"=="" >>"%SKIPFILE%" echo %TAG%
if exist "%FAILED%" rmdir /s /q "%FAILED%"
if exist "%TAGFILE%" del "%TAGFILE%" >nul 2>&1
goto done

:rollbacklocked
rem the bad build at INSTALL is locked and could not be moved aside. Do NOT
rem move BACKUP onto it (that would nest inside the bad tree). Leave the good
rem tree at %BACKUP% for recovery and still record the skip. Staging is already
rem consumed, so drop its tag file too.
if not "%TAG%"=="" >>"%SKIPFILE%" echo %TAG%
if exist "%TAGFILE%" del "%TAGFILE%" >nul 2>&1
goto done

:restore
rem staging move failed but install already went to backup: put it back. Keep
rem the staging + tag file so the swap can be retried next exit.
if exist "%INSTALL%" goto done
call :moveretry "%BACKUP%" "%INSTALL%"
goto done

:giveup
rem nothing was consumed; keep staging + tag file for a later retry.
if not exist "%INSTALL%" if exist "%BACKUP%" call :moveretry "%BACKUP%" "%INSTALL%"

:done
del "%~f0" >nul 2>&1
"""
