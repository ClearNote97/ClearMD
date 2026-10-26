"""Regressions for the code review of feature 003 (H-*, M-*, L-*), each from its reported input.

The real-LibreOffice cases are written with the structure LibreOffice 7.4 saves (found by the
reviewer on files it made), so these tests never need LibreOffice.
"""

from pathlib import Path

import pytest
from build_fixtures import ODT_AUTOMATIC_STYLES, _odt_xml, odt_package
from markdown_it import MarkdownIt

from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.odt import OdtConverter
from clearmd.backend.services.conversion.odt.mathml import to_latex
from clearmd.backend.services.conversion.odt.xmltree import parse_part

MATH = 'xmlns="http://www.w3.org/1998/Math/MathML"'
STYLES = ODT_AUTOMATIC_STYLES.replace(
    "</office:automatic-styles>",
    '<style:style style:name="PH" style:family="paragraph">'
    '<style:text-properties text:display="none"/></style:style>'
    '<style:style style:name="PB" style:family="paragraph">'
    '<style:text-properties fo:font-weight="bold"/></style:style>'
    "</office:automatic-styles>",
)
PARSER = MarkdownIt("commonmark")


def md(tmp_path: Path, body: str, extra: dict[str, bytes] | None = None) -> str:
    return convert(tmp_path, body, extra)[0]


def convert(
    tmp_path: Path, body: str, extra: dict[str, bytes] | None = None
) -> tuple[str, set[NoteKind]]:
    path = tmp_path / "r.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", body, automatic=STYLES), extra=extra))
    result = OdtConverter().convert(path, None, path.with_suffix(".md"))  # type: ignore[arg-type]
    return result.markdown, {note.kind for note in result.notes}


def latex(body: str) -> str:
    return to_latex(
        parse_part(f"<math {MATH}><semantics><mrow>{body}</mrow></semantics></math>".encode())
    )


# --- High ----------------------------------------------------------------------------------------


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


# --- Medium --------------------------------------------------------------------------------------


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


@pytest.mark.parametrize(
    ("mathml", "expected"),
    [
        ('<mstyle mathvariant="bold"><mi>x</mi></mstyle>', "\\boldsymbol{x}"),
        ('<mstyle mathvariant="normal"><mi>abc</mi></mstyle>', "\\mathrm{abc}"),
        ('<mstyle mathvariant="sans-serif"><mi>x</mi></mstyle>', "\\mathsf{x}"),
        (
            '<mrow><mo fence="true" stretchy="true">⟨</mo><mi>x</mi>'
            '<mo fence="true" stretchy="true">⟩</mo></mrow>',
            "\\left\\langle x\\right\\rangle",
        ),
        ('<mfenced open="⌊" close="⌋"><mi>y</mi></mfenced>', "\\left\\lfloor y\\right\\rfloor"),
    ],
)
def test_m8_m9_styles_and_fences_of_libreoffice(mathml: str, expected: str) -> None:
    assert latex(mathml) == expected


@pytest.mark.parametrize(
    "attribute",
    [
        'text:outline-level="²"',
        'text:outline-level="' + "9" * 5000 + '"',
    ],
)
def test_m10_strange_numbers_never_fail_the_file(attribute: str, tmp_path: Path) -> None:
    text = md(
        tmp_path,
        f"<text:h {attribute}>H</text:h>"
        '<text:p>a<text:s text:c="²"/>b</text:p>'
        '<text:list text:style-name="L2"><text:list-item text:start-value="³"><text:p>c</text:p>'
        "</text:list-item></text:list>"
        '<table:table><table:table-row><table:table-cell table:number-columns-repeated="'
        + "9" * 5000
        + '"><text:p>d</text:p></table:table-cell></table:table-row></table:table>',
    )
    assert "H" in text and "c" in text and "d" in text


def test_m11_an_empty_formula_writes_nothing(tmp_path: Path) -> None:
    empty = (
        f'<math {MATH}><semantics><mrow/><annotation encoding="StarMath 5.0"></annotation>'
        "</semantics></math>"
    )
    frame = '<draw:frame><draw:object xlink:href="./Object 1"/></draw:frame>'
    text = md(
        tmp_path,
        f"<text:p>a {frame} b</text:p><text:p>{frame}</text:p>",
        {"Object 1/content.xml": empty.encode()},
    )
    assert "$$" not in text and "a b" in text


# --- Low ------------------------------------------------------------------------------------------


def test_l1_deleted_headings_never_move_the_top_level(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        '<text:tracked-changes><text:changed-region text:id="c"><text:deletion>'
        '<text:h text:outline-level="1">borrado</text:h></text:deletion></text:changed-region>'
        '</text:tracked-changes><text:h text:outline-level="2">Real</text:h>',
    )
    assert text.startswith("## Real")


def test_l2_an_item_with_only_a_sublist_has_no_marker_of_its_own(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        '<text:list text:style-name="L1"><text:list-item><text:list><text:list-item>'
        "<text:p>skipped level</text:p></text:list-item></text:list></text:list-item></text:list>",
    )
    assert "1. 1." not in text and "- 1." not in text and "skipped level" in text


def test_l3_quotations_and_code_inside_list_items_keep_their_role(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        '<text:list text:style-name="L1"><text:list-item><text:p>a</text:p>'
        '<text:p text:style-name="P2">x<text:s text:c="3"/>y</text:p></text:list-item></text:list>',
    )
    assert "```" in text and "x   y" in text


def test_l5_an_empty_note_is_still_a_valid_definition(tmp_path: Path) -> None:
    text = md(tmp_path, "<text:p>a<text:note><text:note-body/></text:note></text:p>")
    assert text.rstrip().endswith("[^1]: …")


def test_l7_fields_shown_as_none_disappear(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        '<text:p>a<text:variable-set text:display="none">HIDDEN</text:variable-set>b</text:p>',
    )
    assert text.strip() == "ab"


@pytest.mark.parametrize(
    ("mathml", "expected"),
    [
        ('<munder accentunder="true"><mi>x</mi><mo>̲</mo></munder>', "\\underline{x}"),
        ('<mover accent="true"><mi>x</mi><mo>˚</mo></mover>', "\\mathring{x}"),
        ('<mover accent="true"><mi>x</mi><mo>⃛</mo></mover>', "\\dddot{x}"),
        ('<mover accent="true"><mrow><mi>a</mi><mi>b</mi></mrow><mo stretchy="true">^</mo></mover>',
         "\\widehat{ab}"),
        ("<munder><mi>lim inf</mi><mi>n</mi></munder>", "\\liminf_{n}"),
        ("<mi>a</mi><mo>mod</mo><mi>b</mi>", "a\\bmod b"),
        ("<mi>ε</mi><mi>φ</mi><mi>ϵ</mi><mi>ϕ</mi>", "\\varepsilon\\varphi\\epsilon\\phi"),
        ('<mrow><mo fence="true" stretchy="true">{</mo><mi>x</mi></mrow>', "\\left\\{x\\right."),
        ("<mroot><mi>x</mi><mrow><mi>a</mi><mo>]</mo></mrow></mroot>", "\\sqrt[{a]}]{x}"),
    ],
)  # fmt: skip
def test_l8_to_l11_math_details(mathml: str, expected: str) -> None:
    assert latex(mathml) == expected


def test_l12_an_empty_run_in_the_middle_of_a_row_keeps_the_columns(tmp_path: Path) -> None:
    text = md(
        tmp_path,
        "<table:table><table:table-row><table:table-cell><text:p>a</text:p></table:table-cell>"
        '<table:table-cell table:number-columns-repeated="2"/>'
        "<table:table-cell><text:p>d</text:p></table:table-cell></table:table-row></table:table>",
    )
    assert "| a |  |  | d |" in text


def test_emphasis_characters_of_the_document_are_never_emphasis(tmp_path: Path) -> None:
    text = md(tmp_path, "<text:p>2*3*4 y archivo_de_datos_x y a~b~c</text:p>")
    html = PARSER.render(text)
    assert "<em>" not in html and "2*3*4" in html and "archivo_de_datos_x" in html
