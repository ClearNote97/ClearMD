"""The committed fixtures exist, are reproducible and have the properties the tests rely on."""

import io
import zipfile
from pathlib import Path

import pytest
from build_fixtures import (
    BOMB_UNCOMPRESSED_BYTES,
    DOCUMENTS_DIR,
    FIXED_ZIP_TIME,
    MARKERS,
    NON_DETERMINISTIC,
    ODT_DIR,
    ODT_MIME,
    PDF_PASSWORD,
    TEX_DIR,
    build,
    build_odt,
    build_tex,
)
from pypdf import PdfReader

ZIP_BASED = ["sample.docx", "sample.pptx", "sample.xlsx", "sample.epub", "zip_bomb.docx"]


@pytest.fixture(scope="module")
def rebuilt(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return build(tmp_path_factory.mktemp("fixtures"))


def test_every_fixture_is_committed(rebuilt: dict[str, Path]) -> None:
    missing = [name for name in rebuilt if not (DOCUMENTS_DIR / name).is_file()]
    assert missing == []


def test_rebuilding_gives_the_committed_bytes(rebuilt: dict[str, Path]) -> None:
    changed = [
        name
        for name, path in rebuilt.items()
        if name not in NON_DETERMINISTIC
        and path.read_bytes() != (DOCUMENTS_DIR / name).read_bytes()
    ]
    assert changed == []


def test_every_marker_belongs_to_a_fixture(rebuilt: dict[str, Path]) -> None:
    assert set(MARKERS) <= set(rebuilt)


@pytest.mark.parametrize("name", ZIP_BASED)
def test_zip_entries_have_fixed_timestamps(name: str) -> None:
    with zipfile.ZipFile(DOCUMENTS_DIR / name) as archive:
        assert {info.date_time for info in archive.infolist()} == {FIXED_ZIP_TIME}


def test_pdf_holds_its_marker() -> None:
    reader = PdfReader(DOCUMENTS_DIR / "sample.pdf")
    assert MARKERS["sample.pdf"] in reader.pages[0].extract_text()


def test_encrypted_pdf_needs_the_password() -> None:
    reader = PdfReader(DOCUMENTS_DIR / "encrypted.pdf")
    assert reader.is_encrypted
    reader.decrypt(PDF_PASSWORD)
    assert MARKERS["encrypted.pdf"] in reader.pages[0].extract_text()


def test_corrupt_pdf_has_a_header_and_no_structure() -> None:
    data = (DOCUMENTS_DIR / "corrupt.pdf").read_bytes()
    assert data.startswith(b"%PDF-")
    assert b"xref" not in data
    assert b"%%EOF" not in data


def test_corrupt_docx_is_not_a_readable_zip() -> None:
    with pytest.raises(zipfile.BadZipFile):
        zipfile.ZipFile(io.BytesIO((DOCUMENTS_DIR / "corrupt.docx").read_bytes()))


def test_docx_without_extension_is_the_sample_docx() -> None:
    assert (DOCUMENTS_DIR / "docx_without_extension").read_bytes() == (
        DOCUMENTS_DIR / "sample.docx"
    ).read_bytes()


def test_zip_bomb_is_small_on_disk_and_huge_inside() -> None:
    path = DOCUMENTS_DIR / "zip_bomb.docx"
    with zipfile.ZipFile(path) as archive:
        uncompressed = sum(info.file_size for info in archive.infolist())
    assert uncompressed >= BOMB_UNCOMPRESSED_BYTES * 0.99
    assert path.stat().st_size < 100 * 1024
    assert uncompressed / path.stat().st_size > 100


def test_epub_starts_with_a_stored_mimetype() -> None:
    with zipfile.ZipFile(DOCUMENTS_DIR / "sample.epub") as archive:
        first = archive.infolist()[0]
        assert first.filename == "mimetype"
        assert first.compress_type == zipfile.ZIP_STORED


def test_the_latex_fixtures_are_committed_and_reproducible(tmp_path: Path) -> None:
    rebuilt = build_tex(tmp_path)
    changed = [
        name for name, path in rebuilt.items() if path.read_bytes() != (TEX_DIR / name).read_bytes()
    ]
    assert changed == []


def test_the_latin1_fixtures_are_not_utf8() -> None:
    for name in ("latin1.tex", "latin1_undeclared.tex"):
        with pytest.raises(UnicodeDecodeError):
            (TEX_DIR / name).read_bytes().decode("utf-8")


def test_the_exponential_macro_fixture_doubles_forty_times() -> None:
    text = (TEX_DIR / "hostile" / "exponential_macro.tex").read_text(encoding="utf-8")
    assert text.count("\\def") == 41
    assert "\\def\\bombaa{\\bombab\\bombab}" in text


@pytest.fixture(scope="module")
def rebuilt_odt(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return build_odt(tmp_path_factory.mktemp("odt"))


def test_the_odt_fixtures_are_committed_and_reproducible(rebuilt_odt: dict[str, Path]) -> None:
    changed = [
        name
        for name, path in rebuilt_odt.items()
        if not (ODT_DIR / name).is_file() or path.read_bytes() != (ODT_DIR / name).read_bytes()
    ]
    assert changed == []


@pytest.mark.parametrize("name", ["report.odt", "formulas.odt", "images.odt", "real/report.odt"])
def test_an_odt_starts_with_its_stored_mimetype(name: str) -> None:
    with zipfile.ZipFile(ODT_DIR / name) as archive:
        first = archive.infolist()[0]
        assert first.filename == "mimetype" and first.compress_type == zipfile.ZIP_STORED
        assert archive.read(first) == ODT_MIME.encode()


def test_the_real_odt_was_written_by_libreoffice() -> None:
    with zipfile.ZipFile(ODT_DIR / "real" / "report.odt") as archive:
        meta = archive.read("meta.xml").decode("utf-8")
        formulas = [name for name in archive.namelist() if name.endswith("/content.xml")]
        pictures = [name for name in archive.namelist() if name.startswith("Pictures/")]
    assert "LibreOffice" in meta
    assert len(formulas) == 5 and len(pictures) == 1


def test_the_hostile_odt_fixtures_are_what_they_claim() -> None:
    def content(name: str) -> bytes:
        with zipfile.ZipFile(ODT_DIR / "hostile" / name) as archive:
            return archive.read("content.xml")

    assert b"<!DOCTYPE" in content("doctype.odt")
    assert content("entities.odt").count(b"<!ENTITY") == 10
    assert content("deep.odt").count(b"<text:span>") == 20_000
    with zipfile.ZipFile(ODT_DIR / "hostile" / "bomb.odt") as archive:
        info = archive.getinfo("content.xml")
        assert info.file_size / info.compress_size > 100
