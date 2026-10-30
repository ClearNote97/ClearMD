"""ClearMD's own OpenDocument text converter (feature 003, ADR-0006, ADR-0024): stdlib only."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.images import MAX_IMAGE_BYTES, ImageSink
from clearmd.backend.services.conversion.odt.mathml import Unsupported, starmath, to_latex
from clearmd.backend.services.conversion.odt.package import OdtPackage, object_part, picture_part
from clearmd.backend.services.conversion.odt.render import FormulaResult, OdtRenderer
from clearmd.backend.services.conversion.odt.styles import Styles
from clearmd.backend.services.conversion.xmltree import Element

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
        self._results: dict[str, FormulaResult] = {}  # each object translated once

    def __call__(self, formula: Element) -> FormulaResult:
        inline = formula.find("math:math")  # a flat document keeps it inline
        if inline is not None:
            return self._translate(inline, allowed=True)
        name = object_part(formula.get("xlink:href"))
        if name is None:  # outside the archive: never read
            return FormulaResult(None)
        if name not in self._results:
            tree, allowed = self._object(name)
            if tree is None:  # too big or unreadable: the manifest says what it was
                result = FormulaResult(None, formula=self._package.is_formula(name))
            elif tree.tag != "math:math":  # a chart or another embedded object
                result = FormulaResult(None, formula=False)
            else:
                result = self._translate(tree, allowed=allowed)
            self._results[name] = result
        return self._results[name]

    def _translate(self, math: Element, *, allowed: bool) -> FormulaResult:
        source = starmath(math)
        if not allowed:
            return FormulaResult(None, source)
        try:
            return FormulaResult(to_latex(math), source)
        except Unsupported:
            return FormulaResult(None, source)

    def _object(self, name: str) -> tuple[Element | None, bool]:
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

    def convert(
        self,
        source: Path,
        detection: Detection,
        target: Path,
        *,
        images: ImageSink | None = None,
    ) -> ConversionResult:
        with OdtPackage.open(source) as package:
            content = package.content()
            styles = Styles(content, package.styles())

            def picture(href: str) -> str | None:
                name = picture_part(href)
                data = package.picture(name, MAX_IMAGE_BYTES) if name else None
                return images.add(data) if images is not None and data else None

            renderer = OdtRenderer(
                styles,
                formula=_Formulas(package),
                language=styles.language or _meta_language(package),
                source_size=len(content.text()),
                pictures=picture if images is not None else None,
            )
            markdown = renderer.document(content)
        return ConversionResult(markdown, renderer.notes())
