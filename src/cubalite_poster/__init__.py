"""Cubalite Poster — automatic poster image generator."""

from typing import Any

__all__ = ["main"]


def __getattr__(name: str) -> Any:
    # Lazy so unit tests can import resources/ui without pulling the app shell.
    if name == "main":
        from cubalite_poster.app import main as _main

        return _main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
