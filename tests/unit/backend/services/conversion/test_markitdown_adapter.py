"""The real markitdown on every fixture (plan: "Adapter" tests), and the exception mapping."""

import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest
from build_fixtures import MARKERS
from markitdown import FileConversionException, UnsupportedFormatException
from markitdown._exceptions import FailedConversionAttempt
from support import DOCUMENTS_DIR

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId, format_for_extension
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion import markitdown_adapter
from clearmd.backend.services.conversion.markitdown_adapter import (
    MarkItDownConverter,
    map_exception,
)

CONVERTIBLE = sorted(name for name in MARKERS if name != "encrypted.pdf")


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
    markdown = converter.convert(DOCUMENTS_DIR / name, _detection(name))
    assert MARKERS[name] in markdown


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
        converter.convert(DOCUMENTS_DIR / name, _detection(name))
    assert raised.value.code is code
    assert raised.value.detail  # the technical detail is kept for the summary


def test_markitdown_is_created_once_and_without_plugins(monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[dict[str, Any]] = []

    class FakeMarkItDown:
        def __init__(self, **kwargs: Any) -> None:
            created.append(kwargs)

        def convert_local(self, path: str, **kwargs: Any) -> Any:
            return type("Result", (), {"markdown": "# ok"})()

    monkeypatch.setattr(markitdown_adapter, "MarkItDown", FakeMarkItDown)
    converter = MarkItDownConverter()
    detection = Detection(FormatId.TXT, DetectionMethod.EXTENSION)
    assert converter.convert(DOCUMENTS_DIR / "sample.txt", detection) == "# ok"
    converter.convert(DOCUMENTS_DIR / "sample.txt", detection)
    assert created == [{"enable_plugins": False}]


def _fce(error: BaseException) -> FileConversionException:
    attempt = FailedConversionAttempt(converter=object(), exc_info=(type(error), error, None))
    return FileConversionException(attempts=[attempt])


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (UnsupportedFormatException("no converter"), ErrorCode.UNSUPPORTED_FORMAT),
        (PermissionError(13, "Permission denied"), ErrorCode.PERMISSION_DENIED),
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
