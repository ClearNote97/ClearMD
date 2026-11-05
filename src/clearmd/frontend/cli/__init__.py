"""Command-line interface for ClearMD."""

from clearmd.frontend.cli.app import main
from clearmd.frontend.cli.parser import build_parser

__all__ = ["build_parser", "main"]
