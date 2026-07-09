"""Native dialog helpers (Win32 filter encoding is pure and OS-independent)."""

from cubalite_poster.ui.native_dialogs import _win_filter


def test_win_filter_uses_semicolons_and_double_nul() -> None:
    raw = _win_filter(
        (
            ("Imágenes", "*.png *.jpg *.jpeg"),
            ("Todos los archivos", "*.*"),
        )
    )
    assert "*.png;*.jpg;*.jpeg" in raw
    assert raw.endswith("\0\0")
    assert "Imágenes" in raw
