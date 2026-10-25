"""markitdown's converters behind ClearMD's converter contract (ADR-0004). Worker process only.

Only the converter of the detected format runs, called directly on a stream ClearMD opened itself:
``MarkItDown`` is not used, because when a converter fails it falls back to every built-in one —
a zip renamed ``.pdf`` would reach its ZipConverter (bypassing the zip-bomb check of ADR-0015) and
an image would run exiftool (security review of feature 001).

The exception mapping was confirmed against the fixtures (T04): pdfminer raises
``PDFPasswordIncorrect`` for an encrypted PDF and ``PDFSyntaxError`` for a broken one; a truncated
docx raises ``BadZipFile``.
"""

import os
import stat
import zipfile
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import BinaryIO
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError

from markitdown import DocumentConverter, StreamInfo, UnsupportedFormatException
from markitdown.converters import (
    CsvConverter,
    DocxConverter,
    EpubConverter,
    HtmlConverter,
    IpynbConverter,
    PdfConverter,
    PlainTextConverter,
    PptxConverter,
    XlsxConverter,
)
from pdfminer.pdfdocument import PDFEncryptionError
from pdfminer.psexceptions import PSException

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection

_CORRUPT: tuple[type[BaseException], ...] = (
    zipfile.BadZipFile,
    ParseError,
    ExpatError,
    PSException,
)
# lxml (used by python-pptx) is matched by name: it ships no type information.
_CORRUPT_BY_NAME = frozenset({"XMLSyntaxError"})
_NO_FOLLOW = getattr(os, "O_NOFOLLOW", 0)
_BINARY = getattr(os, "O_BINARY", 0)


def _describe(error: BaseException) -> str:
    message = str(error).strip()
    return f"{type(error).__name__}: {message}" if message else type(error).__name__


def _code_for(error: BaseException) -> ErrorCode:
    if isinstance(error, MemoryError):
        return ErrorCode.OUT_OF_MEMORY
    if isinstance(error, PDFEncryptionError):
        return ErrorCode.PASSWORD_PROTECTED
    if isinstance(error, _CORRUPT) or type(error).__name__ in _CORRUPT_BY_NAME:
        return ErrorCode.CORRUPT_FILE
    if isinstance(error, PermissionError):
        return ErrorCode.SOURCE_UNREADABLE
    return ErrorCode.CONVERSION_FAILED


def map_exception(error: Exception) -> ConversionError:
    """The ClearMD error for anything a converter (or the file system) raised."""
    if isinstance(error, UnsupportedFormatException):
        return ConversionError(ErrorCode.UNSUPPORTED_FORMAT, _describe(error))
    attempts = getattr(error, "attempts", None)  # markitdown's FileConversionException
    if attempts is not None or type(error).__name__ == "FileConversionException":
        causes = [attempt.exc_info[1] for attempt in attempts or [] if attempt.exc_info]
        for cause in causes:
            code = _code_for(cause)
            if code is not ErrorCode.CONVERSION_FAILED:
                return ConversionError(code, _describe(cause))
        detail = _describe(causes[0]) if causes else _describe(error)
        return ConversionError(ErrorCode.CONVERSION_FAILED, detail)
    return ConversionError(_code_for(error), _describe(error))


def _open_regular_file(source: Path) -> BinaryIO:
    """Open without following a symlink (where the OS allows it) and only if it is a file."""
    try:
        descriptor = os.open(source, os.O_RDONLY | _NO_FOLLOW | _BINARY)
    except OSError as error:
        raise ConversionError(ErrorCode.SOURCE_UNREADABLE, _describe(error)) from error
    if not stat.S_ISREG(os.fstat(descriptor).st_mode) or source.is_symlink():
        os.close(descriptor)
        raise ConversionError(ErrorCode.SOURCE_UNREADABLE, "not a regular file")
    return os.fdopen(descriptor, "rb")


def _converters() -> Mapping[FormatId, DocumentConverter]:
    # Some of markitdown's converters have untyped constructors.
    return MappingProxyType(
        {
            FormatId.PDF: PdfConverter(),
            FormatId.DOCX: DocxConverter(),  # type: ignore[no-untyped-call]
            FormatId.PPTX: PptxConverter(),  # type: ignore[no-untyped-call]
            FormatId.XLSX: XlsxConverter(),  # type: ignore[no-untyped-call]
            FormatId.HTML: HtmlConverter(),
            FormatId.CSV: CsvConverter(),  # type: ignore[no-untyped-call]
            FormatId.EPUB: EpubConverter(),  # type: ignore[no-untyped-call]
            FormatId.IPYNB: IpynbConverter(),
            FormatId.TXT: PlainTextConverter(),
        }
    )


class MarkItDownConverter:
    """markitdown's converter for the detected format, and nothing else."""

    def __init__(self) -> None:
        self.converters = _converters()

    def convert(self, source: Path, detection: Detection) -> ConversionResult:
        converter = self.converters[detection.format]
        hint = StreamInfo(extension=f".{detection.format.value}", filename=source.name)
        with _open_regular_file(source) as stream:
            try:
                result = converter.convert(stream, hint)
            except Exception as error:
                raise map_exception(error) from error
        return ConversionResult(result.markdown)  # markitdown reports nothing it skipped
