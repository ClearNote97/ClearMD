"""Tables found from where their words stand (feature 013), on words written by hand."""

from collections.abc import Sequence
from pathlib import Path

from support.pdf_builder import Box, Text, build_pdf, paragraph

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.pdf import PdfConverter
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
    assert markdown.startswith(
        "Table 1: Medians by year.\n\n| Year | Median | CV | Maximum |\n|---|"
    )
    assert "| 2013 | 0.861 | 0.113 | 1.0 (3) |" in markdown
    assert "measured by the median of each year." in markdown  # the paragraph goes on


def test_a_sideways_table_is_read_upright_and_its_page_header_goes(tmp_path: Path) -> None:
    body = paragraph(["Some text of the article on every page, long enough to be body."], top=700)
    pages = [[header(n + 1), *body] for n in range(5)]
    turned = [Text("Table 2: Courts by year.", 100, 10, x=80, sideways=True)]
    pages[2] = [header(3), *turned, *sideways(DATA, 110)]
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
    assert "```\nEF = max t\n" in markdown and "(5)" in markdown.split("```")[1]
    assert "s.t. z <= 1" in markdown.split("```")[1]


def test_an_equation_is_cropped_as_a_picture_with_the_images_folder(tmp_path: Path) -> None:
    from clearmd.backend.services.conversion.images import ImageSink

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
