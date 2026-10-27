"""The article converter on the fixture pages, with the full-page fallback (004, T04)."""

from pathlib import Path

from build_fixtures import HTML_DIR

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.html import ArticleConverter

DETECTION = Detection(FormatId.HTML, DetectionMethod.EXTENSION)


def convert(name: str) -> ConversionResult:
    path = HTML_DIR / name
    return ArticleConverter().convert(path, DETECTION, path.with_suffix(".md"))


def test_the_article_without_menu_footer_or_banner() -> None:
    result = convert("news.html")
    markdown = result.markdown
    assert markdown.startswith("# Estaciones comunitarias miden el cambio en el Magdalena\n")
    assert "fixture-html-article" in markdown and "## Qué miden" in markdown
    for noise in ("MENU-FIXTURE", "COOKIES-FIXTURE", "ASIDE-FIXTURE", "FOOTER-FIXTURE"):
        assert noise not in markdown
    assert "*Imagen: Una estación junto al río*" in markdown
    assert NoteKind.IMAGES_NOT_DOWNLOADED in {note.kind for note in result.notes}


def test_no_article_means_the_full_page_with_a_note() -> None:
    result = convert("no_article.html")
    assert "fixture-html-no-article" in result.markdown  # the whole page, written by ClearMD
    assert NoteKind.ARTICLE_NOT_FOUND in {note.kind for note in result.notes}


def test_the_whole_page_keeps_the_guarantee(tmp_path: Path) -> None:
    from support.markdown_guarantee import broken_promises

    page = tmp_path / "short.html"
    page.write_text(
        "<html><head><title>Corta</title></head><body><h2>Hola</h2><p>Texto <b>breve</b>.</p>"
        "<ul><li>uno</li><li>dos</li></ul><table><tr><th>a</th></tr><tr><td>1</td></tr></table>"
        '<img src="http://tracker.invalid/t.png" alt="rastreo">'
        '<a href="javascript:alert(1)">script</a> <a href="https://x.org/">bien</a>'
        "<script>steal()</script><p>&lt;img src=x onerror=alert(1)&gt; # no</p></body></html>",
        encoding="utf-8",
    )
    result = ArticleConverter().convert(page, DETECTION, page.with_suffix(".md"))
    markdown = result.markdown
    assert NoteKind.ARTICLE_NOT_FOUND in {note.kind for note in result.notes}
    assert markdown.startswith("# Corta\n") and "## Hola" in markdown and "- uno\n- dos" in markdown
    assert "| a |\n|---|\n| 1 |" in markdown and "*Image: rastreo*" in markdown
    assert "tracker.invalid" not in markdown and "steal" not in markdown
    blocks = frozenset({"heading_open", "bullet_list_open", "table_open"})
    assert (
        broken_promises(markdown, allowed_links=frozenset({"https://x.org/"}), blocks=blocks) == []
    )
