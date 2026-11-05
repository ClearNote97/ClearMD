"""Regressions for the code review of feature 003 (M-8 on, L-*), each from its reported input."""

from pathlib import Path

import pytest
from support.odt_review import MATH, PARSER, latex, md


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
