"""What a summary says, once, for every format (ADR-0031): the Markdown and the PDF are drawn from
it. Every text here is the catalog's except the names, folders and technical details, which come
from the user's files: each writer shows those safely (a code span, plain text)."""

from pathlib import Path

from clearmd.backend.schemas.formats import Strategy
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    OutcomeStatus,
    OutputRootReport,
    SkippedItem,
    tool_of,
)
from clearmd.backend.services.rejections import (
    error_action,
    error_text,
    skip_action,
    skip_reason,
    stopped_message,
)
from clearmd.backend.services.summary.model import (
    DATE_FORMAT,
    FOLDERS,
    MARKDOWN_FOLDER,
    Entry,
    Mark,
    Row,
    SummaryContent,
)
from clearmd.i18n import Catalog, printable


def _relative(path: Path, base: Path) -> Path:
    return path.relative_to(base) if path.is_relative_to(base) else path


def _folder(path: Path) -> str:
    parent = path.as_posix()
    return "" if parent == "." else parent


def _converted_place(outcome: ConversionOutcome, markdown: Path) -> tuple[str, str]:
    """(name, folder): the folder is the result's, inside the Markdown folder (OutputSep for a
    split file), the same for every output choice (code review of 009: never a long absolute
    path)."""
    folder = FOLDERS[tool_of([outcome.item])]
    if folder != MARKDOWN_FOLDER:  # OutputSep (023), OutputUnif (026)
        markdown = markdown.parent / folder
    target = _relative(outcome.item.target, markdown)
    return outcome.item.source.name, _folder(target.parent)


def _skipped_place(item: SkippedItem, base: Path) -> tuple[str, str]:
    """(name, folder) of a file left out: its folder as its results would have been placed,
    from the folder above the input it was found under."""
    above = item.input.parent if item.input is not None else base
    relative = _relative(item.path, above)
    return relative.name + ("/" if item.is_dir else ""), _folder(relative.parent)


class SummaryBuilder:
    def __init__(self, catalog: Catalog, *, version: str) -> None:
        self._catalog = catalog
        self._version = version
        self._tool = "convert"

    def plural(self, key: str, count: int, **values: object) -> str:
        if self._tool != "convert" and key.startswith("summary.headline."):  # split, merged
            key = f"summary.{self._tool}_headline." + key.removeprefix("summary.headline.")
        return self._catalog.plural(key, count, **values)

    def build(self, report: OutputRootReport) -> SummaryContent:
        by = {kind: [o for o in report.outcomes if o.status is kind] for kind in OutcomeStatus}
        self._tool = tool_of(outcome.item for outcome in report.outcomes)
        base = report.root.parent
        markdown = report.root / MARKDOWN_FOLDER
        converted = by[OutcomeStatus.CONVERTED]
        attention = (
            [self._failed(o, markdown) for o in by[OutcomeStatus.FAILED]]
            + [self._stopped(o, markdown) for o in by[OutcomeStatus.STOPPED]]
            + [self._noted(o, markdown) for o in converted if o.worth_a_look]
        )
        cleaned = [o for o in converted if o.notes and not o.worth_a_look]
        total = len(converted) + sum(
            len(by[kind])
            for kind in (OutcomeStatus.FAILED, OutcomeStatus.STOPPED, OutcomeStatus.CANCELLED)
        )
        mark, headline = self._headline(
            report, len(converted), total, bool(attention), by[OutcomeStatus.KEPT]
        )
        attention_line = self.plural("summary.attention_count", len(attention)) if attention else ""
        return SummaryContent(
            mark=mark,
            headline=headline,
            attention_line=attention_line,
            batch_line=self._batch_line(report, by),
            attention=tuple(attention),
            converted=tuple(self._row(o, markdown) for o in converted),
            left_out=tuple(self._skipped(item, base) for item in report.skipped),
            kept=tuple(self._kept(o, markdown) for o in by[OutcomeStatus.KEPT]),
            cancelled=tuple(
                Entry(Mark.STOPPED, *_converted_place(o, markdown))
                for o in by[OutcomeStatus.CANCELLED]
            ),
            tool=self._tool,
            cleaned=tuple(
                Entry(None, *_converted_place(o, markdown), notes=o.notes) for o in cleaned
            ),
        )

    def _headline(
        self,
        report: OutputRootReport,
        converted: int,
        total: int,
        attention: bool,
        kept: list[ConversionOutcome],
    ) -> tuple[Mark, str]:
        count = self._catalog.count
        if report.cancelled:
            headline = self.plural("summary.headline.cancelled", converted, total=count(total))
            return Mark.STOPPED, headline
        if total == 0:
            if report.skipped:  # nothing tried, and something left out: worth a look
                return Mark.ATTENTION, self.plural("summary.headline.nothing", len(kept))
            return Mark.DONE, self.plural("summary.headline.nothing_new", len(kept))
        if converted == 0:
            return Mark.FAILED, self.plural("summary.headline.none", total)
        if converted < total:
            headline = self.plural("summary.headline.some", converted, total=count(total))
            return Mark.ATTENTION, headline
        mark = Mark.ATTENTION if attention else Mark.DONE
        return mark, self.plural("summary.headline.all", total)

    def _batch_line(
        self, report: OutputRootReport, by: dict[OutcomeStatus, list[ConversionOutcome]]
    ) -> str:
        totals = self._catalog.totals(
            len(by[OutcomeStatus.CONVERTED]),
            len(report.skipped),
            len(by[OutcomeStatus.FAILED]),
            len(by[OutcomeStatus.STOPPED]),
            tool=self._tool,
            kept=len(by[OutcomeStatus.KEPT]),
        )
        parts = [report.started_at.strftime(DATE_FORMAT), f"ClearMD {self._version}", totals]
        if report.cancelled:
            parts.append(self._catalog.text("summary.batch_cancelled"))
        return " · ".join(parts)

    def _failed(self, outcome: ConversionOutcome, markdown: Path) -> Entry:
        assert outcome.error is not None
        detail = printable(" ".join(outcome.detail.split()))
        return Entry(
            Mark.FAILED,
            *_converted_place(outcome, markdown),
            error_text(self._catalog, outcome),
            detail=detail,
        )

    def _stopped(self, outcome: ConversionOutcome, markdown: Path) -> Entry:
        assert outcome.error is not None
        message = self._catalog.text(
            "summary.stopped_line",
            message=stopped_message(self._catalog, outcome),
            elapsed=self._catalog.clock(outcome.seconds),
            percent=outcome.share_done,
            action=error_action(self._catalog, outcome),
        )
        return Entry(Mark.STOPPED, *_converted_place(outcome, markdown), message)

    def _noted(self, outcome: ConversionOutcome, markdown: Path) -> Entry:
        message = self._catalog.text(
            "summary.converted_but" if self._tool == "convert" else f"summary.{self._tool}_but"
        )
        return Entry(
            Mark.ATTENTION, *_converted_place(outcome, markdown), message, notes=outcome.notes
        )

    def _skipped(self, item: SkippedItem, base: Path) -> Entry:
        reason = skip_reason(self._catalog, item)
        message = f"{reason[:1].upper()}{reason[1:]}. {skip_action(self._catalog, item)}"
        return Entry(None, *_skipped_place(item, base), message)

    def _kept(self, outcome: ConversionOutcome, markdown: Path) -> Entry:
        name, folder = _converted_place(outcome, markdown)
        return Entry(None, name, folder, result=outcome.item.target.name)

    def _row(self, outcome: ConversionOutcome, markdown: Path) -> Row:
        detection = outcome.item.detection
        fmt = detection.format.value.upper()
        if outcome.item.strategy is not Strategy.FULL:
            fmt = self._catalog.text(f"summary.strategy.{outcome.item.strategy}", format=fmt)
        if detection.by_content:
            fmt = self._catalog.text("summary.by_content", format=fmt)
        name, folder = _converted_place(outcome, markdown)
        result = outcome.item.target.name
        if outcome.item.split is not None:  # the parts' folder, and how many (feature 023)
            result = self.plural("summary.parts", outcome.parts, folder=f"{result}/")
        return Row(name, folder, result, fmt, self.time(outcome.seconds))

    def time(self, seconds: float) -> str:
        if seconds < 1:
            return self._catalog.text("time.under_a_second")
        if seconds < 60:
            return self._catalog.text("time.seconds", seconds=round(seconds))
        return self._catalog.clock(seconds)
