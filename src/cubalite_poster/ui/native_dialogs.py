"""Native OS file dialogs.

Windows uses the system common dialogs via ctypes (no Tk/Tcl — smaller builds,
fewer AV false-positive surface). Other platforms fall back to Tk.
"""

from __future__ import annotations

import sys
from pathlib import Path

from cubalite_poster.config import constants


def ask_open_image() -> Path | None:
    """Show the native open-file dialog for a background photo."""
    return _ask_open(
        title=constants.DIALOG_OPEN_IMAGE_TITLE,
        filetypes=constants.IMAGE_FILETYPES,
    )


def ask_save_poster(
    default_name: str = constants.POSTER_DEFAULT_FILENAME,
) -> Path | None:
    """Show the native save-file dialog for exporting a PNG."""
    path = _ask_save(
        title=constants.DIALOG_SAVE_POSTER_TITLE,
        filetypes=constants.PNG_FILETYPES,
        default_name=default_name,
    )
    if path is None:
        return None
    if path.suffix.lower() != ".png":
        return path.with_suffix(".png")
    return path


def _ask_open(
    *,
    title: str,
    filetypes: tuple[tuple[str, str], ...],
) -> Path | None:
    if sys.platform == "win32":
        return _win_open(title=title, filetypes=filetypes)
    return _tk_open(title=title, filetypes=filetypes)


def _ask_save(
    *,
    title: str,
    filetypes: tuple[tuple[str, str], ...],
    default_name: str,
) -> Path | None:
    if sys.platform == "win32":
        return _win_save(
            title=title,
            filetypes=filetypes,
            default_name=default_name,
        )
    return _tk_save(
        title=title,
        filetypes=filetypes,
        default_name=default_name,
    )


# --- Windows (comdlg32) ----------------------------------------------------


def _win_open(
    *,
    title: str,
    filetypes: tuple[tuple[str, str], ...],
) -> Path | None:
    raw = _win_file_dialog(
        title=title,
        filetypes=filetypes,
        save=False,
        default_name="",
    )
    return Path(raw).expanduser() if raw else None


def _win_save(
    *,
    title: str,
    filetypes: tuple[tuple[str, str], ...],
    default_name: str,
) -> Path | None:
    raw = _win_file_dialog(
        title=title,
        filetypes=filetypes,
        save=True,
        default_name=default_name,
    )
    return Path(raw).expanduser() if raw else None


def _win_file_dialog(
    *,
    title: str,
    filetypes: tuple[tuple[str, str], ...],
    save: bool,
    default_name: str,
) -> str | None:
    """OPENFILENAMEW wrapper around GetOpenFileNameW / GetSaveFileNameW."""
    import ctypes
    from ctypes import wintypes

    class OPENFILENAMEW(ctypes.Structure):
        _fields_ = [
            ("lStructSize", wintypes.DWORD),
            ("hwndOwner", wintypes.HWND),
            ("hInstance", wintypes.HINSTANCE),
            ("lpstrFilter", wintypes.LPCWSTR),
            ("lpstrCustomFilter", wintypes.LPWSTR),
            ("nMaxCustFilter", wintypes.DWORD),
            ("nFilterIndex", wintypes.DWORD),
            ("lpstrFile", wintypes.LPWSTR),
            ("nMaxFile", wintypes.DWORD),
            ("lpstrFileTitle", wintypes.LPWSTR),
            ("nMaxFileTitle", wintypes.DWORD),
            ("lpstrInitialDir", wintypes.LPCWSTR),
            ("lpstrTitle", wintypes.LPCWSTR),
            ("Flags", wintypes.DWORD),
            ("nFileOffset", wintypes.WORD),
            ("nFileExtension", wintypes.WORD),
            ("lpstrDefExt", wintypes.LPCWSTR),
            ("lCustData", wintypes.LPARAM),
            ("lpfnHook", wintypes.LPVOID),
            ("lpTemplateName", wintypes.LPCWSTR),
            ("pvReserved", wintypes.LPVOID),
            ("dwReserved", wintypes.DWORD),
            ("FlagsEx", wintypes.DWORD),
        ]

    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    buffer = ctypes.create_unicode_buffer(default_name, 4096)
    ofn.lpstrFile = ctypes.cast(buffer, wintypes.LPWSTR)
    ofn.nMaxFile = len(buffer)
    ofn.lpstrTitle = title
    ofn.lpstrFilter = _win_filter(filetypes)
    ofn.nFilterIndex = 1
    ofn.lpstrDefExt = "png" if save else None

    # OFN_EXPLORER | OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST | OFN_OVERWRITEPROMPT
    flags = 0x00080000 | 0x00000800
    if save:
        flags |= 0x00000002  # OFN_OVERWRITEPROMPT
    else:
        flags |= 0x00001000  # OFN_FILEMUSTEXIST
    ofn.Flags = flags

    # WinDLL exists only on Windows; keep this importable under Linux CI/ty.
    windll_cls = getattr(ctypes, "WinDLL", None)
    if windll_cls is None:
        return None
    comdlg32 = windll_cls("comdlg32", use_last_error=True)
    if save:
        ok = bool(comdlg32.GetSaveFileNameW(ctypes.byref(ofn)))
    else:
        ok = bool(comdlg32.GetOpenFileNameW(ctypes.byref(ofn)))
    if not ok:
        return None
    return buffer.value or None


def _win_filter(filetypes: tuple[tuple[str, str], ...]) -> str:
    """Build an OPENFILENAME filter string from Tk-style (label, patterns) pairs."""
    parts: list[str] = []
    for label, patterns in filetypes:
        # Tk uses spaces; Win32 wants semicolons: "*.png *.jpg" → "*.png;*.jpg"
        win_patterns = ";".join(patterns.split())
        parts.append(f"{label} ({win_patterns})")
        parts.append(win_patterns)
    # Double-NUL terminator required by the API.
    return "\0".join(parts) + "\0\0"


# --- Tk fallback (Linux / macOS) -------------------------------------------


def _tk_open(
    *,
    title: str,
    filetypes: tuple[tuple[str, str], ...],
) -> Path | None:
    root = _hidden_root()
    try:
        from tkinter import filedialog

        raw = filedialog.askopenfilename(parent=root, title=title, filetypes=filetypes)
    finally:
        root.destroy()
    if not raw:
        return None
    return Path(raw).expanduser()


def _tk_save(
    *,
    title: str,
    filetypes: tuple[tuple[str, str], ...],
    default_name: str,
) -> Path | None:
    root = _hidden_root()
    try:
        from tkinter import filedialog

        raw = filedialog.asksaveasfilename(
            parent=root,
            title=title,
            filetypes=filetypes,
            defaultextension=".png",
            initialfile=default_name,
        )
    finally:
        root.destroy()
    if not raw:
        return None
    return Path(raw).expanduser()


def _hidden_root():  # type: ignore[no-untyped-def]
    import contextlib
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    with contextlib.suppress(tk.TclError):
        root.attributes("-topmost", True)
    return root
