"""Benchmarks of features 001, 002 and 003: conversion time and peak memory per format.

Run inside the container (takes several minutes; results to a JSON file):

    uv run python tests/benchmark/run_benchmark.py --out docs/benchmarks/001-results.json
    uv run python tests/benchmark/run_benchmark.py --only tex tex_macros \
        --out docs/benchmarks/002-results.json
    uv run python tests/benchmark/run_benchmark.py --only odt --out docs/benchmarks/003-results.json
    uv run python tests/benchmark/run_benchmark.py --only html_article \\
        --out docs/benchmarks/004-results.json

Every measurement runs its converter (markitdown, or ClearMD's own for ``.tex`` and ``.odt``) in a
fresh *spawn* process, like the worker of ADR-0015. The
parent samples that process's memory and stops it above ``--memory-cap-mib`` so the benchmark never
exhausts the machine. Generated documents are pseudo-random text with a fixed seed: reproducible,
and compressing like real prose (about 3-4:1) instead of like repeated filler.
"""

import argparse
import json
import multiprocessing
import platform
import random
import resource
import statistics
import sys
import tempfile
import time
import zipfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

import psutil

MIB = 1024**2
SEED = 2026
SAMPLE_SECONDS = 0.05

_SYLLABLES = [
    "ka",
    "lo",
    "mi",
    "ne",
    "ru",
    "ta",
    "so",
    "vi",
    "de",
    "pa",
    "ri",
    "zo",
    "fe",
    "gu",
    "bi",
]


# --- Generators ----------------------------------------------------------------------------------


def _words(rng: random.Random, count: int) -> str:
    return " ".join(
        "".join(rng.choice(_SYLLABLES) for _ in range(rng.randint(1, 4))) for _ in range(count)
    )


def _line(rng: random.Random) -> str:
    return _words(rng, rng.randint(8, 14))


def make_txt(path: Path, size: int, rng: random.Random) -> None:
    with path.open("w", encoding="utf-8") as out:
        while out.tell() < size:
            out.write(_line(rng) + "\n")


def make_csv(path: Path, size: int, rng: random.Random) -> None:
    with path.open("w", encoding="utf-8") as out:
        out.write("id,name,value,comment\n")
        row = 0
        while out.tell() < size:
            row += 1
            out.write(f"{row},{_words(rng, 2)},{rng.random() * 1000:.3f},{_words(rng, 6)}\n")


def make_html(path: Path, size: int, rng: random.Random) -> None:
    with path.open("w", encoding="utf-8") as out:
        out.write(
            "<!DOCTYPE html><html><head><meta charset='utf-8'><title>bench</title></head><body>"
        )
        while out.tell() < size:
            out.write(f"<h2>{_words(rng, 3)}</h2><p>{_words(rng, 120)}</p>\n")
        out.write("</body></html>\n")


def make_html_article(path: Path, size: int, rng: random.Random) -> None:
    """A news page for the article mode (004): menu, cookie banner, aside and footer around an
    article with every construct of the subset (headings, emphasis, links, lists, quotes, tables,
    code, images)."""
    with path.open("w", encoding="utf-8") as out:
        out.write(
            "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'><title>bench</title></head>"
            "<body><nav><a href='/'>Inicio</a> <a href='/x'>Sección</a></nav>"
            "<div class='cookies'>Usamos cookies. <button>Aceptar</button></div>"
            f"<main><article><h1>{_words(rng, 6)}</h1>"
        )
        number = 0
        while out.tell() < size:
            number += 1
            out.write(
                f"<h2>{_words(rng, 3)}</h2><p>{_words(rng, 40)} <strong>{_words(rng, 2)}</strong>"
                f" {_words(rng, 30)} <em>{_words(rng, 2)}</em> <a href='https://example.org/{number}'>"
                f"{_words(rng, 3)}</a> {_words(rng, 40)}</p>"
                f"<ul><li>{_words(rng, 5)}</li><li>{_words(rng, 5)}<ul><li>{_words(rng, 4)}</li>"
                f"</ul></li></ul><blockquote><p>{_words(rng, 20)}</p></blockquote>"
                f"<table><tr><th>{_words(rng, 1)}</th><th>{_words(rng, 1)}</th></tr>"
                f"<tr><td>{number}</td><td>{_words(rng, 2)}</td></tr></table>"
                f"<pre><code>x = {number}</code></pre>"
                f"<figure><img src='https://cdn.example/{number}.jpg'"
                f" alt='{_words(rng, 3)}'></figure>"
                f"<p>{_words(rng, 60)}</p>\n"
            )
        out.write(
            "</article><aside>Te puede interesar</aside></main>"
            "<footer>© 2026</footer></body></html>\n"
        )


def _pdf_page_stream(rng: random.Random) -> bytes:
    lines = " 0 -14 Td ".join(f"({_line(rng)}) Tj" for _ in range(48))
    return f"BT /F1 10 Tf 50 760 Td {lines} ET".encode("latin-1")


def make_pdf(path: Path, size: int, rng: random.Random) -> None:
    """Text-only pages, uncompressed streams, written with a correct xref table."""
    offsets: list[int] = []
    page_ids: list[int] = []
    with path.open("wb") as out:
        out.write(b"%PDF-1.4\n")

        def obj(number: int, body: bytes) -> None:
            while len(offsets) < number:
                offsets.append(0)
            offsets[number - 1] = out.tell()
            out.write(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")

        obj(3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        number = 4
        while out.tell() < size:
            stream = _pdf_page_stream(rng)
            obj(number, b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
            obj(
                number + 1,
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % number,
            )
            page_ids.append(number + 1)
            number += 2
        kids = " ".join(f"{page} 0 R" for page in page_ids)
        obj(2, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode())
        obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
        xref_at = out.tell()
        out.write(f"xref\n0 {len(offsets) + 1}\n0000000000 65535 f \n".encode())
        for offset in offsets:
            out.write(f"{offset:010d} 00000 n \n".encode())
        out.write(
            f"trailer\n<< /Size {len(offsets) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n".encode()
        )


_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
_DOCX_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '<Override PartName="/word/document.xml" ContentType="application/'
    'vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
)
_DOCX_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="word/document.xml"/></Relationships>'
)


def _zip_size(archive: zipfile.ZipFile) -> int:
    assert archive.fp is not None
    return archive.fp.tell()


def make_docx_text(path: Path, size: int, rng: random.Random) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _DOCX_TYPES)
        archive.writestr("_rels/.rels", _DOCX_RELS)
        with archive.open("word/document.xml", "w") as entry:
            entry.write(f'<?xml version="1.0" encoding="UTF-8"?><w:document {_W}><w:body>'.encode())
            while _zip_size(archive) < size:
                entry.write(f"<w:p><w:r><w:t>{_words(rng, 60)}</w:t></w:r></w:p>".encode())
            entry.write(b"</w:body></w:document>")


_DRAWING = (
    '<w:p><w:r><w:drawing><wp:inline><wp:extent cx="914400" cy="914400"/>'
    '<wp:docPr id="{n}" name="Picture {n}" descr="photo {n}"/><a:graphic><a:graphicData '
    'uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:blipFill>'
    '<a:blip r:embed="rIdImg{n}"/></pic:blipFill></pic:pic></a:graphicData></a:graphic>'
    "</wp:inline></w:drawing></w:r></w:p>"
)
_DRAWING_NS = (
    _W + ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
    ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
    ' xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"'
)


def make_docx_images(path: Path, size: int, rng: random.Random) -> None:
    """A Word file whose weight is photos (incompressible 2 MiB images), as most heavy docx are."""
    image_size = 2 * MIB
    count = max(1, size // image_size)
    rels = "".join(
        f'<Relationship Id="rIdImg{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        f'relationships/image" Target="media/image{n}.png"/>'
        for n in range(count)
    )
    body = "".join(
        f"<w:p><w:r><w:t>{_words(rng, 30)}</w:t></w:r></w:p>" + _DRAWING.format(n=n)
        for n in range(count)
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _DOCX_TYPES)
        archive.writestr("_rels/.rels", _DOCX_RELS)
        archive.writestr(
            "word/_rels/document.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?><Relationships '
            f'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}'
            "</Relationships>",
        )
        archive.writestr(
            "word/document.xml",
            f'<?xml version="1.0" encoding="UTF-8"?><w:document {_DRAWING_NS}><w:body>{body}'
            "</w:body></w:document>",
        )
        for n in range(count):
            archive.writestr(zipfile.ZipInfo(f"word/media/image{n}.png"), rng.randbytes(image_size))


def make_epub(path: Path, size: int, rng: random.Random) -> None:
    chapters: list[str] = []
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip")
        archive.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container version="1.0" '
            'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
            '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            "</rootfiles></container>",
        )
        while _zip_size(archive) < size:
            name = f"chapter{len(chapters)}.xhtml"
            paragraphs = "".join(f"<p>{_words(rng, 120)}</p>" for _ in range(200))
            archive.writestr(
                f"OEBPS/{name}",
                '<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml">'
                f"<head><title>{name}</title></head><body><h1>{name}</h1>{paragraphs}</body></html>",
            )
            chapters.append(name)
        manifest = "".join(
            f'<item id="c{i}" href="{name}" media-type="application/xhtml+xml"/>'
            for i, name in enumerate(chapters)
        )
        spine = "".join(f'<itemref idref="c{i}"/>' for i in range(len(chapters)))
        archive.writestr(
            "OEBPS/content.opf",
            '<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" '
            'version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>bench</dc:title></metadata>"
            f"<manifest>{manifest}</manifest><spine>{spine}</spine></package>",
        )


def make_ipynb(path: Path, size: int, rng: random.Random) -> None:
    cells: list[dict[str, Any]] = []
    written = 0
    while written < size:
        text = _words(rng, 150)
        cells.append({"cell_type": "markdown", "metadata": {}, "source": [text]})
        cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [f"value = {rng.random()!r}\n", "print(value)"],
            }
        )
        written += len(text) + 120
    notebook = {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    path.write_text(json.dumps(notebook), encoding="utf-8")


_TEX_PREAMBLE = (
    "\\documentclass{article}\n\\usepackage[spanish]{babel}\n"
    "\\title{Benchmark}\\author{ClearMD}\\date{2026}\n\\begin{document}\n\\maketitle\n"
)
_TEX_MACROS = (
    "\\newcommand{\\R}{\\mathbb{R}}\n"
    "\\newcommand{\\norm}[1]{\\left\\lVert #1 \\right\\rVert}\n"
    "\\newcommand{\\pair}[2][0]{(#1, #2)}\n"
    "\\newcommand{\\term}[1]{\\textbf{#1}}\n"
    "\\newcommand{\\vecx}{\\mathbf{x}}\n"
    "\\DeclareMathOperator{\\argmax}{arg\\,max}\n"
    "\\def\\tool{ClearMD}\n"
)


def _tex_paragraph(rng: random.Random, macros: bool) -> str:
    words = _words(rng, rng.randint(40, 70)).split()
    for _ in range(4):
        at = rng.randrange(len(words))
        words[at] = rng.choice(
            [
                f"\\textbf{{{words[at]}}}",
                f"\\emph{{{words[at]}}}",
                f"\\texttt{{{words[at]}}}",
                f"\\cite{{{words[at]}{rng.randint(1, 99)}}}",
                f"$x_{{{rng.randint(1, 9)}}}^2 + y$",
                "Nicol\\'as --- ``cita''",
            ]
        )
    if macros:
        for _ in range(4):
            at = rng.randrange(len(words))
            words[at] = rng.choice(
                [
                    "$\\vecx \\in \\R^n$",
                    f"$\\norm{{\\vecx_{rng.randint(1, 9)}}}$",
                    f"$\\pair[{rng.randint(1, 9)}]{{b}}$",
                    f"\\term{{{words[at]}}}",
                    "$\\argmax_{\\theta} f$",
                    "\\tool{}",
                ]
            )
    text = " ".join(words) + "."
    if rng.random() < 0.3:
        text += f"\\footnote{{{_words(rng, 8)}.}}"
    return text


def _tex_block(rng: random.Random, number: int) -> str:
    choice = number % 4
    if choice == 0:
        items = "".join(f"\\item {_line(rng)}\n" for _ in range(3))
        return f"\\begin{{itemize}}\n{items}\\end{{itemize}}"
    if choice == 1:
        body = f"\\label{{eq:{number}}}\na_{number}^2 + b^2 = c^2"
        return f"\\begin{{equation}}{body}\n\\end{{equation}}"
    if choice == 2:
        rows = "".join(f"{_words(rng, 1)} & {rng.randint(1, 999)} \\\\\n" for _ in range(4))
        return (
            "\\begin{table}\\centering\n\\begin{tabular}{lr}\n\\hline\n"
            f"{rows}\\hline\n\\end{{tabular}}\n\\caption{{{_words(rng, 3)}}}\n\\end{{table}}"
        )
    return f"\\begin{{quote}}{_line(rng)}\\end{{quote}}"


def _tex(path: Path, size: int, rng: random.Random, *, macros: bool) -> None:
    with path.open("w", encoding="utf-8") as out:
        out.write(_TEX_MACROS if macros else "")
        out.write(_TEX_PREAMBLE)
        number = 0
        while out.tell() < size:
            number += 1
            out.write(f"\\section{{{_words(rng, 3)}}}\n")
            for _ in range(3):
                out.write(_tex_paragraph(rng, macros) + "\n\n")
            out.write(_tex_block(rng, number) + "\n\n")
        out.write("\\end{document}\n")


_ODF = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:xlink="http://www.w3.org/1999/xlink" office:version="1.3"'
)
_ODT_STYLES = (
    "<office:automatic-styles>"
    '<style:style style:name="T1" style:family="text">'
    '<style:text-properties fo:font-weight="bold"/></style:style>'
    '<style:style style:name="T2" style:family="text">'
    '<style:text-properties fo:font-style="italic"/></style:style>'
    '<text:list-style style:name="L1"><text:list-level-style-bullet text:level="1"/>'
    "</text:list-style></office:automatic-styles>"
)
_ODT_FORMULA = (
    '<?xml version="1.0" encoding="UTF-8"?><math xmlns="http://www.w3.org/1998/Math/MathML">'
    "<semantics><mrow><mfrac><mi>a</mi><mi>b</mi></mfrac><mo>+</mo><msup><mi>x</mi><mn>2</mn>"
    '</msup></mrow><annotation encoding="StarMath 5.0">{a over b} + x^2</annotation>'
    "</semantics></math>"
)
_ODT_MANIFEST = (
    '<?xml version="1.0" encoding="UTF-8"?><manifest:manifest '
    'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">'
    '<manifest:file-entry manifest:full-path="/" '
    'manifest:media-type="application/vnd.oasis.opendocument.text"/></manifest:manifest>'
)


def _odt_paragraph(rng: random.Random, number: int) -> str:
    words = _words(rng, rng.randint(40, 70)).split()
    for _ in range(3):
        at = rng.randrange(len(words))
        style = rng.choice(["T1", "T2"])
        words[at] = f'<text:span text:style-name="{style}">{words[at]}</text:span>'
    text = " ".join(words) + "."
    if number % 5 == 0:
        text += (
            '<text:note text:note-class="footnote"><text:note-body>'
            f"<text:p>{_words(rng, 8)}.</text:p></text:note-body></text:note>"
        )
    if number % 7 == 0:
        text += ' <draw:frame><draw:object xlink:href="./Object 1"/></draw:frame>'
    return f"<text:p>{text}</text:p>"


def _odt_block(rng: random.Random, number: int) -> str:
    if number % 2:
        items = "".join(
            f"<text:list-item><text:p>{_line(rng)}</text:p></text:list-item>" for _ in range(3)
        )
        return f'<text:list text:style-name="L1">{items}</text:list>'
    rows = "".join(
        "<table:table-row>"
        f"<table:table-cell><text:p>{_words(rng, 1)}</text:p></table:table-cell>"
        f"<table:table-cell><text:p>{rng.randint(1, 999)}</text:p></table:table-cell>"
        "</table:table-row>"
        for _ in range(4)
    )
    return f"<table:table>{rows}</table:table>"


def make_odt(path: Path, size: int, rng: random.Random) -> None:
    """An .odt whose content.xml holds about ``size`` bytes (the text parts are what costs)."""
    parts = [f'<?xml version="1.0" encoding="UTF-8"?><office:document-content {_ODF}>']
    parts.append(f"{_ODT_STYLES}<office:body><office:text>")
    written, number = sum(map(len, parts)), 0
    while written < size:
        number += 1
        piece = f'<text:h text:outline-level="1">{_words(rng, 3)}</text:h>'
        piece += "".join(_odt_paragraph(rng, number * 3 + n) for n in range(3))
        piece += _odt_block(rng, number)
        parts.append(piece)
        written += len(piece)
    parts.append("</office:text></office:body></office:document-content>")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.oasis.opendocument.text")
        archive.writestr("META-INF/manifest.xml", _ODT_MANIFEST, zipfile.ZIP_DEFLATED)
        archive.writestr("content.xml", "".join(parts), zipfile.ZIP_DEFLATED)
        archive.writestr("Object 1/content.xml", _ODT_FORMULA, zipfile.ZIP_DEFLATED)


def make_tex(path: Path, size: int, rng: random.Random) -> None:
    _tex(path, size, rng, macros=False)


def make_tex_macros(path: Path, size: int, rng: random.Random) -> None:
    _tex(path, size, rng, macros=True)


def _calibrated(
    build: Callable[[Path, int, random.Random], None],
    probe_units: int,
    path: Path,
    size: int,
    rng: random.Random,
) -> None:
    """For formats whose size is only known after saving: build small, scale up linearly."""
    build(path, probe_units, random.Random(SEED))
    units = max(1, round(probe_units * size / path.stat().st_size))
    build(path, units, rng)


def _xlsx(path: Path, rows: int, rng: random.Random) -> None:
    import openpyxl

    workbook = openpyxl.Workbook(write_only=True)
    sheet = workbook.create_sheet("Data")
    sheet.append(["id", "name", "value", "comment"])
    for row in range(rows):
        sheet.append([row, _words(rng, 2), rng.random() * 1000, _words(rng, 6)])
    workbook.save(path)


def _pptx(path: Path, slides: int, rng: random.Random) -> None:
    import pptx

    presentation = pptx.Presentation()
    layout = presentation.slide_layouts[1]
    for _ in range(slides):
        slide = presentation.slides.add_slide(layout)
        slide.shapes.title.text = _words(rng, 4)
        slide.placeholders[1].text = _words(rng, 250)
    presentation.save(str(path))


def make_xlsx(path: Path, size: int, rng: random.Random) -> None:
    _calibrated(_xlsx, 2000, path, size, rng)


def make_pptx(path: Path, size: int, rng: random.Random) -> None:
    _calibrated(_pptx, 20, path, size, rng)


@dataclass(frozen=True)
class Case:
    kind: str
    extension: str
    build: Callable[[Path, int, random.Random], None]
    sizes_mib: tuple[float, ...]
    engine: str = "markitdown"  # or "tex" / "odt" / "article": ClearMD's own (002, 003, 004)


CASES = [
    Case("txt", ".txt", make_txt, (1, 10, 50, 100)),
    Case("csv", ".csv", make_csv, (1, 10, 50, 100)),
    Case("html", ".html", make_html, (1, 10, 50)),
    Case("ipynb", ".ipynb", make_ipynb, (1, 10, 50)),
    Case("pdf", ".pdf", make_pdf, (1, 5, 20)),
    Case("docx_text", ".docx", make_docx_text, (1, 10, 50)),
    Case("docx_images", ".docx", make_docx_images, (10, 50, 100)),
    Case("epub", ".epub", make_epub, (1, 10, 50)),
    Case("pptx", ".pptx", make_pptx, (1, 10)),
    Case("xlsx", ".xlsx", make_xlsx, (1, 10, 50)),
    Case("tex", ".tex", make_tex, (1, 5, 10, 25), "tex"),
    Case("tex_macros", ".tex", make_tex_macros, (1, 5, 10, 25), "tex"),
    Case("odt", ".odt", make_odt, (1, 5, 10, 25), "odt"),
    Case("html_article", ".html", make_html_article, (1, 5, 10, 25), "article"),
]


# --- Measurement (child side) --------------------------------------------------------------------


def _peak_rss_mib() -> float:
    # ru_maxrss is in KiB on Linux.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _convert_with(engine: str, extension: str) -> Callable[[str], dict[str, Any]]:
    if engine == "article":
        from clearmd.backend.schemas.formats import FormatId
        from clearmd.backend.schemas.models import Detection, DetectionMethod
        from clearmd.backend.services.conversion.html import ArticleConverter

        article = ArticleConverter()
        page = Detection(FormatId.HTML, DetectionMethod.EXTENSION)

        def convert_article(path: str) -> dict[str, Any]:
            result = article.convert(Path(path), page, Path(path).with_suffix(".md"))
            notes = [note.kind.value for note in result.notes]
            return {"ok": True, "markdown_mib": len(result.markdown) / MIB, "notes": notes}

        return convert_article
    if engine == "odt":
        from clearmd.backend.schemas.formats import FormatId
        from clearmd.backend.schemas.models import Detection, DetectionMethod
        from clearmd.backend.services.conversion.odt import OdtConverter

        odt = OdtConverter()
        found = Detection(FormatId.ODT, DetectionMethod.EXTENSION)

        def convert_odt(path: str) -> dict[str, Any]:
            result = odt.convert(Path(path), found, Path(path).with_suffix(".md"))
            notes = [note.kind.value for note in result.notes]
            return {"ok": True, "markdown_mib": len(result.markdown) / MIB, "notes": notes}

        return convert_odt
    if engine == "tex":
        from clearmd.backend.schemas.formats import FormatId
        from clearmd.backend.schemas.models import Detection, DetectionMethod
        from clearmd.backend.services.conversion.tex import TexConverter

        tex = TexConverter()
        detection = Detection(FormatId.TEX, DetectionMethod.EXTENSION)

        def convert_tex(path: str) -> dict[str, Any]:
            result = tex.convert(Path(path), detection, Path(path).with_suffix(".md"))
            notes = [note.kind.value for note in result.notes]
            return {"ok": True, "markdown_mib": len(result.markdown) / MIB, "notes": notes}

        return convert_tex
    from markitdown import MarkItDown, StreamInfo

    markitdown = MarkItDown(enable_plugins=False)

    def convert_markitdown(path: str) -> dict[str, Any]:
        result = markitdown.convert_local(path, stream_info=StreamInfo(extension=extension))
        return {"ok": True, "markdown_mib": len(result.markdown) / MIB}

    return convert_markitdown


def _measure_child(connection: Connection, path: str, extension: str, engine: str) -> None:
    started = time.perf_counter()
    convert = _convert_with(engine, extension)
    ready = time.perf_counter() - started
    baseline = psutil.Process().memory_info().rss / MIB
    began = time.perf_counter()
    try:
        outcome = convert(path)
    except Exception as error:
        outcome = {"ok": False, "error": f"{type(error).__name__}: {str(error)[:200]}"}
    outcome.update(
        startup_s=ready,
        seconds=time.perf_counter() - began,
        baseline_mib=baseline,
        peak_mib=_peak_rss_mib(),
    )
    connection.send(outcome)


def _startup_child(connection: Connection) -> None:
    started = time.perf_counter()
    import magika
    from markitdown import MarkItDown

    MarkItDown(enable_plugins=False)
    ready = time.perf_counter() - started
    after_markitdown = psutil.Process().memory_info().rss / MIB
    magika.Magika()
    after_second_magika = psutil.Process().memory_info().rss / MIB
    connection.send(
        {
            "import_and_init_s": ready,
            "rss_after_markitdown_mib": after_markitdown,
            "second_magika_mib": after_second_magika - after_markitdown,
        }
    )


# --- Measurement (parent side) -------------------------------------------------------------------


def _run_child(
    target: Callable[..., None], args: tuple[Any, ...], *, memory_cap: int, timeout: float
) -> dict[str, Any]:
    context = multiprocessing.get_context("spawn")
    parent_end, child_end = context.Pipe()
    process = context.Process(target=target, args=(child_end, *args), daemon=True)
    started = time.perf_counter()
    process.start()
    child_end.close()
    sampled_peak = 0
    try:
        while True:
            if parent_end.poll(SAMPLE_SECONDS):
                result: dict[str, Any] = parent_end.recv()
                result["sampled_peak_mib"] = sampled_peak / MIB
                result["wall_s"] = time.perf_counter() - started
                return result
            try:
                rss = psutil.Process(process.pid).memory_info().rss
            except psutil.Error:
                rss = 0
            sampled_peak = max(sampled_peak, rss)
            if rss > memory_cap:
                return {"ok": False, "error": f"stopped above the {memory_cap // MIB} MiB cap"}
            if time.perf_counter() - started > timeout:
                return {"ok": False, "error": f"stopped after {timeout:g} s"}
            if not process.is_alive():
                return {"ok": False, "error": f"process exited with code {process.exitcode}"}
    finally:
        if process.is_alive():
            process.kill()
        process.join()


def zip_stats(path: Path) -> dict[str, float] | None:
    if not zipfile.is_zipfile(path):
        return None
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
    uncompressed = sum(info.file_size for info in infos)
    worst = max(
        (info.file_size / info.compress_size for info in infos if info.compress_size), default=0
    )
    return {
        "uncompressed_mib": uncompressed / MIB,
        "total_ratio": uncompressed / path.stat().st_size,
        "worst_entry_ratio": worst,
    }


@dataclass
class Row:
    kind: str
    size_mib: float
    file_mib: float
    result: dict[str, Any]
    archive: dict[str, float] | None


def run(
    cases: list[Case],
    workdir: Path,
    *,
    memory_cap: int,
    timeout: float,
    slow_after: float,
    log: Callable[[str], None] = print,
) -> list[Row]:
    rows: list[Row] = []
    for case in cases:
        rng = random.Random(SEED)
        for size_mib in case.sizes_mib:
            path = workdir / f"{case.kind}_{size_mib:g}{case.extension}"
            case.build(path, int(size_mib * MIB), rng)
            result = _run_child(
                _measure_child,
                (str(path), case.extension, case.engine),
                memory_cap=memory_cap,
                timeout=timeout,
            )
            row = Row(case.kind, size_mib, path.stat().st_size / MIB, result, zip_stats(path))
            rows.append(row)
            log(json.dumps(asdict(row)))
            path.unlink()
            if not result.get("ok") or result.get("seconds", 0) > slow_after:
                log(f"# {case.kind}: larger sizes skipped after {size_mib:g} MiB")
                break
    return rows


def startup(repetitions: int, *, memory_cap: int, timeout: float) -> dict[str, float]:
    runs = [
        _run_child(_startup_child, (), memory_cap=memory_cap, timeout=timeout)
        for _ in range(repetitions)
    ]
    return {key: statistics.median(run[key] for run in runs) for key in runs[0] if key != "error"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ClearMD benchmarks (features 001 and 002)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--memory-cap-mib", type=int, default=2048)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--slow-after", type=float, default=300)
    parser.add_argument("--only", nargs="*", help="kinds to run (default: all)")
    args = parser.parse_args(argv)
    cap = args.memory_cap_mib * MIB
    cases = [case for case in CASES if not args.only or case.kind in args.only]
    with tempfile.TemporaryDirectory(prefix="clearmd-bench-") as tmp:
        measured_startup = startup(3, memory_cap=cap, timeout=args.timeout)
        print(json.dumps({"startup": measured_startup}))
        rows = run(
            cases, Path(tmp), memory_cap=cap, timeout=args.timeout, slow_after=args.slow_after
        )
    machine = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cpus": psutil.cpu_count(),
        "ram_mib": psutil.virtual_memory().total // MIB,
        "memory_cap_mib": args.memory_cap_mib,
    }
    payload = {"machine": machine, "startup": measured_startup, "rows": [asdict(r) for r in rows]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
