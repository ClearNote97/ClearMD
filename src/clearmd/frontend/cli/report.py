"""What the command line prints: the summary, the plan notes, the settings warnings, the dry run."""

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from clearmd.backend.api import skipped_line
from clearmd.backend.schemas.models import BatchPlan, BatchReport, OutcomeStatus
from clearmd.backend.schemas.settings import SettingsWarning
from clearmd.i18n import Catalog, printable


def print_summary(catalog: Catalog, report: BatchReport) -> None:
    count = {status: 0 for status in OutcomeStatus}
    for outcome in report.outcomes:
        count[outcome.status] += 1
    skipped = len(report.skipped) + count[OutcomeStatus.KEPT]
    line = catalog.totals(
        count[OutcomeStatus.CONVERTED],
        skipped,
        count[OutcomeStatus.FAILED],
        count[OutcomeStatus.STOPPED],
        split=any(outcome.item.split is not None for outcome in report.outcomes),
    )
    print(line)
    for root in output_roots(report):
        print(catalog.text("cli.results", path=p(root)))
    for root in report.unwritten_summaries:
        print(catalog.text("cli.summary_not_written", path=p(root)), file=sys.stderr)
    for root in report.unwritten_pdfs:
        print(catalog.text("cli.pdf_not_written", path=p(root)), file=sys.stderr)


def summary_roots(report: BatchReport) -> list[Path]:
    """The output folders worth opening: those whose summary was written (it says what happened,
    even when every file failed). A folder refused as a link has none."""
    unwritten = set(report.unwritten_summaries)
    return [root for root in output_roots(report) if root not in unwritten]


def output_roots(report: BatchReport) -> list[Path]:
    return list(dict.fromkeys(outcome.item.output_root for outcome in report.outcomes))


def p(value: object) -> str:
    """A name or path as it may be printed: control characters escaped (security review)."""
    return printable(str(value))


def shown(path: Path, is_dir: bool) -> str:
    return p(f"{path.name}/" if is_dir else path.name)


def print_plan_notes(catalog: Catalog, plan: BatchPlan, *, quiet: bool, stream: TextIO) -> None:
    for problem in plan.input_errors:
        print(catalog.text("cli.input_not_found", path=p(problem.path)), file=stream)
    if not quiet:
        for item in plan.skipped:
            print(skipped_line(catalog, item, shown(item.path, item.is_dir)), file=stream)
    for warning in plan.warnings:
        line = catalog.text(
            "cli.warning_slow",
            name=p(warning.item.source.name),
            limit=catalog.text("time.exact_minutes", minutes=round(warning.limit_seconds / 60)),
            estimate=catalog.duration(warning.estimated_seconds),
        )
        print(line, file=stream)


def print_settings_warnings(
    catalog: Catalog, warnings: Sequence[SettingsWarning], stream: TextIO
) -> None:
    for warning in warnings:
        print(catalog.text(f"settings.{warning.problem.value}", setting=warning.key), file=stream)


def print_dry_run(catalog: Catalog, plan: BatchPlan) -> None:
    for item in plan.conversions:
        target = item.target.relative_to(item.output_root.parent)
        line = catalog.text("cli.dry_run_item", source=p(item.source), target=p(target))
        if item.exists:
            line += catalog.text("cli.dry_run_exists")
        print(line)
    split = any(item.split is not None for item in plan.conversions)
    done = "cli.dry_run_split" if split else "cli.dry_run_done"
    print(catalog.text(done, count=len(plan.conversions)))
