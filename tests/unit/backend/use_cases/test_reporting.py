from datetime import UTC, datetime
from pathlib import Path

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import (
    BatchReport,
    ConversionOutcome,
    Detection,
    DetectionMethod,
    OutcomeStatus,
    PlannedConversion,
    SkippedItem,
)
from clearmd.backend.use_cases.reporting import by_output_root

NOW = datetime(2026, 10, 25, 15, 30, tzinfo=UTC)


def _outcome(root: str, name: str) -> ConversionOutcome:
    item = PlannedConversion(
        source=Path(root).parent / name,
        output_root=Path(root),
        target=Path(root) / "OutputMD" / f"{Path(name).stem}.md",
        detection=Detection(FormatId.PDF, DetectionMethod.EXTENSION),
        exists=False,
        cost=1.0,
    )
    return ConversionOutcome(item, OutcomeStatus.CONVERTED)


def test_each_output_root_gets_its_own_outcomes_and_skips() -> None:
    a, b = "/a/ClearMD_Output", "/b/ClearMD_Output"
    report = BatchReport(
        started_at=NOW,
        finished_at=NOW,
        outcomes=(_outcome(a, "x.pdf"), _outcome(b, "y.pdf"), _outcome(a, "z.pdf")),
        skipped=(
            SkippedItem(Path("/b/n.md"), SkipReason.ALREADY_MARKDOWN, output_root=Path(b)),
            SkippedItem(Path("/c/q.md"), SkipReason.ALREADY_MARKDOWN, output_root=Path("/c/x")),
        ),
        input_errors=(),
        cancelled=False,
    )
    roots = by_output_root(report)
    assert [r.root for r in roots] == [Path(a), Path(b)]
    assert [o.item.source.name for o in roots[0].outcomes] == ["x.pdf", "z.pdf"]
    assert [s.path.name for s in roots[1].skipped] == ["n.md"]
    assert roots[0].skipped == ()  # a root with nothing converted gets no summary at all
