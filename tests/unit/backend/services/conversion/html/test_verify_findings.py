"""Regressions for the adversarial verification of 004's fixes (N1–N10), each from its input."""

from pathlib import Path

import pytest
from markdown_it import MarkdownIt
from support.markdown_guarantee import broken_promises

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.formats import FormatId, Strategy
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion import html as article_module
from clearmd.backend.services.conversion.html import ArticleConverter
from clearmd.backend.use_cases.planning import build_plan

DETECTION = Detection(FormatId.HTML, DetectionMethod.EXTENSION)
PARSER = MarkdownIt("commonmark").enable("table")
FILLER = (
    "Un párrafo largo del artículo, con suficiente texto para que el extractor lo tome como "
    "contenido principal de la página y no como ruido de navegación, menú o pie de página."
)
LISTS = frozenset({"heading_open", "bullet_list_open", "ordered_list_open", "fence"})


def whole(tmp_path: Path, body: str) -> ConversionResult:
    """A page with no article: the whole page, written by ClearMD."""
    path = tmp_path / "w.html"
    path.write_text(f"<html><head><title>T</title></head><body>{body}</body></html>", "utf-8")
    return ArticleConverter().convert(path, DETECTION, path.with_suffix(".md"))


def article(tmp_path: Path, body: str) -> ConversionResult:
    filler = "".join(f"<p>{FILLER} {n}.</p>" for n in range(3))
    path = tmp_path / "a.html"
    path.write_text(
        f"<html><body><article><h1>T</h1>{filler}{body}{filler}</article></body></html>", "utf-8"
    )
    return ArticleConverter().convert(path, DETECTION, path.with_suffix(".md"))


def types(markdown: str) -> list[str]:
    return [token.type for token in PARSER.parse(markdown)]


# --- High ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("path", [whole, article])
def test_n1_a_list_item_starting_with_code_never_frees_later_blocks(path, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    result = path(
        tmp_path,
        "<ul><li><pre><code>code\nmore</code></pre></li></ul>"
        "<p># Forged</p><p>| a | b |<br>|---|---|</p><p>Setext<br>===</p>",
    )
    found = types(result.markdown)
    assert found.count("heading_open") == 1 and "table_open" not in found  # the title only
    assert "fence" in found


# --- Medium --------------------------------------------------------------------------------------


@pytest.mark.parametrize("path", [whole, article])
def test_n2_definitions_are_text_never_blocks(path, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    result = path(tmp_path, "<dl><dt># T</dt><dd># Forged</dd><dd>&gt; q</dd><dd>1. x</dd></dl>")
    found = types(result.markdown)
    assert found.count("heading_open") == 1 and "blockquote_open" not in found
    assert "ordered_list_open" not in found


def test_n3_a_page_too_big_for_the_article_is_skipped_with_what_to_do(tmp_path: Path) -> None:
    (tmp_path / "big.html").write_bytes(b"<p>" + b"x" * 3 * 1024**2 + b"</p>")

    class _Html:
        def detect(self, path: Path) -> Detection:
            return DETECTION

    full = Limits().estimated_memory(FormatId.HTML, 3 * 1024**2 + 7)
    plan = build_plan(
        [tmp_path],
        detector=_Html(),
        limits=Limits(worker_memory=full + 1),
        html_strategy=Strategy.ARTICLE,
    )
    assert not plan.conversions
    (skipped,) = plan.skipped
    assert skipped.reason is SkipReason.TOO_MUCH_MEMORY_FOR_ARTICLE


@pytest.mark.parametrize(
    ("body", "kept"),
    [
        ("<dl><div><dt>TERM</dt><dd>DEF</dd></div></dl>", ["TERM", "DEF"]),
        ("<ul>LOOSE<li>a</li></ul>", ["LOOSE", "a"]),
        ('<ul><a href="/x"><li>NAV</li></a></ul>', ["NAV"]),
        ("<table><form><tr><td>CELL</td><td>2</td></tr></form></table>", ["CELL"]),
        ("<table><caption>CAPTION</caption><tr><th>A</th><th>B</th></tr></table>", ["CAPTION"]),
    ],
)
def test_n4_the_whole_page_keeps_every_text(body: str, kept: list[str], tmp_path: Path) -> None:
    markdown = whole(tmp_path, body).markdown
    assert all(text in markdown for text in kept), markdown


def test_n4_content_after_the_body_is_kept(tmp_path: Path) -> None:
    path = tmp_path / "w.html"
    path.write_text("<html><body><p>uno</p></body><p>AFTERBODY</p></html>", "utf-8")
    result = ArticleConverter().convert(path, DETECTION, path.with_suffix(".md"))
    assert "uno" in result.markdown and "AFTERBODY" in result.markdown


def test_n4_a_page_past_the_limits_is_cut_never_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.backend.services.conversion.html import page
    from clearmd.backend.services.conversion.xmltree import XmlLimits

    monkeypatch.setattr(page, "XmlLimits", lambda: XmlLimits(max_elements=50))
    monkeypatch.setattr(article_module, "_article", lambda text: None)  # no article: the page
    result = whole(tmp_path, "".join(f"<p>p{n}</p>" for n in range(200)))
    assert "p0" in result.markdown and "p199" not in result.markdown
    assert NoteKind.PAGE_CUT in {note.kind for note in result.notes}


@pytest.mark.parametrize("path", [whole, article])
def test_n5_inline_code_stays_inline_and_code_with_lines_is_a_block(path, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    result = path(
        tmp_path,
        "<ul><li><code>--flag</code> <em>(optional)</em> sets the mode</li>"
        "<li>Install:<pre><code>pip install a\npip install b</code></pre></li></ul>",
    )
    markdown = result.markdown
    assert "`--flag` *(optional)* sets the mode" in markdown
    assert "pip install a\n" in markdown


def test_n5_a_blockquote_on_the_whole_page_is_a_quote(tmp_path: Path) -> None:
    markdown = whole(
        tmp_path, "<div>He wrote:<blockquote>A LONG QUOTE</blockquote>and left.</div>"
    ).markdown
    assert "> A LONG QUOTE" in markdown and "wrote:A" not in markdown


def test_n7_a_table_past_the_cell_limit_keeps_its_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.backend.services.conversion.html.writer import tables

    monkeypatch.setattr(tables, "MAX_CELLS", 4)
    rows = "".join(f"<tr><td>r{n}</td><td>x</td></tr>" for n in range(5))
    result = whole(tmp_path, f"<table>{rows}</table>")
    assert "r4" in result.markdown
    assert NoteKind.TABLE_SIMPLIFIED not in {note.kind for note in result.notes}


def test_n8_a_logo_heading_is_not_the_title(tmp_path: Path) -> None:
    logo = whole(tmp_path, '<h1><a href="/"><img src="l.png" alt="Site"></a></h1><p>texto</p>')
    assert logo.markdown.startswith("# T\n")
    empty = whole(tmp_path, "<h1></h1><p>texto</p>")
    assert empty.markdown.startswith("# T\n")


def test_n9_a_reference_with_leading_zeros_is_its_character() -> None:
    assert article_module._xml_safe("&#0000000000065;") == "&#0000000000065;"
    assert article_module._xml_safe("&#00000000001;") == "�"


def test_n10_an_address_with_an_entity_scheme_is_never_a_link(tmp_path: Path) -> None:
    markdown = whole(tmp_path, '<p><a href="javascript&amp;colon;alert(1)">x</a></p>').markdown
    assert broken_promises(markdown, blocks=frozenset({"heading_open"})) == []
