"""The ZIP check reads only the central directory (AC-09, ADR-0015)."""

import zipfile
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR

from clearmd.backend.schemas.limits import MIB, Limits
from clearmd.backend.use_cases.archive import inspect_archive, is_unsafe


def test_a_normal_docx_is_safe() -> None:
    info = inspect_archive(DOCUMENTS_DIR / "sample.docx")
    assert info is not None
    assert 1 < info.ratio < 10
    assert not is_unsafe(info, Limits())


def test_the_zip_bomb_is_unsafe_by_ratio() -> None:
    info = inspect_archive(DOCUMENTS_DIR / "zip_bomb.docx")
    assert info is not None
    assert info.ratio > 100
    assert is_unsafe(info, Limits())


def test_too_much_uncompressed_data_is_unsafe_even_with_a_low_ratio() -> None:
    info = inspect_archive(DOCUMENTS_DIR / "zip_bomb.docx")
    assert info is not None
    assert is_unsafe(info, Limits(max_ratio=10_000, max_uncompressed=1 * MIB))


def test_an_unreadable_archive_is_left_to_the_converter() -> None:
    assert inspect_archive(DOCUMENTS_DIR / "corrupt.docx") is None
    assert inspect_archive(DOCUMENTS_DIR / "sample.pdf") is None


def test_nothing_is_decompressed(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("the archive check must not decompress any entry")

    monkeypatch.setattr(zipfile.ZipFile, "open", forbidden)
    monkeypatch.setattr(zipfile.ZipFile, "read", forbidden)
    info = inspect_archive(DOCUMENTS_DIR / "zip_bomb.docx")
    assert info is not None and info.uncompressed >= 20 * MIB


def test_text_size_counts_xml_parts_and_ignores_images(tmp_path: Path) -> None:
    path = tmp_path / "photos.docx"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", "<w:document>" + "x" * 1000 + "</w:document>")
        archive.writestr("word/_rels/document.xml.rels", "<Relationships/>")
        archive.writestr(zipfile.ZipInfo("word/media/image1.png"), b"\x89PNG" + b"\x00" * 50_000)
    info = inspect_archive(path)
    assert info is not None
    assert info.text_bytes == 1025 + len("<Relationships/>")
    assert info.uncompressed > 50_000
