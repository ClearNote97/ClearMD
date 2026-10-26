"""ClearMD's own OpenDocument text converter (feature 003, ADR-0006, ADR-0024): stdlib only."""

from pathlib import Path

from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.odt.package import OdtPackage
from clearmd.backend.services.conversion.odt.render import OdtRenderer
from clearmd.backend.services.conversion.odt.styles import Styles


def _meta_language(package: OdtPackage) -> str:
    """``dc:language`` from ``meta.xml``, when the default style declares none."""
    meta = package.part("meta.xml")
    found = next((e for e in meta.walk() if e.tag == "dc:language"), None) if meta else None
    return found.text().strip().lower() if found is not None else ""


class OdtConverter:
    """Archive → parts → styles → render; images and formulas join in T06 and T07."""

    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        with OdtPackage.open(source) as package:
            content = package.content()
            styles = Styles(content, package.styles())
            renderer = OdtRenderer(styles, language=styles.language or _meta_language(package))
            markdown = renderer.document(content)
        return ConversionResult(markdown, renderer.notes())
