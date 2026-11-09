"""Resumen_ClearMD.md: content per language and notes (AC-28, AC-41)."""

from pathlib import Path

import pytest
from support.summary_cases import NOW, _item, _write

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
from clearmd.backend.services.summary.writer import MarkdownSummaryWriter
from clearmd.i18n import load_catalog

EXPECTED_EN = "\n".join(
    [
        "# ClearMD Summary",
        "",
        "⚠️ **2 of 4 documents were converted.** 2 things need your attention.",
        "",
        "2026-10-25 15:30 · ClearMD 0.1.0 · 2 converted · 2 skipped · 1 failed · 1 stopped",
        "",
        "## Where Your Files Are",
        "Your Markdown files are in the `OutputMD/` folder, next to this summary.",
        "",
        "## Needs Your Attention",
        "- ❌ `contract.pdf` in `project` — This file is password-protected. Remove the password and try again.",  # noqa: E501 (the summary as written)
        "  <details><summary>Technical Detail</summary>PDFPasswordIncorrect</details>",
        "- ⏹️ `manual.pdf` in `project` — It went 10 min without moving. Estimated progress: 67% after 10:00. Try splitting it into smaller parts with Split.",  # noqa: E501 (the summary as written)
        "",
        "## Converted",
        "| Document | Folder | Result | Format | Time |",
        "|---|---|---|---|---|",
        "| `notes.pdf` | `project` | `notes.md` | PDF | 28 s |",
        "| `scan` | `project` | `scan.md` | DOCX, detected by content | <1 s |",
        "",
        "## Left Out",
        "- `.cache/` in `project` — Hidden file. Make it visible to convert it.",
        "- `old.md` in `project` — Already Markdown. It needs no conversion.",
        "",
        "<details>",
        "<summary>History</summary>",
        "",
        "<!-- clearmd:history -->",
        "_No earlier tasks here._",
        "<!-- /clearmd:history -->",
        "",
        "</details>",
        "",
    ]
)


def test_the_summary_in_english(tmp_path: Path) -> None:
    assert _write(tmp_path) == EXPECTED_EN


def test_the_summary_in_spanish(tmp_path: Path) -> None:
    text = _write(tmp_path, "es")
    assert text.startswith("# Resumen de ClearMD\n\n⚠️ **Se convirtieron 2 de 4 documentos.**")
    assert "\n2026-10-25 15:30 · ClearMD 0.1.0 · 2 convertidos" in text
    for heading in (
        "## Dónde Están Tus Archivos",
        "## Necesita Tu Atención",
        "## Convertidos",
        "## No Incluidos",
        "<summary>Historial</summary>",
    ):
        assert heading in text
    assert "| Documento | Carpeta | Resultado | Formato | Tiempo |" in text
    assert "DOCX, detectado por su contenido" in text
    assert "Este archivo está protegido con contraseña." in text


def test_kept_and_cancelled_items_have_their_sections(tmp_path: Path) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    kept = ConversionOutcome(_item(tmp_path, "a.pdf", "a.md", FormatId.PDF), OutcomeStatus.KEPT)
    gone = ConversionOutcome(
        _item(tmp_path, "b.pdf", "b.md", FormatId.PDF), OutcomeStatus.CANCELLED
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (kept, gone), (), True)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "## Kept (the Output Already Existed)\n- `a.pdf` → `a.md`" in text
    assert "## Cancelled\n- ⏹️ `b.pdf`" in text
    assert text.splitlines()[4].endswith(" · cancelled")  # the batch line


def test_c9_1_nothing_tried_and_something_left_out_is_no_success(tmp_path: Path) -> None:
    kept = ConversionOutcome(_item(tmp_path, "a.pdf", "a.md", FormatId.PDF), OutcomeStatus.KEPT)
    left = SkippedItem(tmp_path / "b.xyz", SkipReason.UNSUPPORTED_FORMAT)
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (kept,), (left,), False)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert text.splitlines()[2] == "⚠️ **Nothing was converted: see what was left out.**"


def test_c9_2_the_folder_is_the_results_never_an_absolute_path(tmp_path: Path) -> None:
    chosen = tmp_path / "elsewhere" / "ClearMD_Output"
    item = PlannedConversion(
        source=tmp_path / "Documents" / "top.txt",
        output_root=chosen,
        target=chosen / "OutputMD" / "Documents" / "top.md",
        detection=Detection(FormatId.TXT, DetectionMethod.EXTENSION),
        exists=False,
        cost=1,
    )
    report = OutputRootReport(
        chosen, NOW, NOW, (ConversionOutcome(item, OutcomeStatus.CONVERTED),), (), False
    )
    chosen.mkdir(parents=True)
    MarkdownSummaryWriter(load_catalog("en"), version="0.1.0").write(report)
    text = (chosen / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "| `top.txt` | `Documents` | `top.md` |" in text and str(tmp_path) not in text


@pytest.mark.parametrize(
    ("language", "counts", "headline"),
    [
        ("es", (1, 2), "⚠️ **Se convirtió 1 de 3 documentos.**"),
        ("en", (1, 2), "⚠️ **1 of 3 documents was converted.**"),
        ("es", (2, 1), "⚠️ **Se convirtieron 2 de 3 documentos.**"),
    ],
)
def test_c9_7_singular_and_plural(
    tmp_path: Path, language: str, counts: tuple[int, int], headline: str
) -> None:
    converted, failed = counts
    outcomes = tuple(
        ConversionOutcome(_item(tmp_path, f"c{n}.pdf", f"c{n}.md", FormatId.PDF),
                          OutcomeStatus.CONVERTED)
        for n in range(converted)
    ) + tuple(
        ConversionOutcome(_item(tmp_path, f"f{n}.pdf", f"f{n}.md", FormatId.PDF),
                          OutcomeStatus.FAILED, ErrorCode.CORRUPT_FILE)
        for n in range(failed)
    )  # fmt: skip
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, outcomes, (), False)
    report.root.mkdir()
    MarkdownSummaryWriter(load_catalog(language), version="0.1.0").write(report)
    lines = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8").splitlines()
    assert lines[2].startswith(headline)
    if language == "es" and converted == 1:
        assert "1 convertido · 0 omitidos · 2 con error" in lines[4]
