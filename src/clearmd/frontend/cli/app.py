"""CLI entry point. Thin path of slice A: files in, Markdown out, progress and exit codes (T06).

The prompt, --dry-run, --open, --output-root, --lang and exit codes 3/130 in full arrive in T16;
--no-recursive came with scanning (T08), --output-root with the output paths (T11).
"""

import argparse
import sys
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path
from typing import TextIO

from clearmd.backend.api import plan_batch, run_batch
from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    OutcomeStatus,
    PlannedConversion,
    SkippedItem,
)
from clearmd.i18n import Catalog, load_catalog, resolve_language

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_DECISION_REQUIRED = 3


def build_parser(catalog: Catalog) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clearmd", description=catalog.text("cli.help.description")
    )
    parser.add_argument(
        "paths", nargs="+", type=Path, metavar="PATH", help=catalog.text("cli.help.paths")
    )
    existing = parser.add_mutually_exclusive_group()
    existing.add_argument(
        "--overwrite", action="store_true", help=catalog.text("cli.help.overwrite")
    )
    existing.add_argument("--skip", action="store_true", help=catalog.text("cli.help.skip"))
    parser.add_argument(
        "--no-recursive", action="store_true", help=catalog.text("cli.help.no_recursive")
    )
    parser.add_argument(
        "--output-root", type=Path, metavar="DIR", help=catalog.text("cli.help.output_root")
    )
    parser.add_argument("-q", "--quiet", action="store_true", help=catalog.text("cli.help.quiet"))
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('clearmd')}")
    return parser


def share_done(seconds: float, estimated: float) -> int:
    """How far a stopped file probably got, by the estimate; never claims 100 % (AC-44)."""
    if estimated <= 0:
        return 99
    return max(1, min(99, round(100 * seconds / estimated)))


class _Progress:
    def __init__(self, catalog: Catalog, *, quiet: bool, stream: TextIO) -> None:
        self._catalog, self._quiet, self._stream = catalog, quiet, stream
        self._hinted = False

    def __call__(self, event: BatchEvent) -> None:
        if isinstance(event, ConversionStarted) and not self._quiet:
            line = self._catalog.text(
                "cli.progress", index=event.index, total=event.total, name=event.item.source.name
            )
            if event.seconds_left is not None:
                duration = self._catalog.duration(event.seconds_left)
                line = f"{line} · {self._catalog.text('cli.time_left', duration=duration)}"
            print(line, file=self._stream)
        elif isinstance(event, ConversionFinished) and event.outcome.error is not None:
            outcome = event.outcome
            assert outcome.error is not None
            name = outcome.item.source.name
            if outcome.status is OutcomeStatus.STOPPED:
                line = self._catalog.text(
                    "cli.stopped",
                    name=name,
                    elapsed=self._catalog.clock(outcome.seconds),
                    percent=share_done(outcome.seconds, outcome.item.cost),
                    action=self._catalog.text(outcome.error.action_key),
                )
            else:
                message = self._catalog.error(outcome.error)
                line = self._catalog.text("cli.failed", name=name, message=message)
            print(line, file=self._stream)
            if outcome.error is ErrorCode.PERMISSION_DENIED and not self._hinted:
                self._hinted = True
                print(self._catalog.text("cli.hint_output_root"), file=self._stream)


def _print_summary(catalog: Catalog, report: BatchReport) -> None:
    count = {status: 0 for status in OutcomeStatus}
    for outcome in report.outcomes:
        count[outcome.status] += 1
    skipped = len(report.skipped) + count[OutcomeStatus.KEPT]
    line = catalog.text(
        "cli.summary",
        converted=count[OutcomeStatus.CONVERTED],
        skipped=skipped,
        failed=count[OutcomeStatus.FAILED],
    )
    if count[OutcomeStatus.STOPPED]:
        line += catalog.text("cli.summary_stopped", stopped=count[OutcomeStatus.STOPPED])
    print(line)
    for root in dict.fromkeys(outcome.item.output_root for outcome in report.outcomes):
        print(catalog.text("cli.results", path=root))


def _shown(path: Path, is_dir: bool) -> str:
    return f"{path.name}/" if is_dir else path.name


def _skip_reason(catalog: Catalog, item: SkippedItem) -> str:
    if item.needed_memory is not None and item.memory_limit is not None:
        return catalog.text(
            item.reason.key,
            needed=catalog.gigabytes(item.needed_memory),
            limit=catalog.gigabytes(item.memory_limit),
        )
    return catalog.text(item.reason.key)


def _print_plan_notes(catalog: Catalog, plan: BatchPlan, *, quiet: bool, stream: TextIO) -> None:
    for problem in plan.input_errors:
        print(catalog.text("cli.input_not_found", path=problem.path), file=stream)
    if not quiet:
        for item in plan.skipped:
            name = _shown(item.path, item.is_dir)
            print(
                catalog.text("cli.skipped", name=name, reason=_skip_reason(catalog, item)),
                file=stream,
            )
    for warning in plan.warnings:
        line = catalog.text(
            "cli.warning_slow",
            name=warning.item.source.name,
            limit=catalog.text("time.exact_minutes", minutes=round(warning.limit_seconds / 60)),
            estimate=catalog.duration(warning.estimated_seconds),
        )
        print(line, file=stream)


def main(argv: Sequence[str] | None = None) -> int:
    catalog = load_catalog(resolve_language(None, None))
    args = build_parser(catalog).parse_args(argv)
    err = sys.stderr

    plan = plan_batch(args.paths, recursive=not args.no_recursive, output_root=args.output_root)
    _print_plan_notes(catalog, plan, quiet=args.quiet, stream=err)
    if plan.is_empty:
        if plan.input_errors and not plan.skipped:
            print(catalog.text("cli.no_valid_input"), file=err)
            return EXIT_USAGE
        print(catalog.text("cli.nothing_to_convert"))
        return EXIT_OK
    if plan.existing and not (args.overwrite or args.skip):
        print(catalog.text("cli.decision_required", count=len(plan.existing)), file=err)
        return EXIT_DECISION_REQUIRED

    def overwrite(item: PlannedConversion) -> bool:
        return bool(args.overwrite)

    report = run_batch(
        plan, overwrite=overwrite, on_event=_Progress(catalog, quiet=args.quiet, stream=err)
    )
    _print_summary(catalog, report)
    unfinished = {OutcomeStatus.FAILED, OutcomeStatus.STOPPED}
    failed = any(outcome.status in unfinished for outcome in report.outcomes)
    return EXIT_FAILED if failed else EXIT_OK
