"""Colour parsing helpers for the poster engine (UI-agnostic)."""

from __future__ import annotations

from cubalite_poster.config import constants

Rgb = tuple[int, int, int]


def parse_hex_color(value: str) -> Rgb:
    """Parse an RRGGBB hex string (optional leading ``#``) into an RGB tuple.

    Raises ``ValueError`` when the string is not a valid 6-digit hex colour.
    """
    raw = value.strip().removeprefix("#").removeprefix("0x").removeprefix("0X")
    if len(raw) != constants.POSTER_HEX_COLOR_LENGTH:
        raise ValueError(
            f"expected {constants.POSTER_HEX_COLOR_LENGTH} hex digits "
            f"(e.g. FEF7EC), got {value!r}"
        )
    try:
        r = int(raw[0:2], 16)
        g = int(raw[2:4], 16)
        b = int(raw[4:6], 16)
    except ValueError as exc:
        raise ValueError(f"invalid hex colour {value!r}") from exc
    return (r, g, b)
