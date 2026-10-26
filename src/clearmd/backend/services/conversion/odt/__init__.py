"""ClearMD's own OpenDocument text converter (feature 003, ADR-0006, ADR-0024): stdlib only."""

from pathlib import Path

from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.odt.package import OdtPackage
from clearmd.backend.services.conversion.odt.render import OdtRenderer
from clearmd.backend.services.conversion.odt.styles import Styles


class OdtConverter:
    """Archive → parts → styles → render; images and formulas join in T06 and T07."""

    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        with OdtPackage.open(source) as package:
            content = package.content()
            renderer = OdtRenderer(Styles(content, package.styles()))
            markdown = renderer.document(content)
        return ConversionResult(markdown, renderer.notes())
