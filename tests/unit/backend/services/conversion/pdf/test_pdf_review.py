"""ClearMD's PDF converter (feature 008, ADR-0030): code review, C8-* and S8-*."""

from pathlib import Path

import pytest
from support import DOCUMENTS_DIR
from support.markdown_guarantee import live_syntax
from support.pdf_builder import Text, build_pdf, paragraph
from support.pdf_cases import BODY, DETECTION, convert, lines_of

from clearmd.backend.schemas.errors import ConversionError
from clearmd.backend.services.conversion.pdf import PdfConverter


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
    assert not live_syntax(markdown)
    assert not markdown.lstrip().startswith(("#", "1.", "|"))


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
    from clearmd.backend.services.conversion.pdf.model import Document, Line, Page

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

    from clearmd.backend.services.conversion.pdf.pdfium import document

    assert document._BROKEN == {raw.FPDF_ERR_FILE, raw.FPDF_ERR_FORMAT}
    assert document._PASSWORD == {raw.FPDF_ERR_PASSWORD, raw.FPDF_ERR_SECURITY}  # encrypted
