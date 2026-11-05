"""ClearMD's PDF converter (feature 008, ADR-0030): later findings, C8-5 to A8-7."""

from pathlib import Path

from support.pdf_builder import GLYPH_CODE, Text, paragraph
from support.pdf_cases import BODY, convert, kinds, lines_of

from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.pdf import model


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

    from clearmd.backend.services.conversion.pdf.decode import shift

    symbols = Counter({0x00: 40, 0x01: 30, 0x14: 25, 0x30: 10, 0x32: 8})
    assert shift(symbols) == 0


def test_surrogate_pairs_are_one_character() -> None:
    from clearmd.backend.services.conversion.pdf.lines.assemble import build_line

    chars = model.Chars()
    for code in (0xD835, 0xDC9C, 0x42, 0xD835, 0x43):
        chars.codes.append(code)
        chars.fonts.append(0)
        chars.bold.append(0)
        chars.turns.append(0)
        chars.font_sizes.append(11.0)
        chars.baselines.append(700.0)
        for column, value in (
            (chars.sizes, 11.0), (chars.bottoms, 700.0), (chars.tops, 711.0),
            (chars.lefts, 72.0), (chars.rights, 78.0),
        ):  # fmt: skip
            column.append(value)
    document = model.Document([])
    assert build_line(chars, range(5), [0], [False], document).text == "𝒜B�C"  # a half alone: "�"
    assert document.unreadable == 1


# --- Adversarial check of 008 (A8-*) ----------------------------------------------------------


def test_a8_2_a_header_with_a_bar_goes_even_when_a_page_holds_a_bare_number(
    tmp_path: Path,
) -> None:
    pages = [
        [Text(f"{n} | N. E. Valencia and C. Almanza", 760, 8),
         *paragraph([f"{n} {line}" for line in BODY], top=700), Text("12", 400)]
        for n in range(1, 6)
    ]  # fmt: skip
    assert "Valencia and C. Almanza" not in convert(tmp_path, pages).markdown


def test_a8_4_a_short_run_of_roman_page_numbers_goes(tmp_path: Path) -> None:
    roman = ["ii", "iii", "iv"]
    pages = [
        [Text(numeral, 40, 9), *paragraph([f"{numeral.upper()} {line}" for line in BODY], top=700)]
        for numeral in roman
    ] + [paragraph([f"{n} {line}" for line in BODY], top=700) for n in range(3)]
    lines = lines_of(convert(tmp_path, pages).markdown)
    assert not any(line.strip() in roman for line in lines)


def test_a8_7_an_item_goes_on_across_a_page_in_lowercase(tmp_path: Path) -> None:
    first = [*paragraph(BODY, top=700), *paragraph(["• Measure the efficiency of the"], top=640)]
    second = paragraph(["courts of the country.", "Results show the courts improved."], top=700)
    lines = lines_of(convert(tmp_path, [first, second]).markdown)
    assert "- Measure the efficiency of the courts of the country." in lines


def test_a8_7_a_subtitle_after_a_blank_is_a_heading_again(tmp_path: Path) -> None:
    words = [
        "A Very Long Title That Goes",
        "On For Four Lines Of Large",
        "Type In The Front",
        "Page",
    ]
    title = [Text(line, 740 - 22 * index, 18) for index, line in enumerate(words)]
    page = [*title, Text("A Subtitle In The Same Size", 560, 18), *paragraph(BODY * 4, top=500)]
    assert "# A Subtitle In The Same Size" in convert(tmp_path, [page]).markdown.splitlines()


def test_a8_7_a_held_footnote_goes_after_a_list_without_periods(tmp_path: Path) -> None:
    first = [
        *paragraph(["The judicial system is one of the main tenets,"], top=700),
        *paragraph(["1 Corporación Excelencia en la Justicia."], top=80, size=8),
    ]
    second = paragraph(
        ["because of these objectives:", "• Identify the framework", "• Measure the efficiency"],
        top=700,
    )
    blocks = convert(tmp_path, [first, second]).markdown.strip().split("\n\n")
    # Right after the paragraph it cut (its ":" ends it), before the list: never held to the end.
    assert blocks[1] == "1 Corporación Excelencia en la Justicia."
    assert blocks[2:] == ["- Identify the framework", "- Measure the efficiency"]
