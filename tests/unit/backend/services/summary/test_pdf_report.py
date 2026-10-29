"""Resumen_ClearMD.pdf (feature 009, ADR-0031): the summary's content, read back with PDFium."""

import re
from datetime import timedelta
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionOutcome, OutcomeStatus, OutputRootReport
from clearmd.backend.services.summary.pdf_report import PdfReport
from clearmd.i18n import load_catalog

from .test_writer import NOW, _item, _report


def write(report: OutputRootReport, language: str = "en") -> Path:
    report.root.mkdir(exist_ok=True)
    PdfReport(load_catalog(language), version="0.4.0").write(report)
    return report.root / "Resumen_ClearMD.pdf"


def text_of(path: Path) -> str:
    document = pdfium.PdfDocument(str(path))
    try:
        return "\n".join(page.get_textpage().get_text_range() for page in document)
    finally:
        document.close()


def test_the_pdf_says_what_the_markdown_says(tmp_path: Path) -> None:
    text = text_of(write(_report(tmp_path)))
    for expected in (
        "ClearMD summary",
        "2 of 4 documents were converted. 2 things need your attention.",
        "2026-10-25 15:30 · ClearMD 0.4.0 · 2 converted · 2 skipped · 1 failed · 1 stopped",
        "Where your files are",
        "Needs your attention",
        "contract.pdf in project — This file is password-protected.",
        "Technical detail: PDFPasswordIncorrect",
        "Converted",
        "notes.pdf project project/notes.md PDF 28 s",
        "Left out",
        ".cache/ in project — Hidden file.",
    ):
        assert expected in text, expected


def test_the_pdf_in_spanish(tmp_path: Path) -> None:
    text = text_of(write(_report(tmp_path), "es"))
    assert "Resumen de ClearMD" in text
    assert "Se convirtieron 2 de 4 documentos. 2 cosas necesitan tu atención." in text
    assert "Este archivo está protegido con contraseña." in text


def test_the_pdf_is_small_and_holds_no_link_or_action(tmp_path: Path) -> None:
    data = write(_report(tmp_path)).read_bytes()
    assert len(data) < 20_000  # standard fonts: nothing embedded
    forbidden = (
        b"/URI",
        b"/JavaScript",
        b"/JS",
        b"/Launch",
        b"/OpenAction",
        b"/AA",
        b"/EmbeddedFile",
    )
    assert not [key for key in forbidden if key in data]


def test_hostile_names_are_drawn_as_plain_text(tmp_path: Path) -> None:
    names = ["evil\nline.pdf", "名前.pdf", "a‮b.pdf", "(x) /JavaScript.pdf"]
    outcomes = tuple(
        ConversionOutcome(_item(tmp_path, name, f"{n}.md", FormatId.PDF), OutcomeStatus.CONVERTED)
        for n, name in enumerate(names)
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, outcomes, (), False)
    path = write(report)
    text = text_of(path)
    assert "evil\\x0aline.pdf" in text  # control characters shown escaped, on one line
    assert "??.pdf" in text  # outside the standard fonts: "?" (the Markdown keeps the name)
    assert "JavaScript.pdf" in text and "(x)" in text  # a name is text, never a PDF action
    assert b"/JavaScript" not in path.read_bytes()


def test_a_long_batch_goes_on_over_pages_with_their_numbers(tmp_path: Path) -> None:
    outcomes = tuple(
        ConversionOutcome(
            _item(tmp_path, f"folder/document-{n:03d}.pdf", f"folder/document-{n:03d}.md",
                  FormatId.PDF),
            OutcomeStatus.FAILED if n % 7 == 0 else OutcomeStatus.CONVERTED,
            ErrorCode.CORRUPT_FILE if n % 7 == 0 else None,
            seconds=1.5,
        )
        for n in range(150)
    )  # fmt: skip
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW + timedelta(minutes=3),
                              outcomes, (), False)  # fmt: skip
    path = write(report)
    document = pdfium.PdfDocument(str(path))
    pages = len(document)
    document.close()
    text = text_of(path)
    assert pages >= 3
    assert all(f"document-{n:03d}.pdf" in text for n in range(150))
    assert re.search(rf"ClearMD summary · {pages}\b", text)  # the last page's footer


def test_a_name_too_long_for_a_line_is_cut_never_lost_off_the_page(tmp_path: Path) -> None:
    name = "a" * 300 + ".pdf"
    outcome = ConversionOutcome(
        _item(tmp_path, name, "x.md", FormatId.PDF), OutcomeStatus.FAILED, ErrorCode.CORRUPT_FILE
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    text = text_of(write(report))
    assert text.replace("\r", "").replace("\n", "").count("a" * 50) >= 1
    assert "This file seems to be damaged." in text


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_mark_and_section_draws(tmp_path: Path, language: str) -> None:
    kept = ConversionOutcome(_item(tmp_path, "a.pdf", "a.md", FormatId.PDF), OutcomeStatus.KEPT)
    gone = ConversionOutcome(
        _item(tmp_path, "b.pdf", "b.md", FormatId.PDF), OutcomeStatus.CANCELLED
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (kept, gone), (), True)
    text = text_of(write(report, language))
    assert "a.pdf » a.md" in text and "b.pdf" in text
