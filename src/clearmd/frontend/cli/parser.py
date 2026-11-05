"""The command line parser and the language requested on it."""

import argparse
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path

from clearmd.backend.api import Strategy
from clearmd.i18n import SUPPORTED_LANGUAGES, Catalog


def build_parser(catalog: Catalog) -> argparse.ArgumentParser:
    help_ = catalog.text
    parser = argparse.ArgumentParser(prog="clearmd", description=help_("cli.help.description"))
    parser.add_argument("paths", nargs="+", type=Path, metavar="PATH", help=help_("cli.help.paths"))
    existing = parser.add_mutually_exclusive_group()
    existing.add_argument("--overwrite", action="store_true", help=help_("cli.help.overwrite"))
    existing.add_argument("--skip", action="store_true", help=help_("cli.help.skip"))
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
        "--images",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=help_("cli.help.images"),
    )
    parser.add_argument("--dry-run", action="store_true", help=help_("cli.help.dry_run"))
    parser.add_argument("--open", action="store_true", help=help_("cli.help.open"))
    parser.add_argument("--lang", choices=SUPPORTED_LANGUAGES, help=help_("cli.help.lang"))
    parser.add_argument("-q", "--quiet", action="store_true", help=help_("cli.help.quiet"))
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('clearmd')}")
    return parser


def requested_language(argv: Sequence[str] | None) -> str | None:
    """``--lang`` is read first, so that even the help and the settings warnings use it."""
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--lang", choices=SUPPORTED_LANGUAGES)
    known, _ = pre.parse_known_args(argv)
    language: str | None = known.lang
    return language
