"""The flow of one run: settings, plan, decision, batch, summary, open."""

import argparse
import sys
from collections.abc import Sequence

from clearmd.backend.api import (
    Cut,
    Keep,
    SplitSpec,
    Strategy,
    load_settings,
    open_folder,
    plan_batch,
)
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.cli.batch import (
    EXIT_CANCELLED,
    EXIT_DECISION_REQUIRED,
    EXIT_OK,
    EXIT_USAGE,
    exit_code,
    run_cancellable,
)
from clearmd.frontend.cli.parser import build_parser, requested_language
from clearmd.frontend.cli.progress import Progress
from clearmd.frontend.cli.prompts import decision as decide
from clearmd.frontend.cli.report import (
    p,
    print_dry_run,
    print_plan_notes,
    print_settings_warnings,
    print_summary,
    summary_roots,
)
from clearmd.i18n import load_catalog, resolve_language


def run(argv: Sequence[str] | None) -> int:
    settings, settings_warnings = load_settings()
    catalog = load_catalog(resolve_language(requested_language(argv), settings.language))
    parser = build_parser(catalog)
    args = parser.parse_args(argv)
    if args.keep and not (args.split_parts or args.split_pages or args.split_words):
        parser.error(catalog.text("cli.keep_needs_split"))
    split = split_spec(args, settings)
    err = sys.stderr
    print_settings_warnings(catalog, settings_warnings, err)

    # A flag decides for this run only; without one, the shared settings do (AC-34).
    recursive = settings.recursive if args.recursive is None else args.recursive
    on_existing = (
        "overwrite" if args.overwrite else "skip" if args.skip else settings.on_existing_output
    )
    try:
        plan = plan_batch(
            args.paths,
            recursive=recursive,
            output_root=args.output_root,
            html_strategy=Strategy(args.html or settings.html_strategy),
            split=split,
        )
    except KeyboardInterrupt:
        print(catalog.text("cli.cancelled_before_start"), file=err)
        return EXIT_CANCELLED
    print_plan_notes(catalog, plan, quiet=args.quiet, stream=err)
    if plan.is_empty:
        if plan.input_errors and not plan.skipped:
            print(catalog.text("cli.no_valid_input"), file=err)
            return EXIT_USAGE
        print(catalog.text("cli.nothing_to_split" if split else "cli.nothing_to_convert"))
        return EXIT_OK
    if args.dry_run:
        print_dry_run(catalog, plan)
        return EXIT_OK

    try:
        decision = decide(catalog, plan, on_existing, err)
    except KeyboardInterrupt:
        print(catalog.text("cli.cancelled_before_start"), file=err)
        return EXIT_CANCELLED
    if decision is None:
        return EXIT_DECISION_REQUIRED
    progress = Progress(catalog, quiet=args.quiet, stream=err)
    summary_pdf, summary_markdown = summary_files(args, settings.summary_format)
    images = settings.images == "folder" if args.images is None else args.images
    report = run_cancellable(
        catalog,
        plan,
        decision,
        progress,
        err,
        summary_pdf=summary_pdf,
        summary_markdown=summary_markdown,
        images=images,
    )
    print_summary(catalog, report)
    if args.open:
        for root in summary_roots(report):
            try:
                open_folder(root)
            except (OSError, ValueError):  # a root refused as a link, no file browser…
                print(catalog.text("cli.cannot_open", path=p(root)), file=err)
    return exit_code(report)


def split_spec(args: argparse.Namespace, settings: Settings) -> SplitSpec | None:
    """Split, when asked for (feature 023): the cut from the flag, what to keep from --keep or
    the setting."""
    keep = Keep(args.keep or settings.split_keep)
    if args.split_parts:
        return SplitSpec(Cut.PARTS, args.split_parts, keep)
    if args.split_pages:
        return SplitSpec(Cut.PAGES, args.split_pages, keep)
    if args.split_words:
        return SplitSpec(Cut.WORDS, args.split_words, keep)
    return None


def summary_files(args: argparse.Namespace, setting: str) -> tuple[bool, bool]:
    """(the PDF summary, the Markdown summary) for this run. A flag decides for this run only
    (--summary-pdf, --no-summary-pdf, --summary-pdf-only); without one, the setting (020)."""
    if args.summary_pdf_only:
        return True, False
    if args.summary_pdf is not None:
        return args.summary_pdf, True
    return setting in {"markdown_pdf", "pdf"}, setting != "pdf"
