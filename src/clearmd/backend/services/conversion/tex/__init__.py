"""ClearMD's own LaTeX converter (feature 002, ADR-0006, ADR-0022). Worker process only."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import ConversionResult, Detection


class TexConverter:
    """Read → collect the author's macros → parse → render, following includes (plan of 002)."""

    def convert(self, source: Path, detection: Detection) -> ConversionResult:
        raise ConversionError(ErrorCode.CONVERSION_FAILED, "the .tex converter arrives in T04-T05")
