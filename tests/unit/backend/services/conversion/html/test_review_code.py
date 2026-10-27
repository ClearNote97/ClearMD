"""Regressions for the code review of feature 004 (H1–H2, M1–M6, L1–L13), each from its input."""

import gzip
import time
from pathlib import Path

import pytest
from markdown_it import MarkdownIt

from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.formats import FormatId, Strategy
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    ConversionResult,
    Detection,
    DetectionMethod,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.html import ArticleConverter
from clearmd.backend.services.conversion.html.render import ArticleRenderer
from clearmd.backend.services.conversion.markdown_out import link_target
from clearmd.backend.services.conversion.xmltree import parse_part
from clearmd.backend.services.rejections import stopped_message
from clearmd.backend.use_cases.planning import build_plan
from clearmd.i18n import load_catalog

PARSER = MarkdownIt("commonmark").enable(["table", "strikethrough"])
FILLER = (
    "Un párrafo largo del artículo, con suficiente texto para que el extractor lo tome como "
    "contenido principal de la página y no como ruido de navegación, menú o pie de página."
)
DETECTION = Detection(FormatId.HTML, DetectionMethod.EXTENSION)


class _FullPage:
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        return ConversionResult("FULL\n", ())


def render(body: str, *, title: str = "", language: str = "en") -> str:
    renderer = ArticleRenderer(language=language, source_size=len(body))
    return renderer.document(parse_part(f"<body>{body}</body>".encode()), title=title)


def page(tmp_path: Path, article: str, *, head: str = "", before: str = "") -> str:
    filler = "".join(f"<p>{FILLER} {n}.</p>" for n in range(3))
    path = tmp_path / "p.html"
    path.write_text(
        f'<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">{head}</head><body>{before}'
        f"<article>{article}{filler}</article></body></html>",
        encoding="utf-8",
    )
    return ArticleConverter(_FullPage()).convert(path, DETECTION, path.with_suffix(".md")).markdown


# --- High ----------------------------------------------------------------------------------------


def test_h1_inline_code_and_quotes_stay_in_their_sentence() -> None:
    markdown = render(
        '<list rend="ul"><item>Use <code>ls -la</code> to list files</item>'
        "<item>He said <quote>hi there</quote> to me</item></list>"
        "<quote>Run <code>make</code> then wait</quote>"
    )
    assert "- Use `ls -la` to list files" in markdown
    assert "He said hi there to me" in markdown and "> Run `make` then wait" in markdown
    assert "```" not in markdown


def test_h2_line_breaks_inside_a_code_block_are_kept() -> None:
    markdown = render("<code><code>line1<lb/>line2<lb/>line3</code></code>")
    assert "```\nline1\nline2\nline3\n```" in markdown


# --- Medium --------------------------------------------------------------------------------------


def test_m1_the_title_is_found_wherever_the_h1_is(tmp_path: Path) -> None:
    hero = page(
        tmp_path,
        '<img src="h.jpg" alt="Hero"><h1>The Real Title</h1><h2>Part</h2>',
        head="<title>Site | The Real Title</title>",
    )
    assert hero.startswith("# The Real Title\n") and "## Part" in hero
    outside = page(
        tmp_path, "<h2>Sección</h2>", head="<title>Página de prueba</title>", before="<header/>"
    )
    assert outside.startswith("# Página de prueba\n") and "## Sección" in outside


def test_m2_a_query_string_stays_a_link() -> None:
    markdown = render('<p><ref target="https://x.org/w?title=B&amp;action=edit">editar</ref></p>')
    html = PARSER.render(markdown)
    assert 'href="https://x.org/w?title=B&amp;action=edit"' in html
    assert link_target("javascript&colon;alert(1)") == "<javascript\\&colon;alert(1)>"


def test_m3_an_image_next_to_emphasis_never_shows_asterisks() -> None:
    markdown = render('<p>A <hi rend="#i">word<graphic alt="pic"/></hi>after</p>')
    assert "*" not in PARSER.render(markdown).replace("<em>", "").replace("</em>", "")


def test_m4_an_item_with_many_paragraphs_is_linear() -> None:
    started = time.monotonic()
    render('<list rend="ul"><item>' + "<p>x</p>" * 40_000 + "</item></list>")
    assert time.monotonic() - started < 5


def test_m5_a_compressed_page_is_never_decompressed(tmp_path: Path) -> None:
    filler = "".join(f"<p>{FILLER} {n}.</p>" for n in range(5))
    path = tmp_path / "p.html"
    path.write_bytes(
        gzip.compress(f"<html><body><article>{filler}</article></body></html>".encode())
    )
    result = ArticleConverter(_FullPage()).convert(path, DETECTION, path.with_suffix(".md"))
    assert result.markdown == "FULL\n"  # no article in the bytes as they are on disk


def test_m6_a_page_too_big_for_the_article_is_planned_in_full(tmp_path: Path) -> None:
    (tmp_path / "big.html").write_bytes(b"<p>" + b"x" * 3 * 1024**2 + b"</p>")

    class _Html:
        def detect(self, path: Path) -> Detection:
            return DETECTION

    limits = Limits(worker_memory=150 * 1024**2 + 1)  # the full page fits, the article does not
    limits = Limits(worker_memory=limits.estimated_memory(FormatId.HTML, 3 * 1024**2 + 7) + 1)
    plan = build_plan([tmp_path], detector=_Html(), limits=limits, html_strategy=Strategy.ARTICLE)
    (item,) = plan.conversions
    assert item.strategy is Strategy.FULL and not plan.skipped
    assert [warning.item for warning in plan.strategy_warnings] == [item]


# --- Low -----------------------------------------------------------------------------------------


def test_l1_definition_lists_keep_terms_apart() -> None:
    markdown = render(
        '<list rend="dl"><item rend="dt-1">IDIGER</item>'
        '<item rend="dd-1">El instituto</item></list>'
    )
    assert "**IDIGER**" in markdown and "El instituto" in markdown


def test_l2_a_caption_row_is_not_the_header() -> None:
    markdown = render(
        '<table><row><cell role="head">Reportes</cell></row>'
        '<row><cell role="head">Localidad</cell><cell role="head">N</cell></row>'
        "<row><cell>Suba</cell><cell>3</cell></row></table>"
    )
    assert "| Localidad | N |\n|---|---|\n| Suba | 3 |" in markdown and "Reportes" in markdown


def test_l3_a_line_break_after_a_space_gives_one_space() -> None:
    markdown = render('<head rend="h2">Lluvias dejan <lb/>inundaciones</head>')
    assert "## Lluvias dejan inundaciones" in markdown


def test_l4_paragraphs_of_a_quote_have_one_empty_line_between() -> None:
    markdown = render("<quote><p>uno</p><p>dos</p></quote>")
    assert "> uno\n>\n> dos" in markdown


def test_l5_a_heading_without_level_never_outranks_its_section() -> None:
    markdown = render(
        '<head rend="h2">Sección</head><head rend="h4">Sub</head><head>Spoiler</head>'
    )
    assert "## Sección" in markdown and "**Spoiler**" in markdown


def test_l6_lists_deeper_than_ten_levels_are_flattened() -> None:
    body = "<item>deep</item>"
    for _ in range(40):
        body = f'<item>x<list rend="ul">{body}</list></item>'
    markdown = render(f'<list rend="ul">{body}</list>')
    assert "deep" in markdown
    assert max(len(line) - len(line.lstrip()) for line in markdown.split("\n")) <= 2 * 11


def test_l9_the_images_note_reads_as_a_count() -> None:
    text = load_catalog("en").text("note.images_not_downloaded", items="`2`")
    assert text.startswith("images not downloaded")


def test_l12_data_lang_is_not_the_page_language(tmp_path: Path) -> None:
    filler = "".join(f"<p>{FILLER} {n}.</p>" for n in range(3))
    path = tmp_path / "p.html"
    path.write_text(
        f'<html data-lang="de" lang="es"><body><article>{filler}<img src="x.jpg" alt="foto">'
        f"{filler}</article></body></html>",
        encoding="utf-8",
    )
    result = ArticleConverter(_FullPage()).convert(path, DETECTION, path.with_suffix(".md"))
    assert "*Imagen: foto*" in result.markdown


@pytest.mark.parametrize(("limit", "shown"), [(600, "10 min"), (150, "150 s"), (30, "30 s")])
def test_l13_a_time_limit_is_shown_exactly(limit: float, shown: str) -> None:
    item = PlannedConversion(
        Path("a.pdf"), Path("o"), Path("o/a.md"), DETECTION, exists=False, cost=1.0
    )
    outcome = ConversionOutcome(item, OutcomeStatus.STOPPED, ErrorCode.TIMED_OUT, limit=limit)
    assert f"({shown})" in stopped_message(load_catalog("en"), outcome)


def test_m8_a_failure_inside_trafilatura_falls_back_to_the_full_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import trafilatura

    def broken(*args: object, **kwargs: object) -> None:
        raise ValueError("inside trafilatura")

    monkeypatch.setattr(trafilatura, "bare_extraction", broken)
    path = tmp_path / "p.html"
    path.write_text("<p>x</p>", encoding="utf-8")
    result = ArticleConverter(_FullPage()).convert(path, DETECTION, path.with_suffix(".md"))
    assert result.markdown == "FULL\n"
    assert NoteKind.ARTICLE_NOT_FOUND in {note.kind for note in result.notes}
