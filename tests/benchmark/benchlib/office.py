"""Generators of the Office and e-book formats: docx, epub, xlsx and pptx."""

import random
import zipfile
from pathlib import Path

from benchlib.common import MIB, _calibrated, _words, _zip_size

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
