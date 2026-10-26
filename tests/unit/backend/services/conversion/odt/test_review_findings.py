"""Regressions for the security audit of feature 003 (S1–S9); each reproduces the reported input."""

import time
import zipfile
from pathlib import Path

import pytest
from build_fixtures import ODT_AUTOMATIC_STYLES, _odt_xml, odt_package
from support.markdown_guarantee import broken_promises

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.markdown_out import MARK
from clearmd.backend.services.conversion.odt import OdtConverter
from clearmd.backend.services.conversion.odt.xmltree import XmlLimits, XmlRefused, parse_part

MATH = 'xmlns="http://www.w3.org/1998/Math/MathML"'


def _file(tmp_path: Path, body: str, extra: dict[str, bytes] | None = None) -> Path:
    path = tmp_path / "s.odt"
    path.write_bytes(
        odt_package(_odt_xml("document-content", body, automatic=ODT_AUTOMATIC_STYLES), extra=extra)
    )
    return path


def _convert(path: Path) -> tuple[str, set[NoteKind]]:
    result = OdtConverter().convert(path, None, path.with_suffix(".md"))  # type: ignore[arg-type]
    return result.markdown, {note.kind for note in result.notes}


def _timed(path: Path, seconds: float) -> tuple[str, set[NoteKind]]:
    started = time.monotonic()
    found = _convert(path)
    assert time.monotonic() - started < seconds
    return found


def test_s1_nested_footnotes_are_linear(tmp_path: Path) -> None:
    inner = "x"
    for _ in range(40):
        inner = f"<text:p>a<text:note><text:note-body>{inner}</text:note-body></text:note></text:p>"
    markdown, _ = _timed(_file(tmp_path, inner), 5)
    assert markdown.count("\n[^") <= 41


def test_s2_one_formula_referenced_many_times_is_bounded(tmp_path: Path) -> None:
    formula = (
        f"<math {MATH}><semantics><mrow><mtext>{'\\' * 60_000}</mtext></mrow></semantics></math>"
    )
    frame = '<draw:frame><draw:object xlink:href="./Object 1"/></draw:frame>'
    body = "<text:p>" + ("x " + frame) * 1000 + "</text:p>"
    path = _file(tmp_path, body, {"Object 1/content.xml": formula.encode()})
    markdown, kinds = _timed(path, 20)
    assert len(markdown) < 8 * 1024**2
    assert NoteKind.FORMULA_KEPT_AS_SOURCE in kinds


def test_s3_table_repeats_are_bounded_in_cells_and_characters(tmp_path: Path) -> None:
    cell = (
        '<table:table-cell table:number-columns-repeated="64"><text:p>'
        + "a" * 10_000
        + "</text:p></table:table-cell>"
    )
    row = f'<table:table-row table:number-rows-repeated="64">{cell}</table:table-row>'
    markdown, kinds = _timed(_file(tmp_path, f"<table:table>{row}</table:table>"), 10)
    assert len(markdown) < 4 * 1024**2
    assert NoteKind.TABLE_SIMPLIFIED in kinds


def test_s4_a_long_formula_is_linear(tmp_path: Path) -> None:
    formula = f"<math {MATH}><mrow>{'<mi>α</mi>' * 40_000}</mrow></math>"
    body = '<text:p><draw:frame><draw:object xlink:href="./Object 1"/></draw:frame></text:p>'
    markdown, _ = _timed(_file(tmp_path, body, {"Object 1/content.xml": formula.encode()}), 5)
    assert markdown.count("\\alpha") == 40_000


def test_s5_nested_paragraphs_in_a_cell_are_written_once(tmp_path: Path) -> None:
    inner = "a" * 100_000
    for _ in range(250):
        inner = f"<text:p>{inner}</text:p>"
    table = f"<table:table><table:table-row><table:table-cell>{inner}</table:table-cell>"
    markdown, _ = _timed(_file(tmp_path, table + "</table:table-row></table:table>"), 10)
    assert markdown.count("a") < 200_000


@pytest.mark.parametrize(
    "body",
    [
        'a \\` <text:span text:style-name="T7">&lt;img src=x&gt;</text:span> b \\`',
        'x\\\\` <text:span text:style-name="T7">c</text:span>&lt;img src=x&gt;',
        "a \\| b",
    ],
)
def test_s6_a_backslash_in_the_text_never_cancels_an_escape(body: str, tmp_path: Path) -> None:
    markdown, _ = _convert(_file(tmp_path, f"<text:p>{body}</text:p>"))
    assert broken_promises(markdown) == []


def test_s6_a_backtick_in_math_is_never_a_code_delimiter(tmp_path: Path) -> None:
    formula = f"<math {MATH}><mrow><mi>x</mi><mo>`</mo><mi>y</mi></mrow></math>"
    body = (
        '<text:p>a <draw:frame><draw:object xlink:href="./Object 1"/></draw:frame> '
        '<text:span text:style-name="T7">&lt;img src=x&gt;</text:span> `</text:p>'
    )
    markdown, _ = _convert(_file(tmp_path, body, {"Object 1/content.xml": formula.encode()}))
    assert broken_promises(markdown) == []


def test_s7_the_block_mark_never_comes_from_the_document(tmp_path: Path) -> None:
    code = (
        f'<text:p text:style-name="P2">uno</text:p><text:p text:style-name="P2">{MARK}```</text:p>'
        '<text:p text:style-name="P2">&lt;img src=x&gt;</text:p>'
        f'<text:p>{MARK}# no <text:span text:style-name="T7">{MARK}x</text:span></text:p>'
    )
    markdown, _ = _convert(_file(tmp_path, code))
    assert MARK not in markdown and broken_promises(markdown) == []
    assert MARK not in parse_part(f'<p a="{MARK}">{MARK}</p>'.encode()).text()


def _mark_encrypted(path: Path, name: str) -> None:
    """Set the encryption bit of ``name`` as an encrypting ZIP tool does (zipfile clears it when
    writing): in its local header and in the central directory."""
    data = bytearray(path.read_bytes())
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo(name)
    data[info.header_offset + 6] |= 0x1  # local file header, general purpose flags
    encoded = name.encode()
    position = data.find(b"PK\x01\x02")
    while position != -1:
        length = int.from_bytes(data[position + 28 : position + 30], "little")
        if data[position + 46 : position + 46 + length] == encoded:
            data[position + 8] |= 0x1  # central directory header, general purpose flags
        position = data.find(b"PK\x01\x02", position + 4)
    path.write_bytes(bytes(data))


def test_s8_an_encrypted_zip_entry_is_password_protected(tmp_path: Path) -> None:
    path = _file(tmp_path, "<text:p>x</text:p>")
    _mark_encrypted(path, "content.xml")
    with zipfile.ZipFile(path) as archive:
        assert archive.getinfo("content.xml").flag_bits & 0x1
    with pytest.raises(ConversionError) as raised:
        _convert(path)
    assert raised.value.code is ErrorCode.PASSWORD_PROTECTED


def test_s9_attributes_count_toward_the_xml_limits() -> None:
    many = " ".join(f'a{n}="x"' for n in range(2000))
    with pytest.raises(XmlRefused):
        parse_part(f"<p {many}/>".encode(), XmlLimits(max_elements=1000))
    with pytest.raises(XmlRefused):
        parse_part(f'<p a="{"x" * 2000}"/>'.encode(), XmlLimits(max_characters=1000))
