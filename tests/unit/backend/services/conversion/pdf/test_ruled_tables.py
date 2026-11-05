"""ClearMD's PDF converter: tables drawn with rules."""

from pathlib import Path

from support.pdf_builder import Box, Text
from support.pdf_tables import DATA, convert, ruled

from clearmd.backend.services.conversion.pdf.lattice import Rule, find_lattices, rule
from clearmd.backend.services.conversion.pdf.tables import Word


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
