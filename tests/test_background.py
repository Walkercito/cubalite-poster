"""Image-slot fill resolution: empty default, first CLI flag wins, Path portability."""

from pathlib import Path

from cubalite_poster.core.background import (
    first_fill_flag,
    parse_image_path,
    resolve_image_slot,
)


def test_first_fill_flag_detects_order() -> None:
    assert first_fill_flag(["-i", "a.jpg", "-c", "FF0000"]) == "image"
    assert first_fill_flag(["-c", "FF0000", "-i", "a.jpg"]) == "color"
    assert first_fill_flag(["--image=a.jpg", "--color=FF0000"]) == "image"
    assert first_fill_flag(["--color=FF0000", "--image", "a.jpg"]) == "color"
    assert first_fill_flag(["-t", "hi"]) is None


def test_parse_image_path_empty_is_none() -> None:
    # CLI uses empty strings for “unset” (like -t=''). Path("") is not used.
    assert parse_image_path("") is None
    assert parse_image_path("   ") is None
    assert parse_image_path(None) is None


def test_parse_image_path_cross_platform_strings() -> None:
    # pathlib normalises separators; do not require the file to exist.
    posix = parse_image_path("photos/shot.jpg")
    assert posix is not None
    assert posix.parts[-2:] == ("photos", "shot.jpg") or posix.as_posix().endswith(
        "photos/shot.jpg"
    )

    mixed = parse_image_path(r"C:\Users\me\Pictures\shot.jpg")
    assert mixed is not None
    # On all OSes Path keeps the path; as_posix uses forward slashes.
    assert "shot.jpg" in mixed.as_posix()

    home = parse_image_path("~/Pictures/shot.jpg")
    assert home is not None
    assert not str(home).startswith("~")


def test_resolve_empty_image_string_is_unset() -> None:
    image, color, warning = resolve_image_slot(["-i", ""], image="", color=None)
    assert image is None
    assert color is None
    assert warning is None


def test_resolve_only_image() -> None:
    image, color, warning = resolve_image_slot(
        ["-i", "shot.jpg"], image="shot.jpg", color=None
    )
    assert image == Path("shot.jpg")
    assert color is None
    assert warning is None


def test_resolve_only_color() -> None:
    image, color, warning = resolve_image_slot(
        ["-c", "FF0000"], image="", color="FF0000"
    )
    assert image is None
    assert color == "FF0000"
    assert warning is None


def test_resolve_both_image_first_wins() -> None:
    image, color, warning = resolve_image_slot(
        ["-i", "shot.jpg", "-c", "FF0000"],
        image="shot.jpg",
        color="FF0000",
    )
    assert image == Path("shot.jpg")
    assert color is None
    assert warning is not None
    assert "image" in warning.lower()
    assert "first" in warning.lower()


def test_resolve_both_color_first_wins() -> None:
    image, color, warning = resolve_image_slot(
        ["-c", "00FF00", "--image", "shot.jpg"],
        image="shot.jpg",
        color="00FF00",
    )
    assert image is None
    assert color == "00FF00"
    assert warning is not None
    assert "colour" in warning.lower() or "color" in warning.lower()


def test_empty_image_with_color_does_not_warn() -> None:
    """-i='' is unset, so -c alone is not a conflict."""
    image, color, warning = resolve_image_slot(
        ["-i", "", "-c", "FFFFFF"],
        image="",
        color="FFFFFF",
    )
    assert image is None
    assert color == "FFFFFF"
    assert warning is None
