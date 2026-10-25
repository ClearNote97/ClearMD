"""CLI entry point. Walking skeleton: only reports the version until feature 001 lands."""

import argparse
from collections.abc import Sequence
from importlib.metadata import version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clearmd",
        description="Turn documents into Markdown. 100% local.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('clearmd')}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
