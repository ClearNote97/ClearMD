"""The text subset of spec 003, row by row: inline text (AC-05 – AC-09, AC-13 – AC-14)."""

import time
from pathlib import Path

from build_fixtures import ODT_AUTOMATIC_STYLES
from markdown_it import MarkdownIt
from support import ODT_DIR
from support.odt_render import body, convert

GOLDEN = Path(__file__).parent / "golden"


PARSER = MarkdownIt("commonmark")


def test_the_report_comes_out_exactly_as_reviewed() -> None:
    markdown, found = convert(ODT_DIR / "report.odt")
    assert markdown == (GOLDEN / "report.md").read_text(encoding="utf-8")
    assert found == {}


def test_the_shallowest_outline_level_is_level_two(tmp_path: Path) -> None:
    text = body(
        tmp_path,
        '<text:h text:outline-level="2">A</text:h><text:h text:outline-level="3">B</text:h>',
    )
    assert text.startswith("## A\n\n### B")


def test_headings_inside_an_outline_list_stay_headings(tmp_path: Path) -> None:
    text = body(
        tmp_path,
        '<text:list><text:list-item><text:h text:outline-level="1"><text:number>1.</text:number>'
        "Uno</text:h></text:list-item></text:list>",
    )
    assert text.strip() == "## Uno"


def test_a_heading_or_title_is_never_wrapped_in_its_own_bold(tmp_path: Path) -> None:
    styles = ODT_AUTOMATIC_STYLES.replace(
        "</office:automatic-styles>",
        '<style:style style:name="PB" style:family="paragraph">'
        '<style:text-properties fo:font-weight="bold"/></style:style></office:automatic-styles>',
    )
    text = body(
        tmp_path,
        '<text:h text:style-name="PB" text:outline-level="1">H</text:h>'
        '<text:p text:style-name="PB">Negrita entera</text:p>',
        styles,
    )
    assert "## H" in text and "**Negrita entera**" in text


def test_properties_change_inside_one_delimiter_run(tmp_path: Path) -> None:
    text = body(
        tmp_path,
        '<text:p><text:span text:style-name="T1">a<text:span text:style-name="T2">b</text:span>'
        "</text:span>c</text:p>",
    )
    assert text.strip() == "**a*b***c"
    html = PARSER.render(text)
    assert "<strong>a<em>b</em></strong>c" in html


def test_spaces_stay_outside_the_delimiters(tmp_path: Path) -> None:
    text = body(tmp_path, '<text:p>x<text:span text:style-name="T1"> y </text:span>z</text:p>')
    assert text.strip() == "x **y** z"


def test_odf_whitespace_collapses_and_text_s_keeps_its_count(tmp_path: Path) -> None:
    text = body(tmp_path, '<text:p>\n   a \n\n b<text:s text:c="3"/>c<text:s/>d   </text:p>')
    assert text.strip() == "a b   c d"


def test_hidden_text_by_field_or_by_style_disappears(tmp_path: Path) -> None:
    styles = ODT_AUTOMATIC_STYLES.replace(
        "</office:automatic-styles>",
        '<style:style style:name="H" style:family="text">'
        '<style:text-properties text:display="none"/></style:style></office:automatic-styles>',
    )
    text = body(
        tmp_path,
        '<text:p>a<text:span text:style-name="H">oculto</text:span>'
        '<text:hidden-text text:string-value="tampoco" text:is-hidden="true"/>'
        '<text:hidden-text text:string-value=" visible" text:is-hidden="false"/>b</text:p>'
        '<text:section text:display="none"><text:p>seccion oculta</text:p></text:section>',
        styles,
    )
    assert "oculto" not in text and "tampoco" not in text and "seccion" not in text
    assert "a visibleb" in text


def test_a_style_loop_never_hangs(tmp_path: Path) -> None:
    styles = ODT_AUTOMATIC_STYLES.replace(
        "</office:automatic-styles>",
        '<style:style style:name="X" style:family="text" style:parent-style-name="Y"/>'
        '<style:style style:name="Y" style:family="text" style:parent-style-name="X"/>'
        "</office:automatic-styles>",
    )
    started = time.monotonic()
    assert "texto" in body(
        tmp_path, '<text:p><text:span text:style-name="X">texto</text:span></text:p>', styles
    )
    assert time.monotonic() - started < 2
