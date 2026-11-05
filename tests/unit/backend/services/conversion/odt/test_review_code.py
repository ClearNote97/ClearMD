"""Regressions for the code review of feature 003 (H-*, M-1..M-7), from their reported input."""

from pathlib import Path

from support.odt_review import PARSER, convert, md

from clearmd.backend.schemas.notes import NoteKind


def test_h2_l6_a_paragraph_hidden_by_its_style_or_field_is_dropped_everywhere(
    tmp_path: Path,
) -> None:
    text = md(
        tmp_path,
        '<text:p text:style-name="PH">oculto entero</text:p>'
        '<text:h text:outline-level="1"><text:hidden-paragraph text:is-hidden="true"/>'
        "H oculto</text:h>"
        '<text:p text:style-name="P1"><text:hidden-paragraph text:is-hidden="true"/>'
        "cita oculta</text:p>"
        "<text:p>visible</text:p>",
    )
    assert "oculto" not in text and "cita oculta" not in text and "visible" in text


def test_h3_a_chart_is_a_placeholder_never_a_formula(tmp_path: Path) -> None:
    chart = (
        '<?xml version="1.0"?><office:document-content '
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"><office:body>'
        "<office:chart/></office:body></office:document-content>"
    )
    body = (
        '<text:p>chart: <draw:frame draw:name="Chart1"><draw:object xlink:href="./Object 1"/>'
        '<draw:image xlink:href="./ObjectReplacements/Object 1"/></draw:frame></text:p>'
    )
    text, kinds = convert(tmp_path, body, {"Object 1/content.xml": chart.encode()})
    assert "*Image: Chart1*" in text and "Formula" not in text
    assert NoteKind.FORMULA_KEPT_AS_SOURCE not in kinds and NoteKind.IMAGES_NOT_EXTRACTED in kinds


def test_h4_notes_and_text_boxes_in_cells_are_written_once(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        "<table:table><table:table-row><table:table-cell><text:p>a<text:note>"
        "<text:note-body><text:p>NOTA</text:p></text:note-body></text:note></text:p>"
        "</table:table-cell><table:table-cell><text:p><draw:frame><draw:text-box>"
        "<text:p>BOX</text:p></draw:text-box></draw:frame></text:p></table:table-cell>"
        "</table:table-row></table:table>",
    )
    assert text.count("NOTA") == 1 and text.count("BOX") == 1


def test_m1_whole_paragraph_bold_survives_in_cells_notes_and_quotes(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        '<table:table><table:table-row><table:table-cell><text:p text:style-name="PB">celda'
        "</text:p></table:table-cell></table:table-row></table:table>"
        '<text:p>x<text:note><text:note-body><text:p text:style-name="PB">nota</text:p>'
        "</text:note-body></text:note></text:p>",
    )
    assert "**celda**" in text and "[^1]: **nota**" in text


def test_m2_a_list_that_continues_keeps_its_numbering(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        '<text:list text:style-name="L2"><text:list-item><text:p>a</text:p></text:list-item>'
        "<text:list-item><text:p>b</text:p></text:list-item></text:list><text:p>entre</text:p>"
        '<text:list text:style-name="L2" text:continue-numbering="true"><text:list-item>'
        "<text:p>c</text:p></text:list-item></text:list>",
    )
    assert "3. a\n4. b" in text and "5. c" in text


def test_m3_nested_lists_headers_and_second_paragraphs_stay_apart(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        '<text:list text:style-name="L1"><text:list-header><text:p>cabecera</text:p>'
        "</text:list-header>"
        "<text:list-item><text:p>a</text:p><text:p>segundo</text:p>"
        '<text:list text:style-name="L2"><text:list-item><text:p>sub</text:p></text:list-item>'
        "</text:list></text:list-item></text:list>",
    )
    html = PARSER.render(text)
    assert "cabecera a" not in html and "a segundo" not in html and "a 3. sub" not in html
    assert "<li>" in html and "sub" in html


def test_m4_a_line_break_never_splits_a_heading(tmp_path: Path) -> None:
    text = md(tmp_path, '<text:h text:outline-level="1">Uno<text:line-break/>Dos</text:h>')
    assert text.strip() == "## Uno Dos"


def test_m5_a_link_keeps_the_spaces_around_it(tmp_path: Path) -> None:
    text = md(
        tmp_path, '<text:p>see <text:a xlink:href="https://x.org/">the site </text:a>now</text:p>'
    )
    assert "see [the site](https://x.org/) now" in text


def test_m6_a_text_box_keeps_lists_and_tables_and_its_spacing(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        "<text:p>x<draw:frame><draw:text-box><text:p>box</text:p>"
        '<text:list text:style-name="L1"><text:list-item><text:p>LISTA</text:p></text:list-item>'
        "</text:list><table:table><table:table-row><table:table-cell><text:p>TABLA</text:p>"
        "</table:table-cell></table:table-row></table:table></draw:text-box></draw:frame>y</text:p>",
    )
    assert "LISTA" in text and "TABLA" in text and "x box" in text and "TABLA y" in text


def test_m7_a_page_anchored_image_is_a_placeholder(tmp_path: Path) -> None:
    text, kinds = convert(
        tmp_path,
        '<draw:frame text:anchor-type="page" draw:name="P">'
        '<draw:image xlink:href="Pictures/p.png"/>'
        "<svg:title>page title</svg:title></draw:frame><text:p>x</text:p>",
    )
    assert "*Image: page title*" in text and NoteKind.ELEMENTS_SIMPLIFIED not in kinds
