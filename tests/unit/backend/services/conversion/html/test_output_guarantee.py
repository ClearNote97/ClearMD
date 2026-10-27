"""The output guarantee of ADR-0023 holds for the article mode (AC-07), checked with a CommonMark
parser: hostile text in every place of a real page, through trafilatura and ClearMD's renderer.

Inline: no HTML, image or link but the page's own allowed ones. Blocks: the page with hostile text
has exactly the block structure of the same page with harmless text (a forged heading, list,
quote, table or fence would change it).
"""

import html
import itertools
import random
from collections import Counter
from pathlib import Path

import pytest
from markdown_it import MarkdownIt
from support.markdown_guarantee import broken_promises

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.html import ArticleConverter

OK_LINK = "https://ok.example/page"
# A link the page wrote, relative, its line break encoded (R1 of feature 003): a link, never HTML.
PAGE_LINKS = frozenset({OK_LINK, "x%0Aonmouseover=alert(1)"})
PARSER = MarkdownIt("commonmark", {"html": True}).enable("table")
CLEARMD_BLOCKS = frozenset(
    {"heading_open", "bullet_list_open", "ordered_list_open", "blockquote_open", "table_open"}
)
FILLER = (
    "Este párrafo es lo bastante largo para que el extractor lo considere parte del artículo "
    "principal de la página, con datos, contexto y una conclusión clara sobre el tema tratado."
)
# Written as text in the page (escaped as HTML), so they reach the article as characters.
BAD_TEXT = [
    "<img src=x onerror=alert(1)>",
    "![x](http://evil.example/b.png)",
    "[t](javascript:alert(1))",
    "`", "a ` b", "``x``", "!", "]", "[a]: http://evil.example/r",
    "# h", "> q", "- i", "1. i", "===", "--", "***", "~~~", "```", "| a | b |",
    "\\", "\\`", "a\\", "\\!", "&#58;", "&amp;", "**", "_x_", "~~s~~", "<!-- c -->",
    "    indented", "# forged", "x\ty",
]  # fmt: skip
# Written as raw HTML inside the article: markup the page itself carries.
BAD_HTML = [
    '<a href="javascript:alert(1)">js</a>',
    '<a href="javascript&#58;alert(1)">entity</a>',
    '<a href="//evil.example/x">no scheme</a>',
    '<a href="data:text/html,<b>x</b>">data</a>',
    '<a href="x&#10;onmouseover=alert(1)">newline</a>',
    '<img src="https://evil.example/i.png" alt="i">',
    "<script>steal()</script>",
    '<iframe src="https://evil.example/f"></iframe>',
    "<b><i>nested</b></i>",
    "<code>&lt;img src=x&gt;</code>",
    # A carriage return in a code block inside a list or a quote (F1 of the audit of 004).
    "</p><ul><li><p>i</p><pre><code>a&#13;# f&#13;&lt;img src=x&gt;&#13;</code></pre></li></ul><p>",
    "</p><blockquote><pre><code>a&#13;- f&#13;&lt;b&gt;x&#13;</code></pre></blockquote><p>",
    "&#1; &#xFFFE; &#11;",  # characters XML forbids (F2)
]
# Where text reaches the article ({t}): every construct of the subset.
PLACES = [
    "<p>{t} " + FILLER + "</p>",
    "<p><strong>{t}</strong> y <em>{t}</em> " + FILLER + "</p>",
    f'<p><a href="{OK_LINK}">{{t}}</a> ' + FILLER + "</p>",
    "<ul><li>{t}</li><li>dos</li></ul>",
    "<ol><li>{t}</li><li>dos</li></ol>",
    "<blockquote><p>{t}</p></blockquote>",
    "<table><tr><th>{t}</th><th>b</th></tr><tr><td>{t}</td><td>c</td></tr></table>",
    "<h2>{t}</h2>",
    '<figure><img src="https://cdn.example/x.jpg" alt="{t}"></figure>',
    "<pre><code>{t}</code></pre>",
    "<ul><li><pre><code>{t}\nmore</code></pre></li></ul><p>{t} " + FILLER + "</p>",
    "<dl><dt>{t}</dt><dd>{t}</dd></dl>",
]


def _page(body: str, title: str = "Un artículo") -> str:
    paragraphs = "".join(f"<p>{FILLER} {n}.</p>" for n in range(3))
    return (
        f'<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>{title}</title></head>'
        f"<body><article><h1>Un artículo</h1>{paragraphs}{body}{paragraphs}</article></body></html>"
    )


def _convert(tmp_path: Path, page: str) -> ConversionResult:
    path = tmp_path / "p.html"
    path.write_text(page, encoding="utf-8")
    detection = Detection(FormatId.HTML, DetectionMethod.EXTENSION)
    return ArticleConverter().convert(path, detection, path.with_suffix(".md"))


def _structure(markdown: str) -> Counter[str]:
    return Counter(t.type for t in PARSER.parse(markdown) if t.nesting == 1 or t.type == "fence")


def _problems(tmp_path: Path, place: str, text: str, *, raw: bool = False) -> list[str]:
    """Inline problems, and a block structure other than the same page's with harmless text
    (for raw markup, which brings blocks of its own: one heading, the title, and no other)."""
    inserted = text if raw else html.escape(text, quote=True)
    result = _convert(tmp_path, _page(place.format(t=inserted)))
    # Every page here has an article: a fallback would leave the case untested.
    assert NoteKind.ARTICLE_NOT_FOUND not in {note.kind for note in result.notes}, place
    harmless = _convert(tmp_path, _page(place.format(t="texto")))
    found = broken_promises(
        result.markdown, allowed_links=PAGE_LINKS, blocks=CLEARMD_BLOCKS | {"fence"}
    )
    structure = _structure(result.markdown)
    if (structure["heading_open"] != 1) if raw else (structure != _structure(harmless.markdown)):
        found.append(f"structure {structure} in {result.markdown!r}")
    return found


@pytest.mark.parametrize("place", PLACES)
def test_hostile_text_in_every_place_never_breaks_the_guarantee(place: str, tmp_path: Path) -> None:
    broken = {text: found for text in BAD_TEXT if (found := _problems(tmp_path, place, text))}
    assert broken == {}


@pytest.mark.parametrize("markup", BAD_HTML)
def test_hostile_markup_never_breaks_the_guarantee(markup: str, tmp_path: Path) -> None:
    place = "<p>{t} " + FILLER + "</p>"
    assert _problems(tmp_path, place, markup, raw=True) == []


def test_a_hostile_title_stays_one_heading(tmp_path: Path) -> None:
    for text in ("# x\n- y", "<img src=x>", "[t](javascript:x)", "x\n===\n"):
        result = _convert(tmp_path, _page("", title=html.escape(text)))
        assert broken_promises(result.markdown, blocks=CLEARMD_BLOCKS) == []


def test_a_seeded_fuzz_of_places_and_text_never_breaks_it(tmp_path: Path) -> None:
    rng = random.Random(2026)
    broken = {}
    for _ in range(150):
        place = rng.choice(PLACES)
        text = "".join(rng.choice(BAD_TEXT) for _ in range(rng.randint(1, 4)))
        if found := _problems(tmp_path, place, text):
            broken[(place, text)] = found
    assert dict(itertools.islice(broken.items(), 3)) == {}


def _whole_page(tmp_path: Path, body: str) -> ConversionResult:
    """A page with no article: the whole page, written by ClearMD."""
    path = tmp_path / "w.html"
    path.write_text(
        f"<html><head><title>Página</title></head><body>{body}</body></html>", encoding="utf-8"
    )
    return ArticleConverter().convert(
        path, Detection(FormatId.HTML, DetectionMethod.EXTENSION), path
    )


@pytest.mark.parametrize("place", PLACES)
def test_the_whole_page_written_by_clearmd_keeps_the_guarantee(place: str, tmp_path: Path) -> None:
    short = place.replace(" " + FILLER, "")
    harmless = _structure(_whole_page(tmp_path, short.format(t="texto")).markdown)
    broken = {}
    for text in BAD_TEXT:
        result = _whole_page(tmp_path, short.format(t=html.escape(text, quote=True)))
        assert NoteKind.ARTICLE_NOT_FOUND in {note.kind for note in result.notes}
        found = broken_promises(
            result.markdown, allowed_links=PAGE_LINKS, blocks=CLEARMD_BLOCKS | {"fence"}
        )
        if _structure(result.markdown) != harmless:
            found.append(f"structure in {result.markdown!r}")
        if found:
            broken[text] = found
    assert broken == {}
