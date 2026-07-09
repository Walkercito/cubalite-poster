"""Resolve mutually exclusive image-slot fill sources (image vs solid colour)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

FillKind = str  # "image" | "color"


def parse_image_path(value: str | Path | None) -> Path | None:
    """Turn a CLI path string into a cross-platform ``Path``, or ``None`` if empty.

    Uses :class:`pathlib.Path` so Windows (``C:\\…``, ``/``), POSIX, and
    ``~`` home expansion all work without OS-specific branching.
    """
    if value is None:
        return None
    if isinstance(value, Path):
        # Path("") is not meaningful — treat as unset.
        raw = str(value).strip()
        if not raw:
            return None
        return value.expanduser()
    stripped = value.strip()
    if not stripped:
        return None
    return Path(stripped).expanduser()


def first_fill_flag(argv: Sequence[str]) -> FillKind | None:
    """Return which fill flag appears first on the CLI: ``image`` or ``color``."""
    for arg in argv:
        if arg in ("-i", "--image") or arg.startswith(("-i=", "--image=")):
            return "image"
        if arg in ("-c", "--color") or arg.startswith(("-c=", "--color=")):
            return "color"
    return None


def resolve_image_slot(
    argv: Sequence[str],
    *,
    image: str | Path | None,
    color: str | None,
) -> tuple[Path | None, str | None, str | None]:
    """Pick the image-slot source when both image and colour may be set.

    ``image`` may be an empty string (same as ``-i=''``) meaning no image.
    Returns ``(image_path, color_hex, warning)``.
    If both are provided, the flag that appears first on ``argv`` wins and a
    warning explains the other was ignored. If neither was passed, both are
    ``None`` (caller uses the default white fill).
    """
    image_path = parse_image_path(image)
    color_hex = color.strip() if isinstance(color, str) and color.strip() else color
    if color_hex == "":
        color_hex = None

    if image_path is None and color_hex is None:
        return None, None, None
    if image_path is not None and color_hex is None:
        return image_path, None, None
    if image_path is None and color_hex is not None:
        return None, color_hex, None

    # Both provided — first flag on the command line wins.
    winner = first_fill_flag(argv)
    if winner == "color":
        warning = (
            "warning: both --image/-i and --color/-c were passed; "
            "using colour because it appeared first "
            f"({color_hex!r}). Image ignored."
        )
        return None, color_hex, warning
    warning = (
        "warning: both --image/-i and --color/-c were passed; "
        f"using image because it appeared first ({image_path}). Colour ignored."
    )
    return image_path, None, warning
