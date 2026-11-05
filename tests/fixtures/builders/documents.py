"""The presentation, spreadsheet, e-book and plain-text fixtures, and ``build`` for them all."""

import io
import json
from collections.abc import Callable
from pathlib import Path

import openpyxl
import pptx

from builders.common import MARKERS, _normalize_office_zip, _write_zip
from builders.docx import minimal_docx, zip_bomb_docx
from builders.pdf import encrypted_pdf, minimal_pdf


def minimal_pptx() -> bytes:
    presentation = pptx.Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "ClearMD fixture"
    slide.placeholders[1].text = f"Text from a PPTX slide: {MARKERS['sample.pptx']}"
    buffer = io.BytesIO()
    presentation.save(buffer)
    return _normalize_office_zip(buffer.getvalue())


def minimal_xlsx() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Data"
    sheet.append(["Name", "Value"])
    sheet.append([MARKERS["sample.xlsx"], 1])
    sheet.append(["second row", 2])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return _normalize_office_zip(buffer.getvalue())


def minimal_epub() -> bytes:
    container = (
        '<?xml version="1.0"?>'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/>'
        "</rootfiles></container>"
    )
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:identifier id="id">clearmd-fixture</dc:identifier><dc:title>ClearMD fixture</dc:title>'
        "<dc:creator>ClearMD</dc:creator><dc:language>en</dc:language></metadata>"
        '<manifest><item id="chapter1" href="chapter1.xhtml" '
        'media-type="application/xhtml+xml"/></manifest>'
        '<spine><itemref idref="chapter1"/></spine></package>'
    )
    chapter = (
        '<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml">'
        "<head><title>Chapter 1</title></head><body><h1>Chapter 1</h1>"
        f"<p>Text from an EPUB chapter: {MARKERS['sample.epub']}</p></body></html>"
    )
    return _write_zip(
        [
            ("mimetype", b"application/epub+zip"),
            ("META-INF/container.xml", container.encode()),
            ("OEBPS/content.opf", opf.encode()),
            ("OEBPS/chapter1.xhtml", chapter.encode()),
        ],
        stored=frozenset({"mimetype"}),
    )


def minimal_html() -> bytes:
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>ClearMD fixture</title></head>'
        "<body><h1>ClearMD fixture</h1>"
        f"<p>Text from an HTML page: {MARKERS['sample.html']}</p></body></html>\n"
    ).encode()


def minimal_csv() -> bytes:
    return f"name,value\n{MARKERS['sample.csv']},1\nsecond row,2\n".encode()


def minimal_txt() -> bytes:
    return f"Text from a plain-text file: {MARKERS['sample.txt']}\n".encode()


def minimal_ipynb() -> bytes:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# ClearMD fixture\n", MARKERS["sample.ipynb"]],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["1 + 1"],
            },
        ],
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return (json.dumps(notebook, indent=1) + "\n").encode()


def build(destination: Path) -> dict[str, Path]:
    """Write every fixture into ``destination`` and return them by name."""
    pdf = minimal_pdf(["ClearMD fixture", f"Text from a PDF document: {MARKERS['sample.pdf']}"])
    docx = minimal_docx()
    builders: dict[str, Callable[[], bytes]] = {
        "sample.pdf": lambda: pdf,
        "encrypted.pdf": lambda: encrypted_pdf(pdf),
        # A PDF header followed by garbage: no objects, no trailer.
        "corrupt.pdf": lambda: b"%PDF-1.4\n" + b"\x00garbage\x00" * 64,
        "sample.docx": lambda: docx,
        "docx_without_extension": lambda: docx,
        # The first half of a valid docx: its ZIP central directory is missing.
        "corrupt.docx": lambda: docx[: len(docx) // 2],
        "zip_bomb.docx": zip_bomb_docx,
        "sample.pptx": minimal_pptx,
        "sample.xlsx": minimal_xlsx,
        "sample.epub": minimal_epub,
        "sample.html": minimal_html,
        "sample.csv": minimal_csv,
        "sample.txt": minimal_txt,
        "sample.ipynb": minimal_ipynb,
    }
    destination.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, make in builders.items():
        path = destination / name
        path.write_bytes(make())
        written[name] = path
    return written
