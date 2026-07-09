"""Bundled asset paths resolve in development installs."""

from cubalite_poster import resources
from cubalite_poster.config import constants


def test_fonts_dir_contains_required_faces() -> None:
    assert resources.FONTS_DIR.is_dir()
    for name in (
        constants.BASE_FONT_FILE,
        constants.HEADING_FONT_FILE,
        constants.POSTER_HEADLINE_FONT_FILE,
    ):
        assert (resources.FONTS_DIR / name).is_file(), name
