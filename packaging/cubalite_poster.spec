# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — lean Windows build of Cubalite Poster.

Design goals (see README "Build Windows .exe"):
  * Small: only runtime deps + fonts actually used by the app
  * Low AV false positives: onedir (not onefile), no UPX, version resource
  * No Tk/Tcl on Windows (dialogs use Win32 comdlg32)

Build on Windows:
  uv sync --group packaging
  uv run pyinstaller packaging/cubalite_poster.spec
"""

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs, copy_metadata

ROOT = Path(SPECPATH).resolve().parent
SRC = ROOT / "src"
PKG = SRC / "cubalite_poster"
FONTS = PKG / "assets" / "fonts"

# Only faces referenced by config/constants.py (UI Geist + poster Libre).
FONT_FILES = (
    "Geist-Regular.ttf",
    "Geist-Bold.ttf",
    "LibreBaskerville-Bold.ttf",
    "OFL.txt",
)

datas = [
    (str(FONTS / name), "cubalite_poster/assets/fonts")
    for name in FONT_FILES
    if (FONTS / name).is_file()
]

# Bundle the package dist-info so importlib.metadata.version("cubalite-poster")
# works in the frozen build — the auto-updater reads it to know its own version.
datas += copy_metadata("cubalite-poster")

# DearPyGUI ships a platform .pyd / shared lib that must travel with the app.
binaries = collect_dynamic_libs("dearpygui")

# Keep the bundle free of test tools and unused imaging backends.
excludes = [
    "pytest",
    "ruff",
    "ty",
    "_pytest",
    "unittest",
    "pydoc",
    "doctest",
    "tkinter",
    "_tkinter",
    "turtle",
    "PIL.ImageQt",
    "PIL.ImageTk",
    "PIL.ImageGrab",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "IPython",
    "notebook",
]

a = Analysis(
    [str(ROOT / "packaging" / "run_app.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "dearpygui",
        "dearpygui.dearpygui",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# onedir: one folder with CubalitePoster.exe + deps.
# Prefer this over onefile — extracts-to-temp triggers AV heuristics and is slower.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CubalitePoster",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX packing is a major AV false-positive source — never enable.
    console=False,  # GUI app: no black console window.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(ROOT / "packaging" / "file_version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="CubalitePoster",
)
