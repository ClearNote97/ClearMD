"""Regressions for the second verification of 004's fixes (R1–R6), each from its input."""

import time
from pathlib import Path

from markdown_it import MarkdownIt

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.services.conversion import html as article_module
from clearmd.backend.services.conversion.html import ArticleConverter
from clearmd.backend.services.conversion.html.render import ArticleRenderer
from clearmd.backend.services.conversion.xmltree import parse_part

DETECTION = Detection(FormatId.HTML, DetectionMethod.EXTENSION)
PARSER = MarkdownIt("commonmark").enable("table")


def whole(tmp_path: Path, body: str, monkeypatch: object = None) -> ConversionResult:
    path = tmp_path / "w.html"
    path.write_text(f"<html><head><title>T</title></head><body>{body}</body></html>", "utf-8")
    return ArticleConverter().convert(path, DETECTION, path.with_suffix(".md"))


def render(body: str) -> str:
    return ArticleRenderer(language="en", source_size=len(body)).document(
        parse_part(f"<body>{body}</body>".encode())
    )


def fences(markdown: str) -> list[int]:
    return [token.level for token in PARSER.parse(markdown) if token.type == "fence"]


def test_r1_code_opening_an_item_stays_in_the_item() -> None:
    items = "".join(f"<item>{n}</item>" for n in range(9))
    markdown = render(
        f'<list rend="ol">{items}<item><code><code>a\nb</code></code></item></list>'
        '<list rend="ul"><item><code><code>c\nd</code></code></item><item>second</item></list>'
    )
    html = PARSER.render(markdown)
    assert fences(markdown) and min(fences(markdown)) > 0, markdown  # every fence inside an item
    assert "code_block" not in [token.type for token in PARSER.parse(markdown)]
    assert html.count("<ul>") == 1 and "<li></li>" not in html


def test_r2_two_inline_codes_in_a_row_stay_inline() -> None:
    markdown = render('<list rend="ul"><item><code>Ctrl</code> <code>C</code> copies</item></list>')
    assert "- `Ctrl` `C` copies" in markdown


def test_r3_a_table_nested_in_a_table_keeps_its_text() -> None:
    markdown = render(
        "<table><row><cell>a</cell><cell>b</cell></row>"
        "<div><table><row><cell>INNER1</cell><cell>INNER2</cell></row></table></div></table>"
    )
    assert "INNER1" in markdown and "INNER2" in markdown


def test_r4_rows_past_the_limit_keep_their_cells_apart(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from clearmd.backend.services.conversion.html.writer import tables as render_module

    monkeypatch.setattr(render_module, "MAX_CELLS", 4)
    rows = "".join(f"<row><cell>r{n}a</cell><cell>r{n}b</cell></row>" for n in range(4))
    markdown = render(f"<table>{rows}</table>")
    assert "r3a r3b" in markdown and markdown.count("r2a") == 1


def test_r5_the_title_is_the_first_h1_with_text(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(article_module, "_article", lambda text: None)
    markdown = whole(
        tmp_path, '<h1><a href="/"><img src="l.png" alt="Site"></a></h1><h1>Real</h1><p>x</p>'
    ).markdown
    assert markdown.startswith("# Real\n")


def test_r6_many_inline_codes_are_linear() -> None:
    started = time.monotonic()
    render("<p>" + "<code>x</code> " * 40_000 + "</p>")
    render("<div>" + "<code>x</code> " * 40_000 + "</div>")
    assert time.monotonic() - started < 10
