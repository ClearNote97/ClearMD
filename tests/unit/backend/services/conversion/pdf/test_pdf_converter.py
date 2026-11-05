"""ClearMD's PDF converter (feature 008, ADR-0030): reading and cleaning PDFs written by hand."""

from pathlib import Path

import pytest
from support import DOCUMENTS_DIR
from support.pdf_builder import Text, paragraph
from support.pdf_cases import BODY, DETECTION, convert, kinds

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.pdf import PdfConverter


def test_the_fixture_converts_and_keeps_its_text(tmp_path: Path) -> None:
    result = PdfConverter().convert(DOCUMENTS_DIR / "sample.pdf", DETECTION, tmp_path / "s.md")
    assert "fixture-pdf" in result.markdown


@pytest.mark.parametrize(
    ("name", "code"),
    [("encrypted.pdf", ErrorCode.PASSWORD_PROTECTED), ("corrupt.pdf", ErrorCode.CORRUPT_FILE)],
)
def test_a_locked_or_broken_pdf_fails_with_its_code(
    tmp_path: Path, name: str, code: ErrorCode
) -> None:
    with pytest.raises(ConversionError) as raised:
        PdfConverter().convert(DOCUMENTS_DIR / name, DETECTION, tmp_path / "x.md")
    assert raised.value.code is code and raised.value.detail


def test_a_zip_renamed_pdf_is_a_broken_pdf(tmp_path: Path) -> None:
    import zipfile

    fake = tmp_path / "invoice.pdf"
    with zipfile.ZipFile(fake, "w") as archive:
        archive.writestr("inner.txt", "x" * 1000)
    with pytest.raises(ConversionError) as raised:
        PdfConverter().convert(fake, DETECTION, tmp_path / "x.md")
    assert raised.value.code is ErrorCode.CORRUPT_FILE


def test_words_keep_their_spaces(tmp_path: Path) -> None:
    result = convert(tmp_path, [paragraph(BODY, top=700)])
    assert "based on values such as impartiality, effectiveness" in result.markdown


def test_a_font_without_a_character_map_is_read_back_and_told(tmp_path: Path) -> None:
    page = [
        Text("ESCUELA DE POSGRADO", 700, 20, "glyphs"),
        Text("Maestría en Gestión Pública", 670, 14, "glyphs"),
        *paragraph(BODY, top=600),
    ]
    result = convert(tmp_path, [page])
    assert "ESCUELA DE POSGRADO" in result.markdown
    assert "Maestría en Gestión Pública" in result.markdown
    assert NoteKind.PDF_TEXT_DECODED in kinds(result)


def test_a_regular_font_is_never_moved(tmp_path: Path) -> None:
    result = convert(tmp_path, [paragraph(BODY, top=700)])
    assert NoteKind.PDF_TEXT_DECODED not in kinds(result)


def test_text_upside_down_reads_the_right_way(tmp_path: Path) -> None:
    page = [*paragraph(BODY, top=700), Text("Number of solved cases", 300, 11, rotated=True)]
    assert "Number of solved cases" in convert(tmp_path, [page]).markdown


def test_a_page_without_text_is_told_by_its_number(tmp_path: Path) -> None:
    result = convert(tmp_path, [paragraph(BODY, top=700), [], paragraph(BODY, top=700)])
    notes = [note for note in result.notes if note.kind is NoteKind.PDF_PAGES_WITHOUT_TEXT]
    assert [item.subject for item in notes[0].items] == ["2"]


def test_a_pdf_with_no_text_at_all_is_an_empty_document_with_its_note(tmp_path: Path) -> None:
    result = convert(tmp_path, [[], []])
    assert result.markdown.strip() == ""
    assert NoteKind.PDF_PAGES_WITHOUT_TEXT in kinds(result)


# --- Cleaning --------------------------------------------------------------------------------


def _page(number: int, lines: list[str]) -> list[Text]:
    return [
        Text("Review of Law and Economics", 760, 8),
        *paragraph(lines, top=700),
        Text(str(number), 40, 8),
    ]


def test_running_headers_and_page_numbers_go_and_it_is_told(tmp_path: Path) -> None:
    result = convert(tmp_path, [_page(n, BODY) for n in range(1, 6)])
    assert "Review of Law and Economics" not in result.markdown
    assert not any(line.strip().isdigit() for line in result.markdown.splitlines())
    assert NoteKind.PDF_RUNNING_REMOVED in kinds(result)


def test_with_few_pages_a_repeated_line_is_content(tmp_path: Path) -> None:
    result = convert(tmp_path, [_page(n, BODY) for n in range(1, 3)])
    assert result.markdown.count("Review of Law and Economics") == 2


def test_headings_are_told_by_their_size_the_tallest_first(tmp_path: Path) -> None:
    page = [
        Text("Evaluating Colombian Criminal Justice", 740, 18),
        Text("Introduction", 700, 14),
        *paragraph(BODY, top=670),
        Text("Methodology", 600, 14),
        *paragraph(BODY, top=570),
    ]
    lines = convert(tmp_path, [page]).markdown.splitlines()
    assert "# Evaluating Colombian Criminal Justice" in lines
    assert "## Introduction" in lines and "## Methodology" in lines


def test_a_numbered_bold_line_is_a_heading_by_its_numbers(tmp_path: Path) -> None:
    page = [
        Text("1 Introduction", 700, 11, "bold"),
        *paragraph(BODY, top=680),
        Text("3.1 Data and Variables", 600, 11, "bold"),
        *paragraph(BODY, top=580),
        Text("IV. RESULTADOS", 500, 11, "bold"),
        *paragraph(BODY, top=480),
        Text("II. MARCO TEÓRICO.", 400, 11, "bold"),
    ]
    lines = convert(tmp_path, [page]).markdown.splitlines()
    assert "## 1 Introduction" in lines
    assert "### 3.1 Data and Variables" in lines
    assert "## IV. RESULTADOS" in lines and "## II. MARCO TEÓRICO." in lines


def test_bold_text_that_is_a_sentence_or_a_formula_is_no_heading(tmp_path: Path) -> None:
    page = [
        Text("3 Jueces de Paz de Pomalca. El objetivo general es determinar", 700, 11, "bold"),
        Text("((xt+1, yt+1) = 0", 660, 20),
        *paragraph(BODY, top=620),
    ]
    markdown = convert(tmp_path, [page]).markdown
    assert not any(line.startswith("#") for line in markdown.splitlines())


def test_lines_of_a_paragraph_are_one_and_a_gap_starts_another(tmp_path: Path) -> None:
    page = [*paragraph(BODY, top=700), *paragraph(BODY, top=640)]
    blocks = convert(tmp_path, [page]).markdown.strip().split("\n\n")
    assert len(blocks) == 2 and blocks[0] == " ".join(BODY)


def test_a_paragraph_goes_on_to_the_next_page_and_its_footnote_waits(tmp_path: Path) -> None:
    first = [
        *paragraph(["A properly functioning judicial system is one of the main tenets,"], top=700),
        *paragraph(
            ["1 Corporación Excelencia en la Justicia, a civil society group."], top=80, size=8
        ),
    ]
    second = paragraph(["because it hinders the correct functioning of institutions."], top=700)
    blocks = convert(tmp_path, [first, second]).markdown.strip().split("\n\n")
    assert blocks[0].endswith(
        "main tenets, because it hinders the correct functioning of institutions."
    )
    assert blocks[1].startswith("1 Corporación Excelencia")


def test_words_broken_at_the_end_of_a_line_are_joined(tmp_path: Path) -> None:
    """A hyphen ending a line is a broken word for PDFium (it gives a soft hyphen), as it almost
    always is in a typeset document; one inside a line stays."""
    page = paragraph(["the problems of the adminis-", "tration and a well-known case."], top=700)
    markdown = convert(tmp_path, [page]).markdown
    assert "the problems of the administration and a well-known case." in markdown


def test_bullets_become_list_items(tmp_path: Path) -> None:
    page = paragraph(["• Identify the legal framework", "• Measure the efficiency"], top=700)
    lines = convert(tmp_path, [page]).markdown.splitlines()
    assert "- Identify the legal framework" in lines and "- Measure the efficiency" in lines
