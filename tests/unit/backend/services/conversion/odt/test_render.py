"""The text subset of spec 003, row by row (AC-05 – AC-09, AC-13 – AC-14)."""

import time
from pathlib import Path

import pytest
from build_fixtures import ODT_AUTOMATIC_STYLES, _odt_xml, odt_package
from markdown_it import MarkdownIt
from support import ODT_DIR

from clearmd.backend.schemas.notes import NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.odt import OdtConverter

GOLDEN = Path(__file__).parent / "golden"
PARSER = MarkdownIt("commonmark")


def convert(path: Path) -> tuple[str, dict[NoteKind, tuple[NoteItem, ...]]]:
    result = OdtConverter().convert(path, None, path.with_suffix(".md"))  # type: ignore[arg-type]
    return result.markdown, {note.kind: note.items for note in result.notes}


def body(tmp_path: Path, xml: str, automatic: str = ODT_AUTOMATIC_STYLES) -> str:
    path = tmp_path / "t.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", xml, automatic=automatic)))
    return convert(path)[0]


def notes(tmp_path: Path, xml: str) -> dict[NoteKind, tuple[NoteItem, ...]]:
    path = tmp_path / "t.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", xml)))
    return convert(path)[1]


def test_the_report_comes_out_exactly_as_reviewed() -> None:
    markdown, found = convert(ODT_DIR / "report.odt")
    assert markdown == (GOLDEN / "report.md").read_text(encoding="utf-8")
    assert found == {}


# --- Structure -----------------------------------------------------------------------------------


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


# --- Inline text ---------------------------------------------------------------------------------


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


def test_links_follow_the_rules_of_adr_0023(tmp_path: Path) -> None:
    text = body(
        tmp_path,
        '<text:p><text:a xlink:href="https://ok.example/a b">ok</text:a> '
        '<text:a xlink:href="javascript:alert(1)">mal</text:a> '
        '<text:a xlink:href="https://ok.example/x"><text:span text:style-name="T1">neg</text:span>'
        "</text:a></text:p>",
    )
    assert "[ok](<https://ok.example/a b>)" in text
    assert "](javascript" not in text and "mal (`javascript:alert(1)`)" in text
    assert "[**neg**](https://ok.example/x)" in text


def test_document_text_never_becomes_markdown(tmp_path: Path) -> None:
    text = body(
        tmp_path,
        "<text:p>&lt;img src=x&gt; [a](http://evil.example/b.png) `x`</text:p>"
        "<text:p># no</text:p>",
    )
    assert "<img" not in text and "](" not in text and "\n# no" not in "\n" + text


def test_footnotes_and_endnotes_share_one_numbering(tmp_path: Path) -> None:
    text = body(
        tmp_path,
        '<text:p>a<text:note text:note-class="footnote"><text:note-body><text:p>uno</text:p>'
        '</text:note-body></text:note> b<text:note text:note-class="endnote"><text:note-body>'
        "<text:p>dos</text:p></text:note-body></text:note></text:p>",
    )
    assert "a[^1] b[^2]" in text and text.rstrip().endswith("[^1]: uno\n[^2]: dos")


# --- Lists, quotes and code ----------------------------------------------------------------------


def test_lists_take_their_kind_and_start_from_their_style(tmp_path: Path) -> None:
    text = body(
        tmp_path,
        '<text:list text:style-name="L2"><text:list-item><text:p>c</text:p></text:list-item>'
        '<text:list-item text:start-value="7"><text:p>g</text:p></text:list-item></text:list>'
        '<text:list text:style-name="L1"><text:list-item><text:p>x</text:p>'
        "<text:list><text:list-item><text:p>y</text:p></text:list-item></text:list>"
        "</text:list-item></text:list>",
    )
    assert "3. c\n7. g" in text
    assert "- x\n  1. y" in text


def test_consecutive_quotations_and_code_paragraphs_are_one_block(tmp_path: Path) -> None:
    text = body(
        tmp_path,
        '<text:p text:style-name="P1">uno</text:p><text:p text:style-name="P1">dos</text:p>'
        '<text:p text:style-name="P2">a &lt;b&gt;</text:p>'
        '<text:p text:style-name="P2"><text:tab/>[x](y)</text:p>',
    )
    assert "> uno\n> dos" in text
    assert "```\na <b>\n\t[x](y)\n```" in text


# --- Tables --------------------------------------------------------------------------------------


def test_repeated_cells_and_rows_are_bounded(tmp_path: Path) -> None:
    text = body(
        tmp_path,
        "<table:table><table:table-row>"
        "<table:table-cell><text:p>a</text:p></table:table-cell>"
        '<table:table-cell table:number-columns-repeated="16000"/>'
        '</table:table-row><table:table-row table:number-rows-repeated="1048000">'
        '<table:table-cell table:number-columns-repeated="16001"/></table:table-row></table:table>',
    )
    assert text.strip() == "| a |\n|---|"


def test_a_table_with_merged_cells_is_simplified_and_noted() -> None:
    markdown, found = convert(ODT_DIR / "merged.odt")
    assert "| Junta |  |\n|---|---|\n| a | b |" in markdown
    assert found[NoteKind.TABLE_SIMPLIFIED] == (NoteItem("1"),)


# --- Honesty -------------------------------------------------------------------------------------


def test_comments_and_tracked_changes_give_the_final_text() -> None:
    markdown, found = convert(ODT_DIR / "revisions.odt")
    assert "Texto final." in markdown and "borrado" not in markdown and "comentario" not in markdown
    assert found[NoteKind.REVISIONS_DROPPED] == (
        NoteItem("1", NoteReason.COMMENTS.value),
        NoteItem("1", NoteReason.TRACKED_CHANGES.value),
    )


def test_unknown_elements_keep_their_text_and_are_listed_once() -> None:
    markdown, found = convert(ODT_DIR / "unknown.odt")
    assert "texto en forma" in markdown and "漢字 fin" in markdown
    assert found[NoteKind.ELEMENTS_SIMPLIFIED] == (
        NoteItem("draw:custom-shape"),
        NoteItem("text:ruby"),
    )


def test_generated_content_and_declarations_leave_nothing(tmp_path: Path) -> None:
    found = notes(
        tmp_path,
        '<text:sequence-decls><text:sequence-decl text:name="Figure"/></text:sequence-decls>'
        "<text:table-of-content><text:index-body><text:p>Indice</text:p></text:index-body>"
        '</text:table-of-content><office:forms/><text:p>x<text:bookmark text:name="b"/></text:p>',
    )
    assert found == {}


def test_a_wide_document_converts_in_reasonable_time() -> None:
    started = time.monotonic()
    markdown, _ = convert(ODT_DIR / "hostile" / "many_elements.odt")
    assert markdown.count("x") == 300_000
    assert time.monotonic() - started < 30


@pytest.mark.parametrize("name", ["real/report.odt"])
def test_libreoffices_own_file_converts(name: str) -> None:
    markdown, found = convert(ODT_DIR / name)
    for expected in (
        "# Informe real de LibreOffice",
        "## Resumen",
        "**negrita**",
        "`monoespacio`",
        "mc<sup>2</sup>",
        "1. paso uno",
        "[LibreOffice](https://www.libreoffice.org/)",
        "> Una cita de prueba.",
        "```\ndef f(x):\n    return x * 2\n```",
        "| Columna A | Columna B |",
        "[^1]: Nota al pie real.",
    ):
        assert expected in markdown, expected
    assert found[NoteKind.REVISIONS_DROPPED] == (NoteItem("1", NoteReason.COMMENTS.value),)
