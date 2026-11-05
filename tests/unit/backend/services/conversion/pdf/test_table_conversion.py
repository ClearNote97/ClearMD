"""ClearMD's PDF converter: tables through the converter."""

from pathlib import Path

from support.pdf_builder import Box, Text, paragraph
from support.pdf_tables import DATA, convert, downwards, header, sideways, upright

from clearmd.backend.services.conversion.pdf.tables import Word, find_tables


def test_a_table_and_its_caption_are_their_own_blocks(tmp_path: Path) -> None:
    text = paragraph(["The results are below, and they are measured"], top=700)
    caption = [Text("Table 1: Medians by year.", 650, 10)]
    after = paragraph(["by the median of each year."], top=520)
    markdown = convert(tmp_path, [text + caption + upright(DATA, 620) + after])
    # In the page's order: the text above, the caption, the table, the text below (review of 013).
    assert markdown.startswith(
        "The results are below, and they are measured\n\nTable 1: Medians by year.\n\n"
        "| Year | Median | CV | Maximum |\n|---|"
    )
    assert "| 2013 | 0.861 | 0.113 | 1.0 (3) |" in markdown
    assert markdown.endswith("|\n\nby the median of each year.\n")


def test_a_sideways_table_is_read_upright_and_its_page_header_goes(tmp_path: Path) -> None:
    body = paragraph(["Some text of the article on every page, long enough to be body."], top=700)
    pages: list[list[Text | Box]] = [[header(n + 1), *body] for n in range(5)]
    turned = [Text("Table 2: Courts by year.", 100, 10, x=80, sideways=True)]
    note = paragraph(["A line of the page's body, under the table."], top=60)  # review of 013
    pages[2] = [header(3), *turned, *sideways(DATA, 110), *note]
    markdown = convert(tmp_path, pages)
    assert "Table 2: Courts by year.\n\n| Year | Median | CV | Maximum |" in markdown
    assert "| 2015 | 0.855 | 0.142 | 1.0 (4) |" in markdown
    assert "Journal of Courts" not in markdown


def test_a_table_of_contents_has_one_entry_per_line(tmp_path: Path) -> None:
    entries = [
        "Dedicatoria ............................................. ii",
        "Agradecimiento .......................................... iii",
        "3.1 Tipo y diseño de investigación ....................... 14",
        "3.2 Variables y operacionalización ....................... 15",
    ]
    markdown = convert(tmp_path, [paragraph(["Índice", *entries], top=700)])
    for entry in entries:
        assert f"\n\n{entry}\n" in markdown or markdown.endswith(f"\n\n{entry}")


def test_a_table_read_downwards_and_a_turned_header(tmp_path: Path) -> None:
    body = paragraph(["Some text of the article on every page, long enough to be body."], top=700)
    pages: list[list[Text | Box]] = [[header(n + 1), *body] for n in range(5)]
    turned_header = Text("3 | Journal of Courts", 700, 8, x=560, downwards=True)
    pages[2] = [turned_header, *downwards(DATA, 500)]
    markdown = convert(tmp_path, pages)
    assert "| Year | Median | CV | Maximum |" in markdown
    assert "| 2015 | 0.855 | 0.142 | 1.0 (4) |" in markdown
    assert "Journal of Courts" not in markdown  # told by its text, wherever it stands


def test_a_table_under_larger_text_is_no_footnote(tmp_path: Path) -> None:
    body = paragraph(["A paragraph of the page in a larger font than its table."], top=730, size=14)
    markdown = convert(tmp_path, [[*body, *upright(DATA, 690)]])
    assert "| 2013 | 0.861 | 0.113 | 1.0 (3) |" in markdown


def test_a_table_at_the_same_place_on_every_page_stays(tmp_path: Path) -> None:
    body = paragraph(["The article's text on every page, long enough to be its body."], top=700)
    pages: list[list[Text | Box]] = [[*body, *upright(DATA, 200)] for _ in range(5)]
    assert convert(tmp_path, pages).count("| 2013 | 0.861 |") == 5


def test_a_page_of_many_rows_is_quick() -> None:
    import time

    words = [
        Word(
            f"{row}.{column}", 40 + 60 * column + row % 7, 70 + 60 * column, 800 - row, 806 - row, 6
        )
        for row in range(800)
        for column in range(8)
    ]
    started = time.monotonic()
    find_tables(words)
    assert time.monotonic() - started < 5
