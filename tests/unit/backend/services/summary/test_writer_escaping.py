"""Resumen_ClearMD.md: escaping of names and details."""

from pathlib import Path

import pytest
from support.summary_cases import NOW, _item

from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    OutcomeStatus,
    OutputRootReport,
)
from clearmd.backend.services.summary.writer import MarkdownSummaryWriter
from clearmd.i18n import load_catalog


@pytest.mark.parametrize(
    ("name", "shown"),
    [
        ("a|b.pdf", "`a\\|b.pdf`"),
        ("tick`name.pdf", "`` tick`name.pdf ``"),
    ],
)
def test_untrusted_names_cannot_break_the_table(tmp_path: Path, name: str, shown: str) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    outcome = ConversionOutcome(
        _item(tmp_path, name, "x.md", FormatId.PDF), OutcomeStatus.CONVERTED, seconds=1
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    report.root.mkdir()
    writer.write(report)
    lines = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8").splitlines()
    row = lines[lines.index("|---|---|---|---|---|") + 1]
    assert row.startswith(f"| {shown} |") and row.count(" | ") == 4  # still five cells


def test_technical_details_cannot_inject_html(tmp_path: Path) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    outcome = ConversionOutcome(
        _item(tmp_path, "x.pdf", "x.md", FormatId.PDF),
        OutcomeStatus.FAILED,
        ErrorCode.CONVERSION_FAILED,
        "ValueError: <script>alert(1)</script> & more",
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "<script>" not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; more" in text


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("a``b.pdf", "``` a``b.pdf ```"),
        ("evil\n- injected.pdf", "`evil\\x0a- injected.pdf`"),
        # A "/" makes it a folder and a name: both stay code spans.
        ("fake<!-- /clearmd:history -->.pdf", "`clearmd:history -->.pdf`"),
    ],
)
def test_names_cannot_escape_their_code_span_or_line(
    tmp_path: Path, name: str, expected: str
) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    outcome = ConversionOutcome(
        _item(tmp_path, name, "x.md", FormatId.PDF),
        OutcomeStatus.FAILED,
        ErrorCode.CORRUPT_FILE,
        "x",
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert f"- ❌ {expected} — " in text
    assert text.split("\n").count("<!-- /clearmd:history -->") == 1  # only ClearMD's own marker
    assert "\n- injected" not in text


def test_a_technical_detail_stays_on_one_line(tmp_path: Path) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    outcome = ConversionOutcome(
        _item(tmp_path, "x.pdf", "x.md", FormatId.PDF),
        OutcomeStatus.FAILED,
        ErrorCode.CONVERSION_FAILED,
        "line one\n\n# Injected heading\nline two",
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "\n# Injected heading" not in text
    assert "line one # Injected heading line two" in text
