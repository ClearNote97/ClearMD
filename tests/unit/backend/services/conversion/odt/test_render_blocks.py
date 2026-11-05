"""The text subset of spec 003, row by row: blocks and limits (AC-05 – AC-09, AC-13 – AC-14)."""

import time
from pathlib import Path

import pytest
from support import ODT_DIR
from support.odt_render import body, convert, notes

from clearmd.backend.schemas.notes import NoteItem, NoteKind, NoteReason


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
