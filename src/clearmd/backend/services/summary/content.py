"""What a summary says, once, for every format (ADR-0031): the Markdown and the PDF are drawn from
it. Every text here is the catalog's except the names, folders and technical details, which come
from the user's files: each writer shows those safely (a code span, plain text)."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from clearmd.backend.schemas.formats import Strategy
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    OutcomeStatus,
    OutputRootReport,
    SkippedItem,
)
from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.services.rejections import skip_action, skip_reason, stopped_message
from clearmd.i18n import Catalog, printable

DATE_FORMAT = "%Y-%m-%d %H:%M"
MARKDOWN_FOLDER = "OutputMD"


class Mark(StrEnum):
    """How it went: the whole batch, or one file."""

    DONE = "done"  # ✅ everything converted
    ATTENTION = "attention"  # ⚠️ converted, with something to look at
    FAILED = "failed"  # ❌ not converted
    STOPPED = "stopped"  # ⏹️ stopped at its limit, or the batch cancelled


@dataclass(frozen=True)
class Entry:
    """One file in a list: its name and folder (from the user's files), what happened and what
    to do (the catalog's), its notes, and a technical detail."""

    mark: Mark | None
    name: str
    folder: str  # relative to where the batch started; "" in the top folder
    message: str = ""
    notes: tuple[ConversionNote, ...] = ()
    detail: str = ""
    result: str = ""  # a kept result, relative to the Markdown folder


@dataclass(frozen=True)
class Row:
    """A converted file: the table's row."""

    name: str
    folder: str
    result: str  # relative to the Markdown folder
    format: str
    time: str


@dataclass(frozen=True)
class SummaryContent:
    mark: Mark
    headline: str
    attention_line: str  # "" when nothing needs attention
    batch_line: str  # date · version · totals: the history is made of these
    attention: tuple[Entry, ...]
    converted: tuple[Row, ...]
    left_out: tuple[Entry, ...]
    kept: tuple[Entry, ...]
    cancelled: tuple[Entry, ...]


def _relative(path: Path, base: Path) -> Path:
    return path.relative_to(base) if path.is_relative_to(base) else path


def _place(path: Path, base: Path, *, folder: bool = False) -> tuple[str, str]:
    """(name, folder) of a file, the folder relative to where the batch started."""
    relative = _relative(path, base)
    parent = relative.parent.as_posix()
    name = relative.name + ("/" if folder else "")
    return name, "" if parent == "." else parent


class SummaryBuilder:
    def __init__(self, catalog: Catalog, *, version: str) -> None:
        self._catalog = catalog
        self._version = version

    def plural(self, key: str, count: int, **values: object) -> str:
        """English and Spanish need two forms: one, and every other number."""
        form = "one" if count == 1 else "other"
        return self._catalog.text(f"{key}.{form}", count=self._catalog.count(count), **values)

    def build(self, report: OutputRootReport) -> SummaryContent:
        by = {kind: [o for o in report.outcomes if o.status is kind] for kind in OutcomeStatus}
        base = report.root.parent
        markdown = report.root / MARKDOWN_FOLDER
        converted = by[OutcomeStatus.CONVERTED]
        attention = (
            [self._failed(o, base) for o in by[OutcomeStatus.FAILED]]
            + [self._stopped(o, base) for o in by[OutcomeStatus.STOPPED]]
            + [self._noted(o, base) for o in converted if o.notes]
        )
        total = len(converted) + sum(
            len(by[kind])
            for kind in (OutcomeStatus.FAILED, OutcomeStatus.STOPPED, OutcomeStatus.CANCELLED)
        )
        mark, headline = self._headline(report, len(converted), total, bool(attention))
        attention_line = self.plural("summary.attention_count", len(attention)) if attention else ""
        return SummaryContent(
            mark=mark,
            headline=headline,
            attention_line=attention_line,
            batch_line=self._batch_line(report, by),
            attention=tuple(attention),
            converted=tuple(self._row(o, base, markdown) for o in converted),
            left_out=tuple(self._skipped(item, base) for item in report.skipped),
            kept=tuple(self._kept(o, base, markdown) for o in by[OutcomeStatus.KEPT]),
            cancelled=tuple(
                Entry(Mark.STOPPED, *_place(o.item.source, base))
                for o in by[OutcomeStatus.CANCELLED]
            ),
        )

    def _headline(
        self, report: OutputRootReport, converted: int, total: int, attention: bool
    ) -> tuple[Mark, str]:
        text = self._catalog.text
        if report.cancelled:
            return Mark.STOPPED, text(
                "summary.headline.cancelled", converted=converted, total=total
            )
        if total == 0:
            return Mark.DONE, text("summary.headline.nothing_new")
        if converted == 0:
            return Mark.FAILED, self.plural("summary.headline.none", total)
        if converted < total:
            return Mark.ATTENTION, text("summary.headline.some", converted=converted, total=total)
        mark = Mark.ATTENTION if attention else Mark.DONE
        return mark, self.plural("summary.headline.all", total)

    def _batch_line(
        self, report: OutputRootReport, by: dict[OutcomeStatus, list[ConversionOutcome]]
    ) -> str:
        text = self._catalog.text
        line = " · ".join(
            [
                report.started_at.strftime(DATE_FORMAT),
                f"ClearMD {self._version}",
                text(
                    "cli.summary",
                    converted=len(by[OutcomeStatus.CONVERTED]),
                    skipped=len(report.skipped) + len(by[OutcomeStatus.KEPT]),
                    failed=len(by[OutcomeStatus.FAILED]),
                ),
            ]
        )
        if by[OutcomeStatus.STOPPED]:
            line += text("cli.summary_stopped", stopped=len(by[OutcomeStatus.STOPPED]))
        if report.cancelled:
            line += f" · {text('summary.batch_cancelled')}"
        return line

    def _failed(self, outcome: ConversionOutcome, base: Path) -> Entry:
        assert outcome.error is not None
        detail = printable(" ".join(outcome.detail.split()))
        return Entry(
            Mark.FAILED,
            *_place(outcome.item.source, base),
            self._catalog.error(outcome.error),
            detail=detail,
        )

    def _stopped(self, outcome: ConversionOutcome, base: Path) -> Entry:
        assert outcome.error is not None
        message = self._catalog.text(
            "summary.stopped_line",
            message=stopped_message(self._catalog, outcome),
            elapsed=self._catalog.clock(outcome.seconds),
            percent=outcome.share_done,
            action=self._catalog.text(outcome.error.action_key),
        )
        return Entry(Mark.STOPPED, *_place(outcome.item.source, base), message)

    def _noted(self, outcome: ConversionOutcome, base: Path) -> Entry:
        message = self._catalog.text("summary.converted_but")
        return Entry(
            Mark.ATTENTION, *_place(outcome.item.source, base), message, notes=outcome.notes
        )

    def _skipped(self, item: SkippedItem, base: Path) -> Entry:
        reason = skip_reason(self._catalog, item)
        message = f"{reason[:1].upper()}{reason[1:]}. {skip_action(self._catalog, item)}"
        return Entry(None, *_place(item.path, base, folder=item.is_dir), message)

    def _kept(self, outcome: ConversionOutcome, base: Path, markdown: Path) -> Entry:
        result = _relative(outcome.item.target, markdown).as_posix()
        return Entry(None, *_place(outcome.item.source, base), result=result)

    def _row(self, outcome: ConversionOutcome, base: Path, markdown: Path) -> Row:
        detection = outcome.item.detection
        fmt = detection.format.value.upper()
        if outcome.item.strategy is not Strategy.FULL:
            fmt = self._catalog.text(f"summary.strategy.{outcome.item.strategy}", format=fmt)
        if detection.by_content:
            fmt = self._catalog.text("summary.by_content", format=fmt)
        name, folder = _place(outcome.item.source, base)
        result = _relative(outcome.item.target, markdown).as_posix()
        return Row(name, folder, result, fmt, self.time(outcome.seconds))

    def time(self, seconds: float) -> str:
        if seconds < 1:
            return self._catalog.text("time.under_a_second")
        if seconds < 60:
            return self._catalog.text("time.seconds", seconds=round(seconds))
        return self._catalog.clock(seconds)
