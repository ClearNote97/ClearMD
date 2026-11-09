"""The command-line interface (feature 001): plan, ask if needed, convert, summarize.

Every text comes from the catalogs (ADR-0012). Progress, prompts and notes go to stderr; the final
summary goes to stdout. The batch runs in a thread so that Ctrl+C reaches the main thread at once
and cancels it (AC-26).
"""

import multiprocessing
import sys
from collections.abc import Sequence

from clearmd.frontend.cli.batch import EXIT_FAILED
from clearmd.frontend.cli.flow import run
from clearmd.frontend.cli.parser import requested_language
from clearmd.frontend.cli.report import p
from clearmd.i18n import DEFAULT_LANGUAGE, load_catalog, resolve_language


def main(argv: Sequence[str] | None = None) -> int:
    multiprocessing.freeze_support()  # a no-op unless running as a packaged executable
    try:
        return run(argv)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as error:  # the last net: a message, never a traceback (UX contract)
        catalog = load_catalog(
            resolve_language(requested_language(argv), DEFAULT_LANGUAGE)
        ).for_terminal()
        detail = p(f"{type(error).__name__}: {error}")
        print(catalog.text("cli.unexpected_error", detail=detail), file=sys.stderr)
        return EXIT_FAILED
