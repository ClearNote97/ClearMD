"""The OpenDocument generator (feature 003)."""

import random
import zipfile
from pathlib import Path

from benchlib.common import _line, _words

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
