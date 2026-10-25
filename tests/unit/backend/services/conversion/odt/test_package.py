"""The .odt package: its type, encryption, parts and object references (ADR-0024, AC-04, AC-19)."""

import zipfile
from pathlib import Path

import pytest
from support import ODT_DIR

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.services.conversion.odt.package import OdtPackage, object_part


def _code(name: str) -> ErrorCode:
    with pytest.raises(ConversionError) as raised, OdtPackage.open(ODT_DIR / name):
        pass
    return raised.value.code


def test_a_text_document_opens_and_gives_its_parts() -> None:
    with OdtPackage.open(ODT_DIR / "report.odt") as package:
        assert package.content().tag == "office:document-content"
        styles = package.styles()
        assert styles is not None and styles.tag == "office:document-styles"


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("spreadsheet.odt", ErrorCode.UNSUPPORTED_FORMAT),
        ("encrypted.odt", ErrorCode.PASSWORD_PROTECTED),
        ("damaged.odt", ErrorCode.CORRUPT_FILE),
        ("hostile/doctype.odt", ErrorCode.CORRUPT_FILE),
        ("hostile/entities.odt", ErrorCode.CORRUPT_FILE),
    ],
)
def test_what_cannot_be_read_says_why(name: str, code: ErrorCode) -> None:
    def read() -> None:
        with OdtPackage.open(ODT_DIR / name) as package:
            package.content()

    with pytest.raises(ConversionError) as raised:
        read()
    assert raised.value.code is code


def test_deep_nesting_in_the_content_is_damaged_not_a_crash() -> None:
    with (
        OdtPackage.open(ODT_DIR / "hostile" / "deep.odt") as package,
        pytest.raises(ConversionError) as raised,
    ):
        package.content()
    assert raised.value.code is ErrorCode.CORRUPT_FILE


def test_without_a_mimetype_it_is_damaged(tmp_path: Path) -> None:
    path = tmp_path / "x.odt"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", "<x/>")
    with pytest.raises(ConversionError) as raised, OdtPackage.open(path):
        pass
    assert raised.value.code is ErrorCode.CORRUPT_FILE


def test_a_part_over_its_size_cap_is_refused() -> None:
    def read() -> None:  # the manifest is over 100 bytes already: refused while opening
        with OdtPackage.open(ODT_DIR / "report.odt", max_part_bytes=100) as package:
            package.content()

    with pytest.raises(ConversionError) as raised:
        read()
    assert raised.value.code is ErrorCode.CORRUPT_FILE


def test_a_link_instead_of_the_file_is_never_followed(tmp_path: Path) -> None:
    link = tmp_path / "linked.odt"
    link.symlink_to(ODT_DIR / "report.odt")
    with pytest.raises(ConversionError) as raised, OdtPackage.open(link):
        pass
    assert raised.value.code is ErrorCode.SOURCE_UNREADABLE


@pytest.mark.parametrize(
    ("href", "part"),
    [
        ("./Object 1", "Object 1/content.xml"),
        ("Object 2", "Object 2/content.xml"),
        ("./Object 1/", "Object 1/content.xml"),
        ("../escape", None),
        ("/etc/passwd", None),
        ("http://evil.example/o", None),
        ("C:/x", None),
        ("Object 1/../../x", None),
        ("", None),
    ],
)
def test_object_references_stay_inside_the_archive(href: str, part: str | None) -> None:
    assert object_part(href) == part


def test_a_missing_object_part_reads_as_nothing() -> None:
    with OdtPackage.open(ODT_DIR / "formulas.odt") as package:
        assert package.part("Object 9/content.xml") is None
        found = package.part("Object 1/content.xml")
        assert found is not None and found.tag == "math:math"


def test_the_package_is_closed_after_use() -> None:
    with OdtPackage.open(ODT_DIR / "report.odt") as package:
        pass
    with pytest.raises(ValueError):
        package.content()
