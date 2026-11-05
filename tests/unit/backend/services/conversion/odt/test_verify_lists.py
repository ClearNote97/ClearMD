"""Feature 003 verification (N1-N21): lists and hidden content.

Regressions, each from its reported input."""

import time
from pathlib import Path

from support.odt_verify import MIB, PARSER, convert, md

from clearmd.backend.schemas.notes import NoteKind


def test_n8_lists_deeper_than_ten_levels_are_flattened(tmp_path: Path) -> None:
    body = "<text:p>" + "line<text:line-break/>" * 5_000 + "</text:p>"
    for _ in range(120):
        body = (
            f'<text:list text:style-name="L1"><text:list-item>{body}</text:list-item></text:list>'
        )
    started = time.monotonic()
    markdown, kinds = convert(tmp_path, body)
    assert time.monotonic() - started < 20
    assert len(markdown) < 1 * MIB and NoteKind.ELEMENTS_SIMPLIFIED in kinds
    assert max(len(line) - len(line.lstrip()) for line in markdown.split("\n")) <= 40


def test_n10_two_skipped_list_levels_never_become_code(tmp_path: Path) -> None:
    deep = "<text:list-item><text:p>deep &lt;b&gt;</text:p></text:list-item>"
    body = (
        '<text:list text:style-name="L1"><text:list-item><text:p>x</text:p>'
        f"<text:list><text:list-item><text:list>{deep}</text:list></text:list-item></text:list>"
        "</text:list-item></text:list>"
    )
    tokens = [token.type for token in PARSER.parse(md(tmp_path, body))]
    assert "code_block" not in tokens and tokens.count("bullet_list_open") >= 2


def test_paragraphs_deep_in_a_list_keep_their_item(tmp_path: Path) -> None:
    body = (
        '<text:list text:style-name="L1"><text:list-item><text:p>a</text:p><text:list>'
        "<text:list-item><text:p>b</text:p><text:list><text:list-item><text:p>c</text:p>"
        "<text:p>d<text:line-break/>e</text:p></text:list-item></text:list></text:list-item>"
        "</text:list></text:list-item></text:list>"
    )
    markdown = md(tmp_path, body)
    assert "<p>c</p>\n<p>d<br />\ne</p>\n</li>" in PARSER.render(markdown)
    assert "code_block" not in [token.type for token in PARSER.parse(markdown)]


def test_n11_hidden_sections_comments_and_deletions_inside_containers_stay_out(
    tmp_path: Path,
) -> None:
    hidden = '<text:section text:display="none"><text:p>SECRET</text:p></text:section>'
    annotation = "<office:annotation><text:p>COMMENT</text:p></office:annotation>"
    deletion = (
        '<text:tracked-changes><text:changed-region text:id="c"><text:deletion>'
        "<text:p>DELETED</text:p></text:deletion></text:changed-region></text:tracked-changes>"
    )
    body = (
        f"<table:table><table:table-row><table:table-cell>{hidden}{annotation}{deletion}"
        "<text:p>c</text:p></table:table-cell></table:table-row></table:table>"
        f"<text:p>x<text:note><text:note-body>{hidden}<text:p>n</text:p></text:note-body>"
        f"</text:note><draw:frame><draw:text-box>{hidden}<text:p>box</text:p></draw:text-box>"
        "</draw:frame></text:p>"
    )
    markdown, kinds = convert(tmp_path, body)
    assert "SECRET" not in markdown and "COMMENT" not in markdown and "DELETED" not in markdown
    assert NoteKind.REVISIONS_DROPPED in kinds


def test_n13_a_list_that_restarts_stays_a_list_of_its_own(tmp_path: Path) -> None:
    one = '<text:list text:style-name="L2"><text:list-item><text:p>{}</text:p></text:list-item>'
    body = (one.format("one") + "</text:list>") + (one.format("restarted") + "</text:list>")
    html = PARSER.render(md(tmp_path, body))
    assert html.count("<ol") == 2
