"""ClearMD's PDF converter (feature 008, ADR-0030) on PDFs written by hand for each case."""

from pathlib import Path

import pytest
from support import DOCUMENTS_DIR
from support.pdf_builder import GLYPH_CODE, Text, build_pdf, paragraph

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.pdf import PdfConverter

DETECTION = Detection(FormatId.PDF, DetectionMethod.EXTENSION)
BODY = [
    "The judicial system facilitates the development of economic, social and",
    "political systems, by regulating interactions based on values such as",
    "impartiality, effectiveness and timeliness in the resolution of conflicts.",
]


def convert(tmp_path: Path, pages: list[list[Text]]) -> ConversionResult:
    source = tmp_path / "doc.pdf"
    source.write_bytes(build_pdf(pages))
    return PdfConverter().convert(source, DETECTION, tmp_path / "doc.md")


def kinds(result: ConversionResult) -> list[NoteKind]:
    return [note.kind for note in result.notes]


# --- Reading ---------------------------------------------------------------------------------


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
    ]
    lines = convert(tmp_path, [page]).markdown.splitlines()
    assert "## 1 Introduction" in lines
    assert "### 3.1 Data and Variables" in lines
    assert "## IV. RESULTADOS" in lines


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


@pytest.mark.parametrize(
    "hostile",
    [
        "# not a heading",
        "[click](javascript:alert(1))",
        "<script>x</script>",
        "1. not a list",
        "| a |",
    ],
)
def test_document_text_never_becomes_markdown_it_did_not_write(
    tmp_path: Path, hostile: str
) -> None:
    markdown = convert(tmp_path, [paragraph([hostile], top=700)]).markdown
    assert "<script" not in markdown and "](javascript" not in markdown
    assert not markdown.lstrip().startswith(("#", "1.", "|"))


# --- Code review and security audit of 008 (C8-*, S8-*) ------------------------------------


def lines_of(markdown: str) -> list[str]:
    return [line for line in markdown.splitlines() if line.strip()]


def test_c8_1_a_repeated_line_inside_the_page_or_heading_sized_is_content(tmp_path: Path) -> None:
    law = [
        [
            Text(f"Artículo {2 * n - 1}.", 740, 11, "bold"),
            *paragraph([f"{word} {BODY[0]}" for word in ("uno", "dos", "tres")], top=720),
            Text(f"Artículo {2 * n}.", 650, 11, "bold"),
            *paragraph([f"{n} {BODY[1]}"], top=630),
        ]
        for n in range(1, 6)
    ]
    assert convert(tmp_path, law).markdown.count("Artículo") == 10
    chapter = [
        [
            Text("CAPÍTULO I MARCO TEÓRICO", 760, 8),
            *([Text("CAPÍTULO I MARCO TEÓRICO", 720, 16)] if n == 1 else []),
            *paragraph([f"{n} {line}" for line in BODY], top=690),
        ]
        for n in range(1, 6)
    ]
    assert "# CAPÍTULO I MARCO TEÓRICO" in convert(tmp_path, chapter).markdown.splitlines()
    captions = [
        [
            *paragraph([f"{n} {line}" for line in BODY], top=700),
            Text(f"Tabla {n}", 300, 11, "bold"),
            Text("Fuente: elaboración propia.", 200, 9),
        ]
        for n in range(1, 6)
    ]
    markdown = convert(tmp_path, captions).markdown
    assert markdown.count("Tabla") == 5 and markdown.count("Fuente") == 5


def test_c8_2_years_and_words_like_civil_are_never_page_numbers(tmp_path: Path) -> None:
    page = [Text("I", 760), Text("Civil", 745), *paragraph(BODY, top=700), Text("2014", 40)]
    markdown = convert(tmp_path, [page]).markdown
    assert "I" in lines_of(markdown)[0] and "Civil" in markdown and "2014" in markdown


def test_c8_2_page_numbers_follow_the_pages_roman_ones_too(tmp_path: Path) -> None:
    roman = ["i", "ii", "iii", "iv", "v"]
    pages = [
        [*paragraph([f"{roman[n]} {line}" for line in BODY], top=700), Text(roman[n], 40, 9)]
        for n in range(5)
    ]
    result = convert(tmp_path, pages)
    assert not any(line.strip() in roman for line in result.markdown.splitlines())


def test_c8_3_a_wrapped_line_starting_with_o_or_a_dash_is_no_list_item(tmp_path: Path) -> None:
    page = paragraph(
        ["El juez puede declarar la nulidad cuando falte un requisito esencial", "o cuando la",
         "parte no fue notificada, en el período 2012", "– 2016 de la ley vigente."],
        top=700,
    )  # fmt: skip
    markdown = convert(tmp_path, [page]).markdown
    assert not any(line.startswith("- ") for line in markdown.splitlines())
    assert "esencial o cuando la parte" in markdown


@pytest.mark.parametrize("hostile", ["# x", "> x", "1. x", "- x", "---", "***", "| a | b |"])
def test_s8_1_a_list_item_never_holds_markdown_it_did_not_write(
    tmp_path: Path, hostile: str
) -> None:
    from markdown_it import MarkdownIt

    markdown = convert(tmp_path, [paragraph([f"• {hostile}"], top=700)]).markdown
    tokens = {token.type for token in MarkdownIt("commonmark").parse(markdown)}
    assert tokens <= {
        "bullet_list_open", "bullet_list_close", "list_item_open", "list_item_close",
        "paragraph_open", "paragraph_close", "inline",
    }, markdown  # fmt: skip


def test_s8_2_a_heading_keeps_its_final_hash(tmp_path: Path) -> None:
    page = [Text("Ranking #", 700, 16), *paragraph(BODY, top=670)]
    assert "# Ranking \\#" in convert(tmp_path, [page]).markdown.splitlines()


def test_s8_3_a_paragraph_of_many_broken_words_is_joined_in_linear_time() -> None:
    import time

    from clearmd.backend.services.conversion.pdf.cleaner import clean
    from clearmd.backend.services.conversion.pdf.reader import Document, Line, Page

    def seconds(count: int) -> float:
        lines = [Line("ab­", 11.0, False, 711 - i, 700 - i) for i in range(count)]
        start = time.perf_counter()
        clean(Document([Page(lines)]))
        return time.perf_counter() - start

    assert seconds(80_000) < 6 * max(seconds(20_000), 0.01)  # quadratic would be ~16 times


def test_s8_5_blank_pages_are_listed_as_ranges() -> None:
    from clearmd.backend.services.conversion.pdf import MAX_LISTED_PAGES, page_ranges

    assert [item.subject for item in page_ranges([1, 2, 3, 7, 9, 10])] == ["1–3", "7", "9–10"]
    assert len(page_ranges(list(range(1, 4000, 2)))) == MAX_LISTED_PAGES


def test_s8_6_a_pdf_without_pages_is_an_empty_document_not_an_old_error(tmp_path: Path) -> None:
    with pytest.raises(ConversionError):
        PdfConverter().convert(DOCUMENTS_DIR / "encrypted.pdf", DETECTION, tmp_path / "x.md")
    empty = build_pdf([]).replace(b"/Count 0", b"/Count 0")
    source = tmp_path / "empty.pdf"
    source.write_bytes(empty)
    assert PdfConverter().convert(source, DETECTION, tmp_path / "e.md").markdown.strip() == ""


def test_s8_6_pdfiums_load_errors_are_mapped_by_name() -> None:
    import pypdfium2.raw as raw

    from clearmd.backend.services.conversion.pdf import reader

    assert raw.FPDF_ERR_SECURITY in reader._BROKEN and raw.FPDF_ERR_PAGE not in reader._BROKEN
    assert reader._PASSWORD == {raw.FPDF_ERR_PASSWORD}


def test_c8_5_text_that_cannot_be_read_is_never_dropped_silently(tmp_path: Path) -> None:
    page = [Text(f"{GLYPH_CODE}\x01{GLYPH_CODE}\x05{GLYPH_CODE}\x07", 700, 14, "glyphs"),
            *paragraph(BODY, top=650)]  # fmt: skip
    result = convert(tmp_path, [page])
    assert "�" in result.markdown and NoteKind.PDF_TEXT_UNREADABLE in kinds(result)


def test_c8_7_a_paragraph_in_a_larger_font_is_one_paragraph(tmp_path: Path) -> None:
    page = [*paragraph(BODY * 2, top=700, size=16, leading=19), *paragraph(BODY * 6, top=560)]
    markdown = convert(tmp_path, [page]).markdown
    assert sum(line.startswith("#") for line in markdown.splitlines()) <= 1


def test_c8_8_a_scan_with_a_printed_number_is_a_page_without_text(tmp_path: Path) -> None:
    header = Text("Review of Law and Economics", 760, 8)
    pages = [
        [header, *paragraph([f"{n} {line}" for line in BODY], top=700), Text(str(n), 40, 8)]
        for n in range(1, 6)
    ]
    pages[2] = [header, Text("3", 40, 8)]
    notes = convert(tmp_path, pages).notes
    note = next(note for note in notes if note.kind is NoteKind.PDF_PAGES_WITHOUT_TEXT)
    assert [item.subject for item in note.items] == ["3"]


def test_c8_9_hyphens_across_lines_join_and_a_capital_keeps_its_hyphen(tmp_path: Path) -> None:
    page = paragraph(
        ["the socio-", "Economic factors of the period 2012-", "2016 were included."], top=700
    )
    markdown = convert(tmp_path, [page]).markdown
    assert "socio-Economic factors of the period 2012-2016 were included." in markdown


def test_c8_10_an_item_ends_with_its_page_and_a_long_heading_takes_two_lines(
    tmp_path: Path,
) -> None:
    first = [
        *paragraph(BODY, top=700),
        *paragraph(["• Measure the efficiency of the courts"], top=640),
    ]
    second = paragraph(["Results show that the courts improved over the period."], top=700)
    blocks = convert(tmp_path, [first, second]).markdown.strip().split("\n\n")
    assert blocks[-2] == "- Measure the efficiency of the courts"
    heading = [
        Text("2 Theoretical Framework of the Efficiency", 700, 11, "bold"),
        Text("of the Colombian Criminal Justice", 686, 11, "bold"),
        *paragraph(BODY, top=660),
    ]
    lines = convert(tmp_path, [heading]).markdown.splitlines()
    assert "## 2 Theoretical Framework of the Efficiency of the Colombian Criminal Justice" in lines


def test_c8_10_a_held_footnote_never_lands_between_a_heading_and_its_text(tmp_path: Path) -> None:
    first = [
        *paragraph(["A properly functioning judicial system is one of the main tenets,"], top=700),
        *paragraph(["1 Corporación Excelencia en la Justicia."], top=80, size=8),
    ]
    second = [
        *paragraph(
            ["because it hinders the functioning of institutions, as Table 3 shows"], top=700
        ),
        Text("2 Methodology", 650, 11, "bold"),
        *paragraph(BODY, top=630),
    ]
    blocks = convert(tmp_path, [first, second]).markdown.strip().split("\n\n")
    assert (
        blocks.index("## 2 Methodology")
        == blocks.index("1 Corporación Excelencia en la Justicia.") + 1
    )


def test_c8_14_a_symbol_font_is_never_read_back_into_letters() -> None:
    from collections import Counter

    from clearmd.backend.services.conversion.pdf.reader import _shift

    symbols = Counter({0x00: 40, 0x01: 30, 0x14: 25, 0x30: 10, 0x32: 8})
    assert _shift(symbols) == 0


def test_surrogate_pairs_are_one_character() -> None:
    from collections import Counter

    from clearmd.backend.services.conversion.pdf.reader import Document, _Chars, _Fonts, _line

    chars, fonts = _Chars(), _Fonts()
    fonts.codes.append(Counter())
    fonts.unmapped.append(False)
    fonts.bold.append(False)
    for code in (0xD835, 0xDC9C, 0x42):
        chars.codes.append(code)
        chars.fonts.append(0)
        chars.bold.append(0)
        for column, value in ((chars.sizes, 11.0), (chars.bottoms, 700.0), (chars.tops, 711.0)):
            column.append(value)
    assert _line(chars, range(3), [0], fonts, Document([])).text == "𝒜B"
