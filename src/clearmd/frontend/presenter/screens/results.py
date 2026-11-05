"""Results: the batch's rows and figures, and the folders that hold the converted files."""

from pathlib import Path

from clearmd.backend.api import skip_action, skip_reason, stopped_message
from clearmd.backend.schemas.models import BatchReport, OutcomeStatus
from clearmd.frontend.presenter.icons import FOLDER, icon_for, icon_of_format
from clearmd.frontend.presenter.models import ResultRow, ResultView, Tone
from clearmd.frontend.presenter.screens.choose import shown
from clearmd.frontend.presenter.screens.review import stat
from clearmd.frontend.presenter.state import AppState
from clearmd.i18n import Catalog


def result_view(catalog: Catalog, report: BatchReport, state: AppState) -> ResultView:
    count = {status: 0 for status in OutcomeStatus}
    rows: list[ResultRow] = []
    for outcome in report.outcomes:
        count[outcome.status] += 1
        source = outcome.item.source
        if outcome.status is OutcomeStatus.FAILED and outcome.error is not None:
            detail = catalog.error(outcome.error)
        elif outcome.status is OutcomeStatus.STOPPED and outcome.error is not None:
            action = catalog.text(outcome.error.action_key)
            detail = f"{stopped_message(catalog, outcome)} {action}"
        elif outcome.status is OutcomeStatus.KEPT:
            detail = catalog.text("gui.result.kept")
        else:
            continue
        icon = icon_of_format(outcome.item.detection.format)
        rows.append(ResultRow(*shown(source), detail, icon))
    for skipped in report.skipped:
        reason = skip_reason(catalog, skipped)
        detail = f"{reason}. {skip_action(catalog, skipped)}"
        icon = icon_for(skipped.path, is_folder=skipped.is_dir)
        rows.append(ResultRow(*shown(skipped.path), detail, icon))
    for root in report.unwritten_summaries:
        detail = catalog.text("gui.result.no_summary")
        rows.append(ResultRow(*shown(root), detail, FOLDER))
    for root in report.unwritten_pdfs:
        detail = catalog.text("gui.result.no_pdf_summary")
        rows.append(ResultRow(*shown(root), detail, FOLDER))
    counts = catalog.totals(
        count[OutcomeStatus.CONVERTED],
        len(report.skipped) + count[OutcomeStatus.KEPT],
        count[OutcomeStatus.FAILED],
        count[OutcomeStatus.STOPPED],
    )
    headline = catalog.text(f"gui.state.{state.value}")
    stats = [
        stat(catalog, "gui.result.stat_converted", count[OutcomeStatus.CONVERTED], Tone.ACCENT),
        stat(catalog, "gui.result.stat_skipped", len(report.skipped) + count[OutcomeStatus.KEPT]),
        stat(catalog, "gui.result.stat_failed", count[OutcomeStatus.FAILED], Tone.DANGER),
    ]
    if count[OutcomeStatus.STOPPED]:
        stats.append(stat(catalog, "gui.result.stat_stopped", count[OutcomeStatus.STOPPED]))
    folders = result_folders(report)
    return ResultView(headline, counts, tuple(rows), folders, tuple(stats))


def result_folders(report: BatchReport | None) -> tuple[Path, ...]:
    """The ClearMD_Output folders that hold converted files (none before a batch)."""
    if report is None:
        return ()
    roots = dict.fromkeys(
        outcome.item.output_root
        for outcome in report.outcomes
        if outcome.status is OutcomeStatus.CONVERTED
    )
    return tuple(roots)
