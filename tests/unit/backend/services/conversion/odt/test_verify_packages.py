"""Feature 003 verification (N1-N21): charts, encodings and damaged packages.

Regressions, each from its reported input."""

from pathlib import Path

import pytest
from builders.odt_package import _odt_styles
from support.odt_verify import MATH, MIME, content, convert_bytes, manifest, manual_zip, md

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.xmltree import XmlLimits, XmlRefused, parse_part


def test_n14_a_missing_or_huge_chart_is_an_image_never_a_formula(tmp_path: Path) -> None:
    frame = (
        '<text:p><draw:frame draw:name="Chart1"><draw:object xlink:href="./Object 1"/>'
        "</draw:frame></text:p>"
    )
    entry = (
        '<manifest:file-entry manifest:full-path="Object 1/" '
        'manifest:media-type="application/vnd.oasis.opendocument.chart"/>'
    )
    data = manual_zip(
        [MIME, ("META-INF/manifest.xml", manifest(entry)), ("content.xml", content(frame)),
         ("styles.xml", _odt_styles())]
    )  # fmt: skip
    markdown, kinds = convert_bytes(tmp_path, data)
    assert "*Image: Chart1*" in markdown and NoteKind.FORMULA_KEPT_AS_SOURCE not in kinds


@pytest.mark.parametrize("encoding", ["Shift_JIS", "UTF-7", "rot13", "no-such-encoding"])
def test_n9_an_xml_part_in_an_encoding_odf_does_not_allow_is_refused(encoding: str) -> None:
    with pytest.raises(XmlRefused):
        parse_part(f'<?xml version="1.0" encoding="{encoding}"?><p>x</p>'.encode())


def test_n9_one_formula_in_a_strange_encoding_never_fails_the_document(tmp_path: Path) -> None:
    formula = f'<?xml version="1.0" encoding="Shift_JIS"?><math {MATH}><mi>x</mi></math>'
    frame = '<draw:frame><draw:object xlink:href="./Object 1"/></draw:frame>'
    markdown = md(
        tmp_path, f"<text:p>a {frame}</text:p>", {"Object 1/content.xml": formula.encode()}
    )
    assert markdown.startswith("a")


@pytest.mark.filterwarnings("ignore:Duplicate name")
def test_n16_an_archive_with_a_name_twice_is_damaged(tmp_path: Path) -> None:
    good = content("<text:p>good</text:p>")
    data = manual_zip(
        [MIME, ("META-INF/manifest.xml", manifest("")), ("content.xml", good),
         ("content.xml", content("<text:p>EVIL</text:p>")), ("styles.xml", _odt_styles())]
    )  # fmt: skip
    with pytest.raises(ConversionError) as raised:
        convert_bytes(tmp_path, data)
    assert raised.value.code is ErrorCode.CORRUPT_FILE


@pytest.mark.parametrize("path", ["./content.xml", "/content.xml"])
def test_n17_encryption_declared_with_another_spelling_is_still_a_password(
    path: str, tmp_path: Path
) -> None:
    entry = (
        f'<manifest:file-entry manifest:full-path="{path}" manifest:media-type="text/xml">'
        "<manifest:encryption-data/></manifest:file-entry>"
    )
    data = manual_zip(
        [MIME, ("META-INF/manifest.xml", manifest(entry)), ("content.xml", content("<text:p/>")),
         ("styles.xml", _odt_styles())]
    )  # fmt: skip
    with pytest.raises(ConversionError) as raised:
        convert_bytes(tmp_path, data)
    assert raised.value.code is ErrorCode.PASSWORD_PROTECTED


def test_n20_names_and_namespace_declarations_count_toward_the_limits() -> None:
    with pytest.raises(XmlRefused):
        parse_part(f"<{'a' * 2000}/>".encode(), XmlLimits(max_characters=1000))
    declarations = " ".join(f'xmlns:n{index}="u{index}"' for index in range(2000))
    with pytest.raises(XmlRefused):
        parse_part(f"<p {declarations}/>".encode(), XmlLimits(max_elements=1000))


def test_n21_a_huge_mimetype_is_never_read(tmp_path: Path) -> None:
    data = manual_zip([("mimetype", b"application/vnd.oasis.opendocument.text" + b" " * 4096)])
    with pytest.raises(ConversionError) as raised:
        convert_bytes(tmp_path, data)
    assert raised.value.code is ErrorCode.CORRUPT_FILE and "larger" in str(raised.value)
