"""ClearMD's own OpenDocument text converter (feature 003, ADR-0006, ADR-0024): stdlib only."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.odt.mathml import Unsupported, starmath, to_latex
from clearmd.backend.services.conversion.odt.package import OdtPackage, object_part
from clearmd.backend.services.conversion.odt.render import FormulaResult, OdtRenderer
from clearmd.backend.services.conversion.odt.styles import Styles
from clearmd.backend.services.conversion.odt.xmltree import Element

MAX_FORMULAS = 2000  # formula objects read per document; past it, the StarMath source
MAX_FORMULA_BYTES = 1024**2  # one formula object's content.xml


def _meta_language(package: OdtPackage) -> str:
    """``dc:language`` from ``meta.xml``, when the default style declares none."""
    meta = package.part("meta.xml")
    found = next((e for e in meta.walk() if e.tag == "dc:language"), None) if meta else None
    return found.text().strip().lower() if found is not None else ""


class _Formulas:
    """Formula objects read from the archive only, within their count and size limits."""

    def __init__(self, package: OdtPackage) -> None:
        self._package = package
        self._read = 0

    def __call__(self, formula: Element) -> FormulaResult:
        math = formula.find("math:math")  # a flat document keeps it inline
        if math is None:
            math = self._object(formula.get("xlink:href"))
        if math is None:
            return FormulaResult(None)
        source = starmath(math)
        if self._read > MAX_FORMULAS:
            return FormulaResult(None, source)
        try:
            return FormulaResult(to_latex(math), source)
        except Unsupported:
            return FormulaResult(None, source)

    def _object(self, href: str) -> Element | None:
        name = object_part(href)
        if name is None:  # outside the archive: never read
            return None
        self._read += 1  # past MAX_FORMULAS it is still read, for its StarMath source only
        try:
            return self._package.part(name, max_bytes=MAX_FORMULA_BYTES)
        except ConversionError:  # over its size, or not XML ClearMD reads
            return None


class OdtConverter:
    """Archive → parts → styles → render, with images as placeholders and formulas as LaTeX."""

    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        with OdtPackage.open(source) as package:
            content = package.content()
            styles = Styles(content, package.styles())
            renderer = OdtRenderer(
                styles,
                formula=_Formulas(package),
                language=styles.language or _meta_language(package),
            )
            markdown = renderer.document(content)
        return ConversionResult(markdown, renderer.notes())
