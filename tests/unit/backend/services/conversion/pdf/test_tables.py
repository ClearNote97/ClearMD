"""Tables found from where their words stand (feature 013), on words written by hand."""

from collections.abc import Sequence
from pathlib import Path

import pytest
from support.pdf_builder import Box, Text, build_pdf, paragraph

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.pdf import PdfConverter
from clearmd.backend.services.conversion.pdf import blocks as blk
from clearmd.backend.services.conversion.pdf.equations import Placed, find_equations
from clearmd.backend.services.conversion.pdf.lattice import Rule, find_lattices, rule
from clearmd.backend.services.conversion.pdf.tables import Word, find_tables


def grid(
    rows: list[list[str]], *, top: float = 700, columns: tuple[float, ...] = (72, 180, 260, 340)
) -> list[Word]:  # noqa: E501
    words = []
    for index, row in enumerate(rows):
        bottom = top - 14 * index
        for x, text in zip(columns, row, strict=False):
            if text:
                words.append(Word(text, x, x + 5.5 * len(text), bottom, bottom + 10, 10))
    return words


DATA = [
    ["Year", "Median", "CV", "Maximum"],
    ["2012", "0.871", "0.099", "1.0 (3)"],
    ["2013", "0.861", "0.113", "1.0 (3)"],
    ["2014", "0.863", "0.126", "1.0 (4)"],
    ["2015", "0.855", "0.142", "1.0 (4)"],
]


def test_a_table_is_found_with_its_rows_and_columns() -> None:
    (table,) = find_tables(grid(DATA))
    assert table.rows[0] == ("Year", "Median", "CV", "Maximum")
    assert table.rows[2] == ("2013", "0.861", "0.113", "1.0 (3)")
    assert table.top > table.bottom


def test_a_missing_cell_stays_empty() -> None:
    rows = [row[:] for row in DATA]
    rows[3][2] = ""
    (table,) = find_tables(grid(rows))
    assert table.rows[3] == ("2014", "0.863", "", "1.0 (4)")


def test_three_rows_are_no_table() -> None:
    assert find_tables(grid(DATA[:3])) == []


def test_prose_with_wide_gaps_is_no_table() -> None:
    words = []
    for index, xs in enumerate(((72, 200, 330), (90, 260, 400), (72, 150, 380), (120, 240, 300))):
        bottom = 700 - 14 * index
        for x in xs:
            words.append(Word("justified", x, x + 45, bottom, bottom + 10, 10))
    assert find_tables(words) == []  # gaps that do not line up


def test_an_aligned_formula_is_no_table() -> None:
    rows = [["x", "=", "t+1"], ["y", "=", "(10)"], ["z", "=", "a"], ["w", "=", "b"]]
    assert find_tables(grid(rows, columns=(72, 120, 200))) == []


def test_a_number_of_one_digit_is_content() -> None:
    rows = [["Year", "Effic.", "%"], ["2012", "3", "9"], ["2013", "3", "9"], ["2014", "5", "15"]]
    rows.append(["2015", "7", "21"])
    (table,) = find_tables(grid(rows, columns=(72, 180, 260)))
    assert table.rows[1] == ("2012", "3", "9")


def test_a_cell_wrapped_over_lines_stays_in_the_table() -> None:
    rows = [row[:] for row in DATA]
    rows.insert(2, ["", "", "", "(continued)"])
    rows.insert(3, ["", "", "", "(and more)"])
    (table,) = find_tables(grid(rows))
    assert len(table.rows) == 7


# --- Through the converter ---------------------------------------------------------------------


def convert(tmp_path: Path, pages: Sequence[Sequence[Text | Box]]) -> str:
    source = tmp_path / "paper.pdf"
    source.write_bytes(build_pdf(pages))
    detection = Detection(FormatId.PDF, DetectionMethod.EXTENSION)
    return PdfConverter().convert(source, detection, tmp_path / "paper.md").markdown


def upright(rows: list[list[str]], top: float) -> list[Text]:
    return [
        Text(text, top - 16 * index, 10, x=x)
        for index, row in enumerate(rows)
        for x, text in zip((72, 200, 300, 400), row, strict=False)
        if text
    ]


def sideways(rows: list[list[str]], left: float) -> list[Text]:
    """Each row a column of the page, read upwards: the first row at the left."""
    return [
        Text(text, y, 10, x=left + 16 * index, sideways=True)
        for index, row in enumerate(rows)
        for y, text in zip((100, 230, 330, 430), row, strict=False)
        if text
    ]


def header(page: int) -> Text:
    return Text(f"{page} | Journal of Courts", 760, 8)


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


def downwards(rows: list[list[str]], right: float) -> list[Text]:
    """Each row a column of the page, read downwards: the first row at the right."""
    return [
        Text(text, y, 10, x=right - 16 * index, downwards=True)
        for index, row in enumerate(rows)
        for y, text in zip((700, 570, 470, 370), row, strict=False)
        if text
    ]


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


# --- Ruled tables (lattice) --------------------------------------------------------------------


def ruled(xs: list[float], ys: list[float]) -> list[Rule]:
    rules = [Rule(True, y, xs[0], xs[-1]) for y in ys]
    return rules + [Rule(False, x, ys[-1], ys[0]) for x in xs]


def test_a_cell_wrapped_over_lines_is_one_cell_of_its_ruled_table() -> None:
    words = [
        Word("Name", 75, 100, 690, 698, 8),
        Word("Role", 205, 225, 690, 698, 8),
        Word("Ana", 75, 92, 670, 678, 8),
        Word("Judge", 205, 230, 670, 678, 8),
        Word("of", 205, 215, 660, 668, 8),
        Word("peace", 218, 245, 660, 668, 8),
    ]
    ((table, taken),) = find_lattices(ruled([70, 200, 300], [705, 685, 650]), words)
    assert table.rows == (("Name", "Role"), ("Ana", "Judge of peace"))
    assert len(taken) == 6


def test_a_frame_alone_is_no_table() -> None:
    words = [Word("Text", 80, 100, 600, 608, 8)]
    assert find_lattices(ruled([50, 550], [750, 50]), words) == []


def test_a_thin_box_is_a_rule_and_a_filled_one_is_not() -> None:
    assert rule(70, 700, 300, 700.5) == Rule(True, 700.25, 70, 300)
    assert rule(70, 650, 70.5, 700) == Rule(False, 70.25, 650, 700)
    assert rule(70, 650, 300, 700) is None  # a shaded cell


def test_a_ruled_table_through_the_converter(tmp_path: Path) -> None:
    xs, ys = (70, 200, 330), (705, 685, 650, 630)
    boxes: list[Text | Box] = [Box(70, y, 260, 0.5) for y in ys]
    boxes += [Box(x, 630, 0.5, 75) for x in xs]
    texts: list[Text | Box] = [
        Text("Name", 690, 9, x=75), Text("Role", 690, 9, x=205),
        Text("Ana", 670, 9, x=75), Text("Judge", 670, 9, x=205), Text("of peace", 658, 9, x=205),
        Text("Luis", 635, 9, x=75), Text("Clerk", 635, 9, x=205),
    ]  # fmt: skip
    markdown = convert(tmp_path, [boxes + texts])
    assert "| Name | Role |\n|---|---|\n| Ana | Judge of peace |\n| Luis | Clerk |" in markdown


# --- Equations ---------------------------------------------------------------------------------


def placed(text: str, bottom: float, right: float, size: float = 9) -> Placed:
    return Placed(text, bottom + size, bottom, size, right, False)


def label(text: str, left: float, bottom: float) -> Word:
    return Word(text, left, left + 12, bottom, bottom + 9, 9)


def test_an_equation_is_its_lines_around_its_number() -> None:
    lines = [
        placed("as follows the program is defined here:", 700, 520),
        placed("max θ", 680, 300),
        placed("j=1", 668, 260, 6),
        placed("(5)", 674, 520),
        placed("where the variables mean what they always mean in the text", 640, 520),
    ]
    words = [Word("max", 200, 220, 680, 689, 9), label("(5)", 508, 674)]
    assert find_equations(lines, words) == [range(1, 4)]


def test_a_reference_at_the_end_of_a_line_is_no_equation_number() -> None:
    lines = [placed("the results of the model as given in (5)", 700, 520)]
    words = [Word("in", 480, 492, 700, 709, 9), label("(5)", 495, 700)]
    assert find_equations(lines, words) == []


def test_an_equation_through_the_converter_keeps_its_layout(tmp_path: Path) -> None:
    page: list[Text | Box] = [
        *paragraph(["The program is stated as follows, for every court:"], top=700),
        Text("EF = max t", 670, 11, x=200),
        Text("s.t. z <= 1", 652, 11, x=200),
        Text("(5)", 661, 11, x=520),
        *paragraph(["where the variables are the ones defined in the text above it."], top=620),
    ]
    markdown = convert(tmp_path, [page])
    rows = r"\displaystyle EF = \max t \\ \displaystyle s.t. z <= 1"
    assert f"$$\n\\begin{{array}}{{l}} {rows} \\end{{array}} \\tag{{5}}\n$$" in markdown


def test_an_equation_not_understood_keeps_its_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(blk.equation_latex, "to_latex", lambda glyphs, bars: None)
    page: list[Text | Box] = [
        *paragraph(["The program is stated as follows, for every court:"], top=700),
        Text("EF = max t", 670, 11, x=200),
        Text("s.t. z <= 1", 652, 11, x=200),
        Text("(5)", 661, 11, x=520),
        *paragraph(["where the variables are the ones defined in the text above it."], top=620),
    ]
    markdown = convert(tmp_path, [page])
    assert "```\nEF = max t\n" in markdown and "(5)" in markdown.split("```")[1]
    assert "s.t. z <= 1" in markdown.split("```")[1]


def test_an_equation_not_understood_is_cropped_as_a_picture_with_the_images_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.backend.services.conversion.images import ImageSink

    monkeypatch.setattr(blk.equation_latex, "to_latex", lambda glyphs, bars: None)
    page: list[Text | Box] = [
        *paragraph(["The program is stated as follows, for every court:"], top=700),
        Text("EF = max t", 670, 11, x=200),
        Text("(5)", 670, 11, x=520),
        *paragraph(["where the variables are the ones defined in the text above it."], top=630),
    ]
    source = tmp_path / "paper.pdf"
    source.write_bytes(build_pdf([page]))
    sink = ImageSink.for_folder("paper_images")
    detection = Detection(FormatId.PDF, DetectionMethod.EXTENSION)
    markdown = PdfConverter().convert(source, detection, tmp_path / "p.md", images=sink).markdown
    assert "![](paper_images/image-001.png)" in markdown and "```" not in markdown
    assert sink.images[0].data.startswith(b"\x89PNG")


# --- A table of contents -----------------------------------------------------------------------


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


# --- Review of 013 -----------------------------------------------------------------------------


def test_a_table_under_larger_text_is_no_footnote(tmp_path: Path) -> None:
    body = paragraph(["A paragraph of the page in a larger font than its table."], top=730, size=14)
    markdown = convert(tmp_path, [[*body, *upright(DATA, 690)]])
    assert "| 2013 | 0.861 | 0.113 | 1.0 (3) |" in markdown


def test_a_table_at_the_same_place_on_every_page_stays(tmp_path: Path) -> None:
    body = paragraph(["The article's text on every page, long enough to be its body."], top=700)
    pages: list[list[Text | Box]] = [[*body, *upright(DATA, 200)] for _ in range(5)]
    assert convert(tmp_path, pages).count("| 2013 | 0.861 |") == 5


def test_a_ruled_table_beside_a_stream_table_stays(tmp_path: Path) -> None:
    boxes: list[Text | Box] = [Box(330, y, 200, 0.5) for y in (705, 685, 650)]
    boxes += [Box(x, 650, 0.5, 55) for x in (330, 430, 530)]
    ruled_words: list[Text | Box] = [
        Text("Name", 690, 9, x=335), Text("Role", 690, 9, x=435),
        Text("Ana", 670, 9, x=335), Text("Judge", 670, 9, x=435),
    ]  # fmt: skip
    stream: list[Text | Box] = [
        Text(text, 700 - 16 * index, 9, x=x)
        for index, row in enumerate(DATA)
        for x, text in zip((40, 100, 160, 220), row, strict=False)
    ]
    markdown = convert(tmp_path, [[*boxes, *ruled_words, *stream]])
    assert "| Name | Role |" in markdown and "| Ana | Judge |" in markdown
    assert "| 2013 | 0.861 | 0.113 | 1.0 (3) |" in markdown


def test_a_bulleted_list_set_with_tabs_is_no_table() -> None:
    rows = [
        ["•", "Name", "Ana"],
        ["•", "Role", "Judge"],
        ["•", "Court", "Lima"],
        ["•", "Year", "2021"],
    ]
    assert find_tables(grid(rows, columns=(72, 90, 200))) == []


def test_an_equation_stops_at_a_heading_and_a_caption() -> None:
    lines = [
        placed("3. Methods", 720, 200),
        placed("max θ", 700, 300),
        placed("(5)", 700, 520),
        placed("Table 2: Data", 680, 200),
    ]
    words = [Word("max", 200, 220, 700, 709, 9), label("(5)", 508, 700)]
    assert find_equations(lines, words) == [range(1, 3)]


def test_a_line_of_dots_is_read_at_once() -> None:
    import time

    from clearmd.backend.services.conversion.pdf.cleaner import _toc_entry

    started = time.monotonic()
    assert not _toc_entry("." * 200_000 + " 1x")
    assert _toc_entry("Encuesta " + "." * 200_000 + " 16")
    assert time.monotonic() - started < 1


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


# --- Sub- and superscripts (014) ---------------------------------------------------------------


def scripted(tmp_path: Path, pieces: list[Text]) -> str:
    return convert(tmp_path, [pieces])


def test_a_superscript_and_a_subscript_are_written_as_such(tmp_path: Path) -> None:
    # Helvetica: "EF" is 1.278 em wide, "t" 0.278 em: each piece starts where the last ends.
    markdown = scripted(
        tmp_path,
        [
            Text("The efficiency", 700, 11, x=72),
            Text("EF", 700, 11, x=150),
            Text("t", 704, 7, x=164.1),
            Text("o", 697, 7, x=164.1),
            Text("(x) is the measure of it.", 700, 11, x=166.1),
        ],
    )
    assert "The efficiency EFᵗₒ(x) is the measure of it." in markdown


def test_a_footnote_mark_is_a_superscript(tmp_path: Path) -> None:
    markdown = scripted(
        tmp_path,
        [
            Text("Studies are rare, in relative", 700, 11, x=72),
            Text("terms.", 700, 11, x=230),  # 2.778 em wide
            Text("5", 704, 7, x=260.6),
            Text("Since then, many have used it.", 700, 11, x=267.5),
        ],
    )
    assert "in relative terms.⁵ Since then" in markdown


def test_a_script_unicode_lacks_is_written_with_braces(tmp_path: Path) -> None:
    markdown = scripted(
        tmp_path,
        [
            Text("The power x", 700, 11, x=72),
            Text("q", 704, 7, x=133),
            Text(" grows.", 700, 11, x=137),
        ],
    )
    assert "x^{q}" in markdown


def test_a_tall_brace_is_part_of_its_equation() -> None:
    lines = [
        placed("as follows the program is defined here:", 700, 520),
        placed("P(x) = {", 680, 300, 30),  # a brace 30 points tall: no heading
        placed("y: y ≤ 1", 680, 360),
        placed("(3)", 680, 520),
    ]
    words = [label("(3)", 508, 680)]
    assert find_equations(lines, words) == [range(1, 4)]


# --- Review of 014 -----------------------------------------------------------------------------


def test_scripts_of_text_scaled_by_its_matrix(tmp_path: Path) -> None:
    markdown = scripted(
        tmp_path,
        [
            Text("The efficiency", 700, 11, x=72, scaled=True),
            Text("EF", 700, 11, x=150, scaled=True),
            Text("t", 704, 7, x=164.1, scaled=True),
            Text("o", 697, 7, x=164.1, scaled=True),
            Text("(x) is the measure of it.", 700, 11, x=166.1, scaled=True),
        ],
    )
    assert "EFᵗₒ(x) is the measure of it." in markdown


def test_an_operator_set_smaller_between_two_terms_is_no_script(tmp_path: Path) -> None:
    markdown = scripted(
        tmp_path,
        [
            Text("They could solve 521 (1", 700, 11, x=72),
            Text("*", 703, 7, x=199.6),
            Text("0.169) more cases.", 700, 11, x=202.6),
        ],
    )
    assert "^" not in markdown and "\\*0.169)" in markdown  # an asterisk, never "^{*}"


def test_footnotes_with_raised_marks_stay_apart(tmp_path: Path) -> None:
    body = paragraph(
        ["A page of the article's text, as long as a full line of the page is."], top=700
    )
    notes = []
    for index, text in enumerate(("First note of the page.", "Second note.", "Third note.")):
        y = 120 - 10 * index
        notes += [Text(str(index + 1), y + 3, 5, x=72), Text(text, y, 8, x=76)]
    markdown = convert(tmp_path, [[*body, *notes]])
    assert "¹First note of the page.\n\n²Second note.\n\n³Third note." in markdown


def test_an_equation_is_not_clipped_by_a_note_beside_it() -> None:
    from clearmd.backend.services.conversion.pdf.model import Line

    lines = [
        Line("Some prose before the equation, a full line of text here.", 9, False, 730, 721,
             left=72, right=520),
        Line("A note", 9, False, 712, 705, left=20, right=60),  # in the left margin, beside
        Line("x = ∑ z", 9, False, 714, 700, left=200, right=260),
        Line("y = w (3)", 9, False, 698, 688, left=200, right=520),
        Line("More prose after the equation, a full line of the text again.", 9, False, 670, 661,
             left=72, right=520),
    ]  # fmt: skip
    words = [label("(3)", 508, 689)]
    blocks = [line for line in blk.equation_blocks.place_equations(lines, words) if line.equation]
    assert blocks and blocks[0].top == 714  # its first row whole
