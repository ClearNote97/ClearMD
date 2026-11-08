"""The command line parser and the language requested on it."""

import argparse
from collections.abc import Callable, Sequence
from importlib.metadata import version
from pathlib import Path

from clearmd.backend.api import Into, Keep, Strategy
from clearmd.i18n import SUPPORTED_LANGUAGES, Catalog


def build_parser(catalog: Catalog) -> argparse.ArgumentParser:
    help_ = catalog.text
    parser = argparse.ArgumentParser(prog="clearmd", description=help_("cli.help.description"))
    parser.add_argument("paths", nargs="+", type=Path, metavar="PATH", help=help_("cli.help.paths"))
    existing = parser.add_mutually_exclusive_group()
    existing.add_argument("--overwrite", action="store_true", help=help_("cli.help.overwrite"))
    existing.add_argument("--skip", action="store_true", help=help_("cli.help.skip"))
    existing.add_argument("--changed", action="store_true", help=help_("cli.help.changed"))
    parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=help_("cli.help.recursive"),
    )
    parser.add_argument(
        "--output-root", type=Path, metavar="DIR", help=help_("cli.help.output_root")
    )
    parser.add_argument(
        "--html", choices=[strategy.value for strategy in Strategy], help=help_("cli.help.html")
    )
    parser.add_argument(
        "--summary-pdf",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=help_("cli.help.summary_pdf"),
    )
    parser.add_argument(
        "--summary-pdf-only",
        action="store_true",
        default=False,
        help=help_("cli.help.summary_pdf_only"),
    )
    parser.add_argument(
        "--images",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=help_("cli.help.images"),
    )
    split = parser.add_mutually_exclusive_group()  # Split instead of Convert (feature 023)
    split.add_argument(
        "--split-parts", type=whole(2), metavar="N", help=help_("cli.help.split_parts")
    )
    split.add_argument(
        "--split-pages", type=whole(1), metavar="N", help=help_("cli.help.split_pages")
    )
    split.add_argument(
        "--split-words",
        type=whole(500, 1_000_000),
        metavar="N",
        help=help_("cli.help.split_words"),
    )
    parser.add_argument(
        "--keep", choices=[keep.value for keep in Keep], help=help_("cli.help.keep")
    )
    parser.add_argument(  # Merge (feature 026)
        "--merge", choices=[into.value for into in Into], help=help_("cli.help.merge")
    )
    parser.add_argument("--dry-run", action="store_true", help=help_("cli.help.dry_run"))
    parser.add_argument("--open", action="store_true", help=help_("cli.help.open"))
    parser.add_argument("--lang", choices=SUPPORTED_LANGUAGES, help=help_("cli.help.lang"))
    parser.add_argument("-q", "--quiet", action="store_true", help=help_("cli.help.quiet"))
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('clearmd')}")
    return parser


def whole(low: int, high: int = 10_000) -> Callable[[str], int]:
    """An argument type: a whole number from ``low`` to ``high``."""

    def parse(text: str) -> int:
        try:
            value = int(text)
        except ValueError:
            raise argparse.ArgumentTypeError(f"not a whole number: {text!r}") from None
        if not low <= value <= high:
            raise argparse.ArgumentTypeError(f"must be from {low} to {high}: {value}")
        return value

    return parse


def requested_language(argv: Sequence[str] | None) -> str | None:
    """``--lang`` is read first, so that even the help and the settings warnings use it."""
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--lang", choices=SUPPORTED_LANGUAGES)
    known, _ = pre.parse_known_args(argv)
    language: str | None = known.lang
    return language
