"""ClearMD's PDF converter: superscripts, subscripts and equations beside notes."""

from pathlib import Path

from support.pdf_builder import Text, paragraph
from support.pdf_tables import convert, label, placed, scripted

from clearmd.backend.services.conversion.pdf import blocks as blk
from clearmd.backend.services.conversion.pdf.equations import find_equations


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
