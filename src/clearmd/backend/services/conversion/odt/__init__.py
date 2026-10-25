"""ClearMD's own OpenDocument text converter (feature 003, ADR-0006, ADR-0024): stdlib only."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import ConversionResult, Detection


class OdtConverter:
    """Archive → parts → styles → render (built in feature 003, T04–T07)."""

    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        raise ConversionError(ErrorCode.CONVERSION_FAILED, "the .odt converter is not built yet")
