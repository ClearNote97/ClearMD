"""Feature 008 — one test per acceptance criterion (spec/features/008_*/spec.md), on PDFs written
for each case (the author's own PDFs are never in the repository)."""

import importlib.util
import tomllib
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR
from support.markdown_guarantee import live_syntax
from support.pdf_builder import GLYPH_CODE, Text, build_pdf, paragraph

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.pdf import PdfConverter
from clearmd.backend.services.conversion.registry import build_registry
from clearmd.i18n import load_catalog

ROOT = Path(__file__).resolve().parents[2]
DETECTION = Detection(FormatId.PDF, DetectionMethod.EXTENSION)
BODY = [
    "In this paper, Data Envelopment Analysis is used to calculate the technical",
    "efficiency of the municipal and circuit courts of the ordinary jurisdiction",
    "of the Colombian criminal justice system, from 2012 to 2016.",
]
PDF_NOTES = [kind for kind in NoteKind if kind.value.startswith("pdf_")]


def convert(tmp_path: Path, pages: list[list[Text]]) -> ConversionResult:
    source = tmp_path / "paper.pdf"
    source.write_bytes(build_pdf(pages))
    return PdfConverter().convert(source, DETECTION, tmp_path / "paper.md")


def kinds(result: ConversionResult) -> set[NoteKind]:
    return {note.kind for note in result.notes}


SECTIONS = ["Introduction", "Literature Review", "Methodology", "Results", "Conclusions"]


def article(pages: int) -> list[list[Text]]:
    """Each page with its own section and text, under the same running header and its number."""
    return [
        [
            Text("Rev. Law Econ. 2022", 760, 8),
            Text("Evaluating Criminal Justice", 720, 16) if number == 1 else Text("", 0),
            Text(f"{number} {SECTIONS[number - 1]}", 690, 11, "bold"),
            *paragraph([f"{SECTIONS[number - 1]}: {line}" for line in BODY], top=670),
            Text(str(number), 40, 8),
        ]
        for number in range(1, pages + 1)
    ]


def test_ac_01_words_keep_their_spaces_and_upside_down_text_reads_right(tmp_path: Path) -> None:
    page = [*paragraph(BODY, top=700), Text("Number of solved cases", 300, rotated=True)]
    markdown = convert(tmp_path, [page]).markdown
    assert "calculate the technical efficiency of the municipal" in markdown
    assert "Number of solved cases" in markdown


def test_ac_02_a_font_without_a_character_map_is_read_back_and_told(tmp_path: Path) -> None:
    title = (
        f"PROGRAMA ACADÉMICO DE MAESTR{GLYPH_CODE}\xcbA en Gestión"  # Í: past the standard order
    )
    page = [Text(title, 700, 18, "glyphs"), *paragraph(BODY, top=650)]
    result = convert(tmp_path, [page])
    assert "PROGRAMA ACADÉMICO DE MAESTR�A en Gestión" in result.markdown  # never a wrong letter
    assert {NoteKind.PDF_TEXT_DECODED, NoteKind.PDF_TEXT_UNREADABLE} <= kinds(result)


def test_ac_03_a_page_without_text_is_told_and_nothing_is_guessed(tmp_path: Path) -> None:
    result = convert(tmp_path, [paragraph(BODY, top=700), []])
    note = next(note for note in result.notes if note.kind is NoteKind.PDF_PAGES_WITHOUT_TEXT)
    assert [item.subject for item in note.items] == ["2"]


@pytest.mark.parametrize(
    ("name", "code"),
    [("encrypted.pdf", ErrorCode.PASSWORD_PROTECTED), ("corrupt.pdf", ErrorCode.CORRUPT_FILE)],
)
def test_ac_04_a_locked_or_broken_pdf_fails_with_its_reason(
    tmp_path: Path, name: str, code: ErrorCode
) -> None:
    with pytest.raises(ConversionError) as raised:
        PdfConverter().convert(DOCUMENTS_DIR / name, DETECTION, tmp_path / "x.md")
    assert raised.value.code is code


def test_ac_05_running_lines_and_page_numbers_go_also_in_a_short_document(
    tmp_path: Path,
) -> None:
    long = convert(tmp_path, article(5))
    assert "Rev. Law Econ." not in long.markdown
    assert not any(line.strip().isdigit() for line in long.markdown.splitlines())
    assert NoteKind.PDF_RUNNING_REMOVED in kinds(long)
    # ADR-0030 amended (audit v4, B3-02): on every page of a short document, it goes too.
    short = convert(tmp_path, article(2))
    assert "Rev. Law Econ." not in short.markdown
    one = convert(tmp_path, article(1))  # one page keeps everything
    assert one.markdown.count("Rev. Law Econ.") == 1


def test_ac_06_headings_by_size_or_bold_numbers_never_a_sentence(tmp_path: Path) -> None:
    pages = article(4)
    pages[0].append(Text("2 Jueces de Paz. El objetivo general es determinar", 600, 11, "bold"))
    lines = convert(tmp_path, pages).markdown.splitlines()
    assert "# Evaluating Criminal Justice" in lines
    assert "## 1 Introduction" in lines and "## 4 Results" in lines
    assert not any(line.startswith("#") and "objetivo" in line for line in lines)


def test_ac_07_paragraphs_across_lines_and_pages_with_their_footnotes_after(
    tmp_path: Path,
) -> None:
    first = [
        *paragraph(["The judicial system is one of the main tenets of a modern society,"], top=700),
        *paragraph(["1 Corporación Excelencia en la Justicia."], top=80, size=8),
    ]
    second = [
        *paragraph(["because it regulates interactions between citizens."], top=700),
        *paragraph(BODY, top=640),
    ]
    blocks = convert(tmp_path, [first, second]).markdown.strip().split("\n\n")
    assert blocks[0].endswith("modern society, because it regulates interactions between citizens.")
    assert blocks[1] == "1 Corporación Excelencia en la Justicia."
    assert blocks[2] == " ".join(BODY)


def test_ac_08_broken_words_are_joined_and_bullets_are_list_items(tmp_path: Path) -> None:
    page = paragraph(
        ["the efficiency of the adminis-", "tration of justice.", "• Identify the legal framework"],
        top=700,
    )
    markdown = convert(tmp_path, [page]).markdown
    assert "the efficiency of the administration of justice." in markdown
    assert "- Identify the legal framework" in markdown.splitlines()


def test_ac_09_document_text_never_becomes_markdown_it_did_not_write(tmp_path: Path) -> None:
    hostile = ["# heading?", "[x](javascript:alert(1))", "<img src=x onerror=alert(1)>", "> quote"]
    markdown = convert(tmp_path, [paragraph(hostile, top=700)]).markdown
    assert not live_syntax(markdown)
    assert not any(line.startswith(("#", ">")) for line in markdown.splitlines())


def test_ac_10_pdf_is_clearmds_own_its_notes_in_both_languages_and_in_the_executable() -> None:
    assert isinstance(build_registry().for_format(FormatId.PDF), PdfConverter)
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project["project"]["dependencies"]
    assert not any(dep.startswith("markitdown[pdf") or "pdf," in dep for dep in dependencies)
    assert importlib.util.find_spec("pdfminer") is None
    for language in ("en", "es"):
        catalog = load_catalog(language)
        for kind in PDF_NOTES:
            assert catalog.text(f"note.{kind.value}", items="1, 2")
    check = (ROOT / "packaging" / "check_executables.sh").read_text(encoding="utf-8")
    assert "sample.pdf" in check  # the executables' real batch converts a PDF
