"""Reports and a writer helper shared by the summary writer's tests."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    Detection,
    DetectionMethod,
    OutcomeStatus,
    OutputRootReport,
    PlannedConversion,
    SkippedItem,
)
from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.services.summary.writer import MarkdownSummaryWriter
from clearmd.i18n import load_catalog

BOGOTA = timezone(timedelta(hours=-5))


NOW = datetime(2026, 10, 25, 15, 30, tzinfo=BOGOTA)


def _item(
    parent: Path,
    source: str,
    target: str,
    fmt: FormatId,
    *,
    by_content: bool = False,
    cost: float = 1,
) -> PlannedConversion:
    root = parent / "ClearMD_Output"
    method = DetectionMethod.CONTENT if by_content else DetectionMethod.EXTENSION
    return PlannedConversion(
        source=parent / source,
        output_root=root,
        target=root / "OutputMD" / target,
        detection=Detection(fmt, method),
        exists=False,
        cost=cost,
    )


def _report(parent: Path, *, started_at: datetime = NOW) -> OutputRootReport:
    root = parent / "ClearMD_Output"
    pdf = FormatId.PDF
    return OutputRootReport(
        root=root,
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=40),
        outcomes=(
            ConversionOutcome(
                _item(parent, "project/notes.pdf", "project/notes.md", pdf),
                OutcomeStatus.CONVERTED,
                seconds=28.4,
            ),
            ConversionOutcome(
                _item(parent, "project/scan", "project/scan.md", FormatId.DOCX, by_content=True),
                OutcomeStatus.CONVERTED,
                seconds=0.4,
            ),
            ConversionOutcome(
                _item(parent, "project/manual.pdf", "project/manual.md", pdf, cost=900),
                OutcomeStatus.STOPPED,
                ErrorCode.TIMED_OUT,
                "stopped after 600 s",
                seconds=600,
                limit=600,
            ),
            ConversionOutcome(
                _item(parent, "project/contract.pdf", "project/contract.md", pdf),
                OutcomeStatus.FAILED,
                ErrorCode.PASSWORD_PROTECTED,
                "PDFPasswordIncorrect",
                seconds=0.2,
            ),
        ),
        skipped=(
            SkippedItem(parent / "project" / ".cache", SkipReason.HIDDEN, is_dir=True),
            SkippedItem(parent / "project" / "old.md", SkipReason.ALREADY_MARKDOWN),
        ),
        cancelled=False,
    )


def _write(tmp_path: Path, language: str = "en", **kwargs: datetime) -> str:
    writer = MarkdownSummaryWriter(load_catalog(language), version="0.1.0")
    report = _report(tmp_path, **kwargs)
    report.root.mkdir(exist_ok=True)
    writer.write(report)
    return (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")


def _noted_report(tmp_path: Path, notes: tuple[ConversionNote, ...]) -> OutputRootReport:
    outcome = ConversionOutcome(
        _item(tmp_path, "thesis/main.tex", "thesis/main.md", FormatId.PDF),
        OutcomeStatus.CONVERTED,
        seconds=2,
        notes=notes,
    )
    root = tmp_path / "ClearMD_Output"
    root.mkdir(exist_ok=True)
    return OutputRootReport(root, NOW, NOW, (outcome,), (), False)
