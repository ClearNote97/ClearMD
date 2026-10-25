"""Write Resumen_ClearMD.md for one output folder (ADR-0016; AC-22, AC-28, AC-29, AC-41)."""

import html
from collections.abc import Iterable
from pathlib import Path

from clearmd.backend.schemas.formats import SUMMARY_NAME
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    OutcomeStatus,
    OutputRootReport,
    SkippedItem,
)
from clearmd.backend.use_cases.output_files import UnsafeOutput, atomic_write, read_regular_file
from clearmd.i18n import Catalog

HISTORY_START = "<!-- clearmd:history -->"
HISTORY_END = "<!-- /clearmd:history -->"
HISTORY_LIMIT = 200
DATE_FORMAT = "%Y-%m-%d %H:%M"


def _code(text: str) -> str:
    """A code span that a backtick in a (untrusted) file name cannot close."""
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def _cell(text: str) -> str:
    return _code(text).replace("|", "\\|")


def _relative(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix() if path.is_relative_to(base) else str(path)


def _previous_history(summary: Path) -> tuple[list[str], bool]:
    """Earlier batches, newest first, and whether a previous summary could not be read."""
    try:
        text = read_regular_file(summary)  # a planted link is never read through
    except (UnsafeOutput, OSError, UnicodeDecodeError):
        return [], True
    if text is None:
        return [], False
    if HISTORY_START not in text or HISTORY_END not in text:
        return [], True
    lines = text.splitlines()
    header = next((line for line in lines[1:] if line.strip()), "")
    inside = text.split(HISTORY_START, 1)[1].split(HISTORY_END, 1)[0]
    earlier = [line for line in inside.splitlines() if line.startswith("- ")]
    return [f"- {header}", *earlier], False


class MarkdownSummaryWriter:
    """A ``SummaryWriter``: one Markdown file per ClearMD_Output folder, in the user's language."""

    def __init__(self, catalog: Catalog, *, version: str) -> None:
        self._catalog = catalog
        self._version = version

    def write(self, report: OutputRootReport) -> None:
        path = report.root / SUMMARY_NAME
        history, unreadable = _previous_history(path)
        rendered = self.render(report, history[:HISTORY_LIMIT], unreadable)
        atomic_write(path, rendered, inside=report.root)

    def render(self, report: OutputRootReport, history: list[str], unreadable: bool) -> str:
        text = self._catalog.text
        status = {kind: [o for o in report.outcomes if o.status is kind] for kind in OutcomeStatus}
        base, root = report.root.parent, report.root

        def source(outcome: ConversionOutcome) -> str:
            return _code(_relative(outcome.item.source, base))

        lines = [f"# {text('summary.title')}", self._header(report, status), ""]
        if status[OutcomeStatus.CONVERTED]:
            lines += [
                f"## {text('summary.converted')}",
                f"| {text('summary.col_source')} | {text('summary.col_output')} "
                f"| {text('summary.col_format')} | {text('summary.col_time')} |",
                "|---|---|---|---|",
                *(self._row(o, base, root) for o in status[OutcomeStatus.CONVERTED]),
                "",
            ]
        stopped = (f"- {source(o)} — {self._stopped(o)}" for o in status[OutcomeStatus.STOPPED])
        kept = (
            f"- {source(o)} → {_code(_relative(o.item.target, root))}"
            for o in status[OutcomeStatus.KEPT]
        )
        lines += self._section("summary.stopped", stopped)
        lines += self._section("summary.failed", self._failed(status[OutcomeStatus.FAILED], base))
        lines += self._section("summary.skipped", (self._skipped(i, base) for i in report.skipped))
        lines += self._section("summary.kept", kept)
        cancelled = (f"- {source(o)}" for o in status[OutcomeStatus.CANCELLED])
        lines += self._section("summary.cancelled", cancelled)
        lines += [HISTORY_START, f"## {text('summary.history')}"]
        if unreadable:
            lines.append(f"_{text('summary.history_restarted')}_")
        lines += [*history, HISTORY_END]
        return "\n".join(lines) + "\n"

    def _header(
        self, report: OutputRootReport, by_status: dict[OutcomeStatus, list[ConversionOutcome]]
    ) -> str:
        text = self._catalog.text
        parts = [
            report.started_at.strftime(DATE_FORMAT),
            f"ClearMD {self._version}",
            text(
                "cli.summary",
                converted=len(by_status[OutcomeStatus.CONVERTED]),
                skipped=len(report.skipped) + len(by_status[OutcomeStatus.KEPT]),
                failed=len(by_status[OutcomeStatus.FAILED]),
            ),
        ]
        header = " · ".join(parts)
        if by_status[OutcomeStatus.STOPPED]:
            header += text("cli.summary_stopped", stopped=len(by_status[OutcomeStatus.STOPPED]))
        if report.cancelled:
            header += f" · {text('summary.batch_cancelled')}"
        return header

    def _section(self, key: str, items: Iterable[str]) -> list[str]:
        body = list(items)
        return [f"## {self._catalog.text(key)}", *body, ""] if body else []

    def _row(self, outcome: ConversionOutcome, base: Path, root: Path) -> str:
        detection = outcome.item.detection
        fmt = detection.format.value.upper()
        if detection.by_content:
            fmt = self._catalog.text("summary.by_content", format=fmt)
        source = _cell(_relative(outcome.item.source, base))
        target = _cell(_relative(outcome.item.target, root))
        return f"| {source} | {target} | {fmt} | {self._time(outcome.seconds)} |"

    def _time(self, seconds: float) -> str:
        if seconds < 1:
            return self._catalog.text("time.under_a_second")
        if seconds < 60:
            return self._catalog.text("time.seconds", seconds=round(seconds))
        return self._catalog.clock(seconds)

    def _stopped(self, outcome: ConversionOutcome) -> str:
        assert outcome.error is not None
        return self._catalog.text(
            "summary.stopped_line",
            elapsed=self._catalog.clock(outcome.seconds),
            percent=outcome.share_done,
            action=self._catalog.text(outcome.error.action_key),
        )

    def _failed(self, outcomes: list[ConversionOutcome], base: Path) -> Iterable[str]:
        summary = self._catalog.text("summary.technical_detail")
        for outcome in outcomes:
            assert outcome.error is not None
            message = self._catalog.error(outcome.error)
            yield f"- {_code(_relative(outcome.item.source, base))} — {message}"
            if outcome.detail:
                detail = html.escape(outcome.detail, quote=False)
                yield f"  <details><summary>{summary}</summary>{detail}</details>"

    def _skipped(self, item: SkippedItem, base: Path) -> str:
        shown = _relative(item.path, base) + ("/" if item.is_dir else "")
        if item.needed_memory is not None and item.memory_limit is not None:
            reason = self._catalog.text(
                item.reason.key,
                needed=self._catalog.gigabytes(item.needed_memory),
                limit=self._catalog.gigabytes(item.memory_limit),
            )
        else:
            reason = self._catalog.text(item.reason.key)
        return f"- {_code(shown)} — {reason}"
