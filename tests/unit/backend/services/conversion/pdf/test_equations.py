"""ClearMD's PDF converter: equations."""

from pathlib import Path

import pytest
from support.pdf_builder import Box, Text, build_pdf, paragraph
from support.pdf_tables import convert, label, placed

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.pdf import PdfConverter
from clearmd.backend.services.conversion.pdf import blocks as blk
from clearmd.backend.services.conversion.pdf.equations import find_equations
from clearmd.backend.services.conversion.pdf.tables import Word


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

    from clearmd.backend.services.conversion.pdf.cleaner.headings import toc_entry

    started = time.monotonic()
    assert not toc_entry("." * 200_000 + " 1x")
    assert toc_entry("Encuesta " + "." * 200_000 + " 16")
    assert time.monotonic() - started < 1
