"""ClearMD's own OpenDocument text converter (feature 003, ADR-0006, ADR-0024): stdlib only."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.odt.mathml import Unsupported, starmath, to_latex
from clearmd.backend.services.conversion.odt.package import OdtPackage, object_part
from clearmd.backend.services.conversion.odt.render import FormulaResult, OdtRenderer
from clearmd.backend.services.conversion.odt.styles import Styles
from clearmd.backend.services.conversion.odt.xmltree import Element

# Distinct formula objects read per document (as many as a ZIP may hold, ADR-0015); each one is
# read once however many times it is referenced, so a reference cannot multiply the work.
MAX_FORMULAS = 50_000
MAX_FORMULA_BYTES = 1024**2  # one formula object's content.xml


def _meta_language(package: OdtPackage) -> str:
    """``dc:language`` from ``meta.xml``, when the default style declares none."""
    meta = package.part("meta.xml")
    found = next((e for e in meta.walk() if e.tag == "dc:language"), None) if meta else None
    return found.text().strip().lower() if found is not None else ""


class _Formulas:
    """Formula objects read from the archive only, each once, within the count and size limits."""

    def __init__(self, package: OdtPackage) -> None:
        self._package = package
        # Each object read: its tree, and whether it came within MAX_FORMULAS (past the limit an
        # object is still read, for its StarMath source only).
        self._seen: dict[str, tuple[Element | None, bool]] = {}

    def __call__(self, formula: Element) -> FormulaResult:
        math, allowed = formula.find("math:math"), True  # a flat document keeps it inline
        if math is None:
            math, allowed = self._object(formula.get("xlink:href"))
        if math is None:
            return FormulaResult(None)
        source = starmath(math)
        if not allowed:
            return FormulaResult(None, source)
        try:
            return FormulaResult(to_latex(math), source)
        except Unsupported:
            return FormulaResult(None, source)

    def _object(self, href: str) -> tuple[Element | None, bool]:
        name = object_part(href)
        if name is None:  # outside the archive: never read
            return None, False
        if name not in self._seen:
            allowed = len(self._seen) < MAX_FORMULAS
            try:
                tree = self._package.part(name, max_bytes=MAX_FORMULA_BYTES)
            except ConversionError:  # over its size, or not XML ClearMD reads
                tree = None
            self._seen[name] = (tree, allowed)
        return self._seen[name]


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
