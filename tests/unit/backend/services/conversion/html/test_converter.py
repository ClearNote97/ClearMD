"""The article converter on the fixture pages, with the full-page fallback (004, T04)."""

from pathlib import Path

from build_fixtures import HTML_DIR

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.html import ArticleConverter

DETECTION = Detection(FormatId.HTML, DetectionMethod.EXTENSION)


class _FullPage:
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        return ConversionResult("FULL PAGE\n", ())


def convert(name: str) -> ConversionResult:
    path = HTML_DIR / name
    return ArticleConverter(_FullPage()).convert(path, DETECTION, path.with_suffix(".md"))


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
    assert result.markdown == "FULL PAGE\n"
    assert NoteKind.ARTICLE_NOT_FOUND in {note.kind for note in result.notes}
