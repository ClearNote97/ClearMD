"""trafilatura's XML → Markdown through ClearMD's own writing (004, T04)."""

from markdown_it import MarkdownIt
from support.markdown_guarantee import broken_promises

from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.html.render import ArticleRenderer
from clearmd.backend.services.conversion.xmltree import parse_part

PARSER = MarkdownIt("commonmark").enable("table")


def render(main: str, title: str = "T", language: str = "en") -> tuple[str, set[NoteKind]]:
    tree = parse_part(f'<body><head rend="h1">{title}</head>{main}</body>'.encode())
    renderer = ArticleRenderer(language=language, source_size=len(main))
    markdown = renderer.document(tree)
    return markdown, {note.kind for note in renderer.notes()}


def test_the_title_and_headings_the_shallowest_at_level_two() -> None:
    markdown, _ = render('<head rend="h2">A</head><head rend="h3">B</head>')
    assert markdown == "# T\n\n## A\n\n### B\n"


def test_paragraphs_emphasis_code_and_line_breaks() -> None:
    markdown, _ = render(
        '<p>a <hi rend="#b">b</hi> <hi rend="#i">i</hi> <hi rend="#u">u</hi> <hi rend="#t">t</hi>'
        ' <hi rend="#sup">2</hi> <del rend="overstrike">s</del><lb/>next</p>'
    )
    assert "a **b** *i* <u>u</u> `t` <sup>2</sup> ~~s~~  \nnext" in markdown


def test_links_follow_the_link_rules() -> None:
    markdown, _ = render(
        '<p>see <ref target="https://x.org/a">the site</ref> and '
        '<ref target="javascript:alert(1)">this</ref></p>'
    )
    assert "[the site](https://x.org/a)" in markdown
    assert "this (`javascript:alert(1)`)" in markdown


def test_lists_nested_and_ordered() -> None:
    markdown, _ = render(
        '<list rend="ul"><item>a</item><item>b<list rend="ul"><item>c</item></list></item></list>'
        '<list rend="ol"><item>one</item><item>two</item></list>'
    )
    html = PARSER.render(markdown)
    assert "<li>b\n<ul>\n<li>c</li>" in html and "<ol>\n<li>one</li>\n<li>two</li>" in html


def test_quotes_code_and_tables() -> None:
    markdown, _ = render(
        "<quote><p>said</p></quote><code>x = 1\n  y</code>"
        '<table><row><cell role="head">A</cell><cell role="head">B</cell></row>'
        "<row><cell>1</cell><cell>a|b</cell></row></table>"
    )
    assert "> said" in markdown and "```\nx = 1\n  y\n```" in markdown
    assert "| A | B |\n|---|---|\n| 1 | a\\|b |" in markdown


def test_images_are_placeholders_with_a_note() -> None:
    markdown, kinds = render(
        '<graphic src="https://cdn.example/x.jpg" alt="A river"/>', language="es"
    )
    assert markdown.endswith("*Imagen: A river*\n") and "cdn.example" not in markdown
    assert NoteKind.IMAGES_NOT_DOWNLOADED in kinds


def test_hostile_text_never_breaks_the_guarantee() -> None:
    markdown, _ = render(
        "<p>&lt;img src=x onerror=alert(1)&gt; ![x](http://evil/b.png) [t](javascript:x)</p>"
        "<p># h<lb/>- l<lb/>&gt; q<lb/>===</p>"
        '<p><ref target="//evil.example/x">no scheme</ref></p>'
    )
    assert broken_promises(markdown, blocks=frozenset({"heading_open"})) == []  # the title


def test_unknown_elements_keep_their_text_with_a_note() -> None:
    markdown, kinds = render("<p>a <foo>kept</foo></p><bar>block</bar>")
    assert "a kept" in markdown and "block" in markdown
    assert NoteKind.ELEMENTS_SIMPLIFIED in kinds
