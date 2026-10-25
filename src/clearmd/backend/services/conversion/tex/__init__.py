"""ClearMD's own LaTeX converter (feature 002, ADR-0006, ADR-0022). Worker process only."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.tex.document import convert_document


class TexConverter:
    """A document with its includes and the author's macros; image links start at ``target``."""

    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        try:
            return convert_document(source, target)
        except OSError as error:
            detail = f"{type(error).__name__}: {error}"
            raise ConversionError(ErrorCode.SOURCE_UNREADABLE, detail) from error
