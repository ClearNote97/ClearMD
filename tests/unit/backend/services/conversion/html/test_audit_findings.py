"""Regressions for the security audit of feature 004 (F1–F7), each from its reported input."""

import os
import resource
import time
from pathlib import Path

import pytest
from support.markdown_guarantee import broken_promises

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.html import ArticleConverter
from clearmd.backend.services.conversion.markdown_out import neutralize, tidy
from clearmd.backend.services.conversion.safe_files import NotARegularFile, read_regular_file

DETECTION = Detection(FormatId.HTML, DetectionMethod.EXTENSION)
FILLER = (
    "Un párrafo largo del artículo, con suficiente texto para que el extractor lo tome como "
    "contenido principal de la página y no como ruido de navegación, menú o pie de página."
)
BLOCKS = frozenset({"heading_open", "bullet_list_open", "blockquote_open"})
REMOTE = "http://evil.example/t.png"


class _FullPage:
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        return ConversionResult("FULL\n", ())


def convert(tmp_path: Path, article: str) -> ConversionResult:
    filler = "".join(f"<p>{FILLER} {n}.</p>" for n in range(3))
    path = tmp_path / "p.html"
    path.write_text(
        f'<html lang="es"><body><article><h1>T</h1>{filler}{article}{filler}</article>'
        "</body></html>",
        encoding="utf-8",
    )
    return ArticleConverter(_FullPage()).convert(path, DETECTION, path.with_suffix(".md"))


@pytest.mark.parametrize(
    "container",
    [
        "<ul><li><p>item</p><pre><code>{c}</code></pre></li><li>dos</li></ul>",
        "<blockquote><pre><code>{c}</code></pre></blockquote>",
    ],
)
def test_f1_a_carriage_return_never_leaves_its_code_block(container: str, tmp_path: Path) -> None:
    code = "a&#13;# forged&#13;&lt;img src=x onerror=alert(1)&gt;&#13;"
    markdown = convert(tmp_path, container.format(c=code)).markdown
    assert "\r" not in markdown
    assert broken_promises(markdown, blocks=BLOCKS | {"fence"}) == []
    assert markdown.count("\n# ") + markdown.startswith("# ") == 1  # the title only


def test_f1_every_line_ending_is_one_for_the_shared_writer() -> None:
    assert tidy("a\r# b\r\nc") == "a\n# b\nc\n" and neutralize("a\r# b") == "a\n\\# b"


@pytest.mark.parametrize("reference", ["&#1;", "&#11;", "&#x1F;", "&#xFFFE;"])
def test_f2_a_character_xml_forbids_never_turns_the_article_off(
    reference: str, tmp_path: Path
) -> None:
    result = convert(tmp_path, f"<p>{reference} {FILLER}</p><img src='{REMOTE}'>")
    assert result.markdown != "FULL\n" and REMOTE not in result.markdown
    assert NoteKind.ARTICLE_NOT_FOUND not in {note.kind for note in result.notes}


def test_f3_runs_of_formatting_stay_within_memory(tmp_path: Path) -> None:
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    started = time.monotonic()
    convert(tmp_path, "<p>" + "<b>a</b> " * 50_000 + "</p>")
    grown = (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - before) / 1024
    assert time.monotonic() - started < 20 and grown < 800  # MiB (was about 2.5 GB)


def test_f4_a_page_with_too_many_elements_is_converted_in_full(tmp_path: Path) -> None:
    result = convert(tmp_path, "<p>" + "<span>x</span>" * 60_000 + "</p>")
    assert result.markdown == "FULL\n"
    assert NoteKind.ARTICLE_TOO_COMPLEX in {note.kind for note in result.notes}


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs exist on POSIX only")
def test_f6_a_fifo_never_blocks_the_read(tmp_path: Path) -> None:
    fifo = tmp_path / "page.html"
    os.mkfifo(fifo)
    started = time.monotonic()
    with pytest.raises(NotARegularFile):
        read_regular_file(fifo, 1024)
    assert time.monotonic() - started < 2


def test_f7_a_heading_ending_in_a_hash_keeps_it(tmp_path: Path) -> None:
    markdown = convert(tmp_path, "<h2>Lenguaje C#</h2>").markdown
    assert "## Lenguaje C\\#" in markdown
