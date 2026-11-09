"""Results: the batch's rows and figures, and the folders that hold the converted files."""

from pathlib import Path

from clearmd.backend.api import (
    error_action,
    error_text,
    large_in_report,
    skip_action,
    skip_reason,
    stopped_message,
)
from clearmd.backend.schemas.formats import MERGE_DIR_NAME, RESULTS_DIR_NAME, SPLIT_DIR_NAME
from clearmd.backend.schemas.models import BatchReport, ConversionOutcome, OutcomeStatus, tool_of
from clearmd.frontend.presenter.icons import FOLDER, icon_for, icon_of_format
from clearmd.frontend.presenter.models import ResultRow, ResultView, Tone
from clearmd.frontend.presenter.screens.choose import shown
from clearmd.frontend.presenter.screens.review import split_offer, stat
from clearmd.frontend.presenter.state import AppState
from clearmd.i18n import Catalog


def result_view(catalog: Catalog, report: BatchReport, state: AppState) -> ResultView:
    count = {status: 0 for status in OutcomeStatus}
    rows: list[ResultRow] = []
    for outcome in report.outcomes:
        count[outcome.status] += 1
        source = outcome.item.source
        if outcome.status is OutcomeStatus.FAILED and outcome.error is not None:
            detail = f"{catalog.text('gui.result.word_failed')} {error_text(catalog, outcome)}"
        elif outcome.status is OutcomeStatus.STOPPED and outcome.error is not None:
            action = error_action(catalog, outcome)
            word = catalog.text("gui.result.word_stopped")
            detail = f"{word} {stopped_message(catalog, outcome)} {action}"
        else:  # converted, and kept (the user's choice): not "what needs your attention"
            continue
        icon = icon_of_format(outcome.item.detection.format)
        rows.append(ResultRow(*shown(source), detail, icon, Tone.DANGER))
    for skipped in report.skipped:
        reason = skip_reason(catalog, skipped)
        word = catalog.text("gui.result.word_skipped")
        detail = f"{word} {reason}. {skip_action(catalog, skipped)}"
        icon = icon_for(skipped.path, is_folder=skipped.is_dir)
        rows.append(ResultRow(*shown(skipped.path), detail, icon, Tone.WARNING))
    for root in report.unwritten_summaries:
        detail = catalog.text("gui.result.no_summary")
        rows.append(ResultRow(*shown(root), detail, FOLDER))
    for root in report.unwritten_pdfs:
        detail = catalog.text("gui.result.no_pdf_summary")
        rows.append(ResultRow(*shown(root), detail, FOLDER))
    counts = catalog.totals(
        count[OutcomeStatus.CONVERTED],
        len(report.skipped),
        count[OutcomeStatus.FAILED],
        count[OutcomeStatus.STOPPED],
        tool=tool_of(outcome.item for outcome in report.outcomes),
        kept=count[OutcomeStatus.KEPT],
    )
    headline = catalog.text(f"gui.state.{state.value}")
    stats = [
        stat(catalog, "gui.result.stat_converted", count[OutcomeStatus.CONVERTED], Tone.ACCENT),
        stat(catalog, "gui.result.stat_skipped", len(report.skipped)),
        stat(catalog, "gui.result.stat_failed", count[OutcomeStatus.FAILED], Tone.DANGER),
    ]
    if count[OutcomeStatus.KEPT]:
        stats.insert(1, stat(catalog, "gui.result.stat_kept", count[OutcomeStatus.KEPT]))
    if count[OutcomeStatus.STOPPED]:
        stats.append(stat(catalog, "gui.result.stat_stopped", count[OutcomeStatus.STOPPED]))
    folders = result_folders(report)
    offer = split_offer(catalog, large_in_report(report))
    where = where_line(catalog, report)
    return ResultView(headline, counts, tuple(rows), folders, tuple(stats), offer, where)


def result_folders(report: BatchReport | None) -> tuple[Path, ...]:
    """The ClearMD_Output folders that hold results, new or kept (none before a batch)."""
    if report is None:
        return ()
    roots = dict.fromkeys(
        outcome.item.output_root for outcome in report.outcomes if outcome.status in _HAS_RESULT
    )
    roots.update(dict.fromkeys(folder for folder in report.folders if folder.is_dir()))
    return tuple(roots)


_HAS_RESULT = frozenset({OutcomeStatus.CONVERTED, OutcomeStatus.KEPT})


def where_line(catalog: Catalog, report: BatchReport) -> str:
    """Where the results are, as a path the user can read and copy (audit 2026-11-08, F3-11):
    the folder of Convert, Split or Merge inside each ClearMD_Output."""
    folders = dict.fromkeys(
        _results_folder(outcome) for outcome in report.outcomes if outcome.status in _HAS_RESULT
    )
    folders.update(dict.fromkeys(folder for folder in report.folders if folder.is_dir()))
    if not folders:
        return ""
    paths = "\n".join(str(folder) for folder in folders)
    return catalog.plural("gui.result.where", len(folders), paths=paths)


def _results_folder(outcome: ConversionOutcome) -> Path:
    item = outcome.item
    folder = {"split": SPLIT_DIR_NAME, "merge": MERGE_DIR_NAME}.get(
        tool_of([item]), RESULTS_DIR_NAME
    )
    return item.output_root / folder
