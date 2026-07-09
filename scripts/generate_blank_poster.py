"""CLI helper: write a Post-layered poster.

Basic usage::

    uv run python scripts/generate_blank_poster.py out.png
    uv run python scripts/generate_blank_poster.py out.png -i='' -t=''
    uv run python scripts/generate_blank_poster.py out.png -i='photo.jpg' -t='Headline'
    uv run python scripts/generate_blank_poster.py out.png -c FF0000

Advanced (style) flags — see ``--help`` under “advanced options”.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from cubalite_poster.config import constants
from cubalite_poster.core import PosterGenerator, parse_hex_color
from cubalite_poster.core.background import resolve_image_slot
from cubalite_poster.core.colors import Rgb
from cubalite_poster.models import PosterStyle


def main(argv: list[str] | None = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    args = parser.parse_args(argv_list)

    image_path, color_hex, warning = resolve_image_slot(
        argv_list,
        image=args.image,
        color=args.color,
    )
    if warning is not None:
        print(warning, file=sys.stderr)

    fill_color = None
    if color_hex is not None:
        try:
            fill_color = parse_hex_color(color_hex)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    if image_path is not None and not image_path.is_file():
        print(f"error: image not found: {image_path}", file=sys.stderr)
        return 2

    try:
        style = _style_from_args(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    path = PosterGenerator(
        image=image_path,
        fill_color=fill_color,
        headline=args.text,
        style=style,
    ).save(args.output)
    print(
        f"Wrote {path.resolve()} ({constants.POSTER_WIDTH}x{constants.POSTER_HEIGHT})"
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Cubalite poster canvas "
            "(image fill + gradient scrim + wordmark + headline)."
        )
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=Path(constants.POSTER_DEFAULT_FILENAME),
        help=f"Output PNG path (default: {constants.POSTER_DEFAULT_FILENAME})",
    )
    parser.add_argument(
        "-i",
        "--image",
        default=constants.POSTER_IMAGE_DEFAULT,
        metavar="PATH",
        help=(
            "Background image path (Figma FILL). Default empty (-i=''). "
            "Mutually exclusive with -c; first flag wins. "
            "Paths work on Windows, macOS, and Linux."
        ),
    )
    parser.add_argument(
        "-c",
        "--color",
        default=None,
        metavar="RRGGBB",
        help=(
            "Solid image-slot fill (hex without '#'). "
            "Default white when no image. Mutually exclusive with -i; first wins."
        ),
    )
    parser.add_argument(
        "-t",
        "--text",
        default=constants.POSTER_HEADLINE_DEFAULT,
        metavar="HEADLINE",
        help="Headline text. Default is the sample Lorem Ipsum line.",
    )

    advanced = parser.add_argument_group("advanced style options")

    # Headline
    advanced.add_argument(
        "--headline-font",
        default=constants.POSTER_FONT_PATH_DEFAULT,
        metavar="PATH",
        help=(
            "Headline font file (bundled name or path). "
            f"Default: {constants.POSTER_HEADLINE_FONT_FILE}."
        ),
    )
    advanced.add_argument(
        "--headline-color",
        default=None,
        metavar="RRGGBB",
        help="Headline text colour (hex without '#'). Default: FFFFFF.",
    )
    advanced.add_argument(
        "--headline-size",
        type=int,
        default=constants.POSTER_HEADLINE_FONT_SIZE,
        metavar="PX",
        help=(
            "Preferred headline size in px "
            f"(default: {constants.POSTER_HEADLINE_FONT_SIZE})."
        ),
    )
    advanced.add_argument(
        "--headline-min-size",
        type=int,
        default=constants.POSTER_HEADLINE_MIN_FONT_SIZE,
        metavar="PX",
        help=(
            "Minimum size when auto-fitting long titles "
            f"(default: {constants.POSTER_HEADLINE_MIN_FONT_SIZE})."
        ),
    )
    advanced.add_argument(
        "--headline-max-lines",
        type=int,
        default=constants.POSTER_HEADLINE_MAX_LINES,
        metavar="N",
        help=f"Max wrapped lines (default: {constants.POSTER_HEADLINE_MAX_LINES}).",
    )
    advanced.add_argument(
        "--headline-max-height",
        type=int,
        default=constants.POSTER_HEADLINE_MAX_HEIGHT,
        metavar="PX",
        help=(
            "Headline box height in px from top of text "
            f"(default: {constants.POSTER_HEADLINE_MAX_HEIGHT})."
        ),
    )
    advanced.add_argument(
        "--headline-auto-fit",
        action=argparse.BooleanOptionalAction,
        default=constants.POSTER_HEADLINE_AUTO_FIT,
        help=(
            "Shrink headline font so text fits max-lines/height "
            "(default: on; use --no-headline-auto-fit to disable)."
        ),
    )

    # Gradient
    advanced.add_argument(
        "--gradient-color",
        default=None,
        metavar="RRGGBB",
        help="Scrim colour (hex without '#'). Default: 000000.",
    )
    advanced.add_argument(
        "--gradient-start",
        type=float,
        default=constants.POSTER_GRADIENT_START_Y,
        metavar="Y",
        help=(
            "Normalized Y where scrim alpha starts rising "
            f"(default: {constants.POSTER_GRADIENT_START_Y})."
        ),
    )
    advanced.add_argument(
        "--gradient-end",
        type=float,
        default=constants.POSTER_GRADIENT_END_Y,
        metavar="Y",
        help=(
            "Normalized Y where scrim is fully opaque "
            f"(default: {constants.POSTER_GRADIENT_END_Y})."
        ),
    )

    # Wordmark
    advanced.add_argument(
        "--wordmark-fill",
        default=None,
        metavar="RRGGBB",
        help="Wordmark background fill (hex). Default: FEF7EC.",
    )
    advanced.add_argument(
        "--wordmark-stroke",
        default=None,
        metavar="RRGGBB",
        help="Wordmark border colour (hex). Default: 000000.",
    )
    advanced.add_argument(
        "--wordmark-stroke-width",
        type=int,
        default=constants.POSTER_BADGE_STROKE_WIDTH,
        metavar="PX",
        help=f"Wordmark border width (default: {constants.POSTER_BADGE_STROKE_WIDTH}).",
    )
    advanced.add_argument(
        "--wordmark-font",
        default=constants.POSTER_FONT_PATH_DEFAULT,
        metavar="PATH",
        help=(
            "Wordmark font file (bundled name or path). "
            f"Default: {constants.POSTER_BADGE_FONT_FILE}."
        ),
    )
    advanced.add_argument(
        "--wordmark-size",
        type=int,
        default=constants.POSTER_BADGE_FONT_SIZE,
        metavar="PX",
        help=f"Wordmark font size (default: {constants.POSTER_BADGE_FONT_SIZE}).",
    )
    advanced.add_argument(
        "--wordmark-text",
        default=constants.POSTER_BADGE_LABEL,
        metavar="LABEL",
        help=f"Wordmark label (default: {constants.POSTER_BADGE_LABEL!r}).",
    )
    advanced.add_argument(
        "--wordmark-color",
        default=None,
        metavar="RRGGBB",
        help="Wordmark text colour (hex). Default: 000000.",
    )

    # Layout / borders of content box
    advanced.add_argument(
        "--padding-left",
        type=int,
        default=constants.POSTER_CONTENT_PADDING_LEFT,
        metavar="PX",
        help=(
            "Content left inset / headline X "
            f"(default: {constants.POSTER_CONTENT_PADDING_LEFT})."
        ),
    )
    advanced.add_argument(
        "--padding-right",
        type=int,
        default=constants.POSTER_CONTENT_PADDING_RIGHT,
        metavar="PX",
        help=(
            "Content right inset (sets headline width) "
            f"(default: {constants.POSTER_CONTENT_PADDING_RIGHT})."
        ),
    )
    advanced.add_argument(
        "--padding-bottom",
        type=int,
        default=constants.POSTER_CONTENT_PADDING_BOTTOM,
        metavar="PX",
        help=(
            "Bottom margin under headline box "
            f"(default: {constants.POSTER_CONTENT_PADDING_BOTTOM})."
        ),
    )
    advanced.add_argument(
        "--item-spacing",
        type=int,
        default=constants.POSTER_CONTENT_ITEM_SPACING,
        metavar="PX",
        help=(
            "Gap between wordmark and headline "
            f"(default: {constants.POSTER_CONTENT_ITEM_SPACING})."
        ),
    )

    return parser


def _style_from_args(args: argparse.Namespace) -> PosterStyle:
    style = PosterStyle()
    updates: dict[str, object] = {
        "headline_font_size": args.headline_size,
        "headline_min_font_size": args.headline_min_size,
        "headline_max_lines": args.headline_max_lines,
        "headline_max_height": args.headline_max_height,
        "headline_auto_fit": args.headline_auto_fit,
        "gradient_start_y": args.gradient_start,
        "gradient_end_y": args.gradient_end,
        "badge_stroke_width": args.wordmark_stroke_width,
        "badge_font_size": args.wordmark_size,
        "badge_label": args.wordmark_text,
        "content_padding_left": args.padding_left,
        "content_padding_right": args.padding_right,
        "content_padding_bottom": args.padding_bottom,
        "content_item_spacing": args.item_spacing,
    }

    if args.headline_font:
        updates["headline_font_file"] = args.headline_font
    if args.wordmark_font:
        updates["badge_font_file"] = args.wordmark_font

    updates["headline_color"] = _optional_hex(args.headline_color, style.headline_color)
    updates["gradient_rgb"] = _optional_hex(args.gradient_color, style.gradient_rgb)
    updates["badge_fill"] = _optional_hex(args.wordmark_fill, style.badge_fill)
    updates["badge_stroke"] = _optional_hex(args.wordmark_stroke, style.badge_stroke)
    updates["badge_text_color"] = _optional_hex(
        args.wordmark_color, style.badge_text_color
    )

    return replace(style, **updates)


def _optional_hex(value: str | None, default: Rgb) -> Rgb:
    if value is None or value.strip() == "":
        return default
    return parse_hex_color(value)


if __name__ == "__main__":
    raise SystemExit(main())
