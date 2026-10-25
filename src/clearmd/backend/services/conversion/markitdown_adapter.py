"""markitdown behind ClearMD's converter contract (ADR-0004). Runs only inside the worker process.

The exception mapping was confirmed against the fixtures (T04): markitdown wraps a converter's
error in ``FileConversionException.attempts``; pdfminer raises ``PDFPasswordIncorrect`` for an
encrypted PDF and ``PDFSyntaxError`` for a broken one; a truncated docx raises ``BadZipFile``.
"""

import zipfile
from pathlib import Path
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError

from markitdown import (
    FileConversionException,
    MarkItDown,
    StreamInfo,
    UnsupportedFormatException,
)
from pdfminer.pdfdocument import PDFEncryptionError
from pdfminer.psexceptions import PSException

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import Detection

_CORRUPT: tuple[type[BaseException], ...] = (
    zipfile.BadZipFile,
    ParseError,
    ExpatError,
    PSException,
)
# lxml (used by python-pptx) is matched by name: it ships no type information.
_CORRUPT_BY_NAME = frozenset({"XMLSyntaxError"})


def _describe(error: BaseException) -> str:
    message = str(error).strip()
    return f"{type(error).__name__}: {message}" if message else type(error).__name__


def _code_for(error: BaseException) -> ErrorCode:
    if isinstance(error, PDFEncryptionError):
        return ErrorCode.PASSWORD_PROTECTED
    if isinstance(error, _CORRUPT) or type(error).__name__ in _CORRUPT_BY_NAME:
        return ErrorCode.CORRUPT_FILE
    if isinstance(error, PermissionError):
        return ErrorCode.PERMISSION_DENIED
    return ErrorCode.CONVERSION_FAILED


def map_exception(error: Exception) -> ConversionError:
    """The ClearMD error for anything markitdown (or the file system) raised."""
    if isinstance(error, UnsupportedFormatException):
        return ConversionError(ErrorCode.UNSUPPORTED_FORMAT, _describe(error))
    if isinstance(error, FileConversionException):
        causes = [attempt.exc_info[1] for attempt in error.attempts or [] if attempt.exc_info]
        for cause in causes:
            code = _code_for(cause)
            if code is not ErrorCode.CONVERSION_FAILED:
                return ConversionError(code, _describe(cause))
        detail = _describe(causes[0]) if causes else _describe(error)
        return ConversionError(ErrorCode.CONVERSION_FAILED, detail)
    return ConversionError(_code_for(error), _describe(error))


class MarkItDownConverter:
    """One ``MarkItDown`` per process, created on first use, plugins disabled (ADR-0005)."""

    def __init__(self) -> None:
        self._markitdown: MarkItDown | None = None

    def convert(self, source: Path, detection: Detection) -> str:
        if self._markitdown is None:
            self._markitdown = MarkItDown(enable_plugins=False)
        # The detected format is a hint, so extension-less files convert too.
        hint = StreamInfo(extension=f".{detection.format.value}")
        try:
            result = self._markitdown.convert_local(str(source), stream_info=hint)
        except Exception as error:
            raise map_exception(error) from error
        return result.markdown
