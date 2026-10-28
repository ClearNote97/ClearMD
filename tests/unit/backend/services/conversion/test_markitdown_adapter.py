"""The real markitdown on every fixture (plan: "Adapter" tests), and the exception mapping."""

import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest
from build_fixtures import MARKERS
from markitdown import FileConversionException, UnsupportedFormatException
from markitdown._exceptions import FailedConversionAttempt
from support import DOCUMENTS_DIR, WINDOWS

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId, format_for_extension
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.markitdown_adapter import (
    MarkItDownConverter,
    map_exception,
)

CONVERTIBLE = sorted(name for name in MARKERS if name != "encrypted.pdf")


TARGET = Path("out.md")  # markitdown writes no links to other files


def _detection(name: str) -> Detection:
    if name == "docx_without_extension":
        return Detection(FormatId.DOCX, DetectionMethod.CONTENT)
    format_id = format_for_extension(Path(name).suffix)
    assert format_id is not None
    return Detection(format_id, DetectionMethod.EXTENSION)


@pytest.fixture(scope="module")
def converter() -> MarkItDownConverter:
    return MarkItDownConverter()


@pytest.mark.parametrize("name", CONVERTIBLE)
def test_every_fixture_converts_and_keeps_its_text(
    converter: MarkItDownConverter, name: str
) -> None:
    result = converter.convert(DOCUMENTS_DIR / name, _detection(name), TARGET)
    assert MARKERS[name] in result.markdown
    assert result.notes == ()  # markitdown reports no notes


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("encrypted.pdf", ErrorCode.PASSWORD_PROTECTED),
        ("corrupt.pdf", ErrorCode.CORRUPT_FILE),
        ("corrupt.docx", ErrorCode.CORRUPT_FILE),
    ],
)
def test_hard_fixtures_fail_with_their_code(
    converter: MarkItDownConverter, name: str, code: ErrorCode
) -> None:
    with pytest.raises(ConversionError) as raised:
        converter.convert(DOCUMENTS_DIR / name, _detection(name), TARGET)
    assert raised.value.code is code
    assert raised.value.detail  # the technical detail is kept for the summary


def test_only_the_converter_of_the_detected_format_runs(tmp_path: Path) -> None:
    """A zip renamed .pdf must fail as a PDF, never fall back to markitdown's ZipConverter."""
    import markitdown.converters._zip_converter as zip_module

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("ZipConverter must never run")

    original = zip_module.ZipConverter.convert
    zip_module.ZipConverter.convert = forbidden  # type: ignore[method-assign]
    try:
        fake = tmp_path / "invoice.pdf"
        with zipfile.ZipFile(fake, "w") as archive:
            archive.writestr("inner.txt", "x" * 1000)
        with pytest.raises(ConversionError) as raised:
            MarkItDownConverter().convert(
                fake, Detection(FormatId.PDF, DetectionMethod.EXTENSION), TARGET
            )
        assert raised.value.code is ErrorCode.CORRUPT_FILE
    finally:
        zip_module.ZipConverter.convert = original  # type: ignore[method-assign]


def test_no_image_audio_or_zip_converter_is_ever_registered() -> None:
    names = {type(c).__name__ for c in MarkItDownConverter().converters.values()}
    assert names.isdisjoint(
        {"ZipConverter", "ImageConverter", "AudioConverter", "OutlookMsgConverter"}
    )
    assert set(MarkItDownConverter().converters) == set(FormatId) - {FormatId.TEX, FormatId.ODT}


def test_a_source_replaced_by_a_symlink_is_not_followed(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("private key", encoding="utf-8")
    link = tmp_path / "notes.txt"
    link.symlink_to(secret)
    with pytest.raises(ConversionError) as raised:
        MarkItDownConverter().convert(
            link, Detection(FormatId.TXT, DetectionMethod.EXTENSION), TARGET
        )
    assert raised.value.code is ErrorCode.SOURCE_UNREADABLE


@pytest.mark.skipif(WINDOWS, reason="chmod cannot make a file unreadable on Windows")
def test_a_source_that_cannot_be_read_is_source_unreadable(tmp_path: Path) -> None:
    locked = tmp_path / "locked.txt"
    locked.write_text("x", encoding="utf-8")
    locked.chmod(0)
    try:
        with pytest.raises(ConversionError) as raised:
            MarkItDownConverter().convert(
                locked, Detection(FormatId.TXT, DetectionMethod.EXTENSION), TARGET
            )
    finally:
        locked.chmod(0o644)
    assert raised.value.code is ErrorCode.SOURCE_UNREADABLE


def _fce(error: BaseException) -> FileConversionException:
    attempt = FailedConversionAttempt(converter=object(), exc_info=(type(error), error, None))
    return FileConversionException(attempts=[attempt])


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (UnsupportedFormatException("no converter"), ErrorCode.UNSUPPORTED_FORMAT),
        (PermissionError(13, "Permission denied"), ErrorCode.SOURCE_UNREADABLE),
        (_fce(zipfile.BadZipFile("File is not a zip file")), ErrorCode.CORRUPT_FILE),
        (_fce(RuntimeError("something else")), ErrorCode.CONVERSION_FAILED),
        (FileConversionException(), ErrorCode.CONVERSION_FAILED),
        (RuntimeError("unexpected"), ErrorCode.CONVERSION_FAILED),
    ],
)
def test_exception_mapping(error: Exception, code: ErrorCode) -> None:
    mapped = map_exception(error)
    assert mapped.code is code
    assert mapped.detail


def test_detail_names_the_underlying_exception() -> None:
    mapped = map_exception(_fce(zipfile.BadZipFile("File is not a zip file")))
    assert mapped.detail == "BadZipFile: File is not a zip file"


def test_importing_the_adapter_is_what_loads_markitdown() -> None:
    # The CLI process must never import this module (AC-19); the worker does.
    assert "markitdown" in sys.modules


def test_detail_of_a_raw_converter_error() -> None:
    mapped = map_exception(zipfile.BadZipFile("File is not a zip file"))
    assert (mapped.code, mapped.detail) == (
        ErrorCode.CORRUPT_FILE,
        "BadZipFile: File is not a zip file",
    )
