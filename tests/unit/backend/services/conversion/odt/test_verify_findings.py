"""Feature 003 verification (N1-N21): output guarantee and budgets.

Regressions, each from its reported input."""

from pathlib import Path

from support.markdown_guarantee import broken_promises
from support.odt_verify import MATH, MIB, MONO_HTML, NOTE, PARSER, convert, md, timed

from clearmd.backend.schemas.notes import NoteKind


def test_n1_n12_a_footnote_before_a_link_keeps_the_link_and_no_url_is_live(tmp_path: Path) -> None:
    body = f'<text:p>a{NOTE}<text:a xlink:href="https://e.org/a`">t</text:a>{MONO_HTML}</text:p>'
    markdown = md(tmp_path, body)
    assert broken_promises(markdown, allowed_links=frozenset({"https://e.org/a%60"})) == []
    two = md(tmp_path, f'<text:p>see{NOTE}<text:a xlink:href="https://e.org/">the site</text:a>'
                       f"{NOTE}{NOTE}</text:p>")  # fmt: skip
    assert "see[^1][the site](https://e.org/)[^2][^3]" in two


def test_n2_a_backslash_and_bang_of_the_document_never_make_an_image(tmp_path: Path) -> None:
    link = md(tmp_path, '<text:p>a\\!<text:a xlink:href="https://e.org/x.png">t</text:a></text:p>')
    assert broken_promises(link, allowed_links=frozenset({"https://e.org/x.png"})) == []
    note = md(
        tmp_path,
        "<text:p>a\\!<text:note><text:note-body><text:p>http://evil/x.png</text:p>"
        "</text:note-body></text:note></text:p>",
    )
    assert broken_promises(note) == []


def test_the_checker_counts_backslashes_and_sees_images_made_with_definitions() -> None:
    assert broken_promises("a\\\\![^1]\n\n[^1]: http://evil/x.png\n") != []
    assert broken_promises("a\\![^1]\n\n[^1]: http://evil/x.png\n") == []


def test_n3_a_long_link_split_in_pieces_is_written_within_the_budget(tmp_path: Path) -> None:
    url = "https://e.org/" + "a" * 100_000
    pieces = "x<text:line-break/>" * 200
    markdown = timed(20, tmp_path, f'<text:p><text:a xlink:href="{url}">{pieces}</text:a></text:p>')
    assert len(markdown) < 3 * MIB and "x" in markdown


def test_n4_a_starmath_source_referenced_many_times_is_within_the_budget(tmp_path: Path) -> None:
    unsupported = (
        f'<math {MATH}><semantics><mrow><mzzz>u</mzzz></mrow><annotation encoding="StarMath 5.0">'
        + "x" * 200_000
        + "</annotation></semantics></math>"
    )
    frame = '<draw:frame><draw:object xlink:href="./Object 1"/></draw:frame>'
    markdown = timed(
        20, tmp_path, "<text:p>" + ("a " + frame) * 100 + "</text:p>",
        {"Object 1/content.xml": unsupported.encode()},
    )  # fmt: skip
    assert len(markdown) < 3 * MIB and "*Formula*" in markdown


def test_n5_n6_a_wide_sparse_table_is_neither_huge_nor_slow(tmp_path: Path) -> None:
    empty = '<table:table-cell table:number-columns-repeated="64"/>'
    first = f"<table:table-row><table:table-cell><text:p>a</text:p></table:table-cell>{empty * 780}"
    first += "<table:table-cell><text:p>end</text:p></table:table-cell></table:table-row>"
    row = (
        '<table:table-row table:number-rows-repeated="64"><table:table-cell><text:p>y</text:p>'
        "</table:table-cell></table:table-row>"
    )
    markdown = timed(10, tmp_path, f"<table:table>{first}{row * 40}</table:table>")
    assert len(markdown) < 3 * MIB and "end" in markdown and markdown.count("| y |") == 2560


def test_n7_many_pieces_in_one_paragraph_are_linear(tmp_path: Path) -> None:
    markdown = timed(5, tmp_path, "<text:p>" + 'a<text:s text:c="256"/>' * 20_000 + "</text:p>")
    assert markdown.count("a") == 20_000


def test_repeated_spaces_are_charged_too(tmp_path: Path) -> None:
    markdown = timed(10, tmp_path, "<text:p>" + 'a<text:s text:c="256"/>' * 100_000 + "</text:p>")
    assert len(markdown) < 3 * MIB and markdown.count("a") == 100_000


def test_n18_formatting_that_markdown_cannot_hold_is_dropped_and_said(tmp_path: Path) -> None:
    body = '<text:p>word<text:span text:style-name="T1">"quoted"</text:span>s</text:p>'
    markdown, kinds = convert(tmp_path, body)
    assert PARSER.render(markdown) == "<p>word&quot;quoted&quot;s</p>\n"
    assert NoteKind.FORMATTING_DROPPED in kinds
    kept = md(tmp_path, '<text:p>a <text:span text:style-name="T1">"b"</text:span> c</text:p>')
    assert "<strong>" in PARSER.render(kept)


def test_n19_entities_the_document_wrote_show_as_written(tmp_path: Path) -> None:
    html = PARSER.render(md(tmp_path, "<text:p>&amp;lt;b&amp;gt; &amp;copy; &amp;#91;</text:p>"))
    assert "&amp;lt;b&amp;gt; &amp;copy; &amp;#91;" in html
