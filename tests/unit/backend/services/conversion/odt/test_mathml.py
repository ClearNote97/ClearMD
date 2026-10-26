"""LibreOffice Math: the MathML subset to LaTeX, the StarMath fallback (AC-11, AC-12, AC-19)."""

from pathlib import Path

import pytest
from build_fixtures import MATHML_SUBSET, _odt_xml, odt_package
from support import ODT_DIR

from clearmd.backend.schemas.notes import NoteItem, NoteKind
from clearmd.backend.services.conversion.odt import OdtConverter
from clearmd.backend.services.conversion.odt.mathml import Unsupported, to_latex
from clearmd.backend.services.conversion.odt.xmltree import parse_part

NS = 'xmlns="http://www.w3.org/1998/Math/MathML"'


def latex(body: str) -> str:
    # As LibreOffice writes it: one presentation row next to the StarMath annotation.
    wrapped = f"<math {NS}><semantics><mrow>{body}</mrow></semantics></math>"
    return to_latex(parse_part(wrapped.encode()))


def convert(path: Path) -> tuple[str, dict[NoteKind, tuple[NoteItem, ...]]]:
    result = OdtConverter().convert(path, None, path.with_suffix(".md"))  # type: ignore[arg-type]
    return result.markdown, {note.kind: note.items for note in result.notes}


@pytest.mark.parametrize(
    ("mathml", "expected"),
    [
        ("<mfrac><mi>a</mi><mi>b</mi></mfrac>", "\\frac{a}{b}"),
        ("<msup><mi>x</mi><mn>2</mn></msup>", "x^{2}"),
        ("<msub><mi>x</mi><mi>i</mi></msub>", "x_{i}"),
        ("<msubsup><mi>x</mi><mi>i</mi><mn>2</mn></msubsup>", "x_{i}^{2}"),
        ("<msqrt><mi>y</mi></msqrt>", "\\sqrt{y}"),
        ("<mroot><mi>y</mi><mn>3</mn></mroot>", "\\sqrt[3]{y}"),
        ("<mi>α</mi><mo>+</mo><mi>Ω</mi>", "\\alpha+\\Omega"),
        ("<mi>sin</mi><mi>x</mi>", "\\sin x"),
        ('<mi mathvariant="italic">dx</mi>', "dx"),
        ('<mi mathvariant="normal">∞</mi>', "\\infty"),
        ('<mi mathvariant="bold">v</mi>', "\\mathbf{v}"),
        ("<mn>3.14</mn><mo>×</mo><mn>2</mn>", "3.14\\times2"),
        ("<mo>≤</mo><mo>≠</mo><mo>→</mo><mo>∈</mo><mo>−</mo>", "\\le\\neq\\to\\in-"),
        ("<munderover><mo>∑</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover>"
         "<mi>i</mi>", "\\sum_{i=1}^{n}i"),
        ("<munder><mi>lim</mi><mrow><mi>n</mi><mo>→</mo><mi>∞</mi></mrow></munder>",
         "\\lim_{n\\to\\infty}"),
        ('<mover accent="true"><mi>x</mi><mo>^</mo></mover>', "\\hat{x}"),
        ('<mover accent="true"><mi>x</mi><mo>¯</mo></mover>', "\\overline{x}"),
        ('<mover accent="true"><mi>v</mi><mo>→</mo></mover>', "\\vec{v}"),
        ("<mover><mi>x</mi><mi>y</mi></mover>", "\\overset{y}{x}"),
        ('<mrow><mo fence="true" stretchy="true">(</mo><mi>a</mi>'
         '<mo fence="true" stretchy="true">)</mo></mrow>', "\\left(a\\right)"),
        ('<mfenced open="[" close="]"><mi>a</mi><mi>b</mi></mfenced>', "\\left[a,b\\right]"),
        ("<mtable><mtr><mtd><mi>a</mi></mtd><mtd><mi>b</mi></mtd></mtr>"
         "<mtr><mtd><mi>c</mi></mtd><mtd><mi>d</mi></mtd></mtr></mtable>",
         "\\begin{matrix}a & b \\\\ c & d\\end{matrix}"),
        ("<mtext>si x # 1</mtext>", "\\text{si x \\# 1}"),
        ("<mi>{</mi><mo>%</mo><mo>&amp;</mo>", "\\{\\%\\&"),
        ("<mspace/>", "\\,"),
    ],
)  # fmt: skip
def test_the_subset_becomes_latex(mathml: str, expected: str) -> None:
    assert latex(mathml) == expected


@pytest.mark.parametrize(
    "mathml",
    [
        "<mmultiscripts><mi>a</mi><mprescripts/><none/><mi>b</mi></mmultiscripts>",
        '<menclose notation="box"><mi>z</mi></menclose>',
        "<maction><mi>a</mi></maction>",
        "<mi>" + "<mrow>" * 0 + "x</mi>" + "<msup>" * 70 + "<mi>a</mi>" + "<mi>b</mi></msup>" * 70,
    ],
)
def test_anything_outside_the_subset_is_unsupported(mathml: str) -> None:
    with pytest.raises(Unsupported):
        latex(mathml)


def test_the_real_formulas_of_libreoffice() -> None:
    markdown, found = convert(ODT_DIR / "real" / "report.odt")
    assert "$$\n\\frac{a}{b}+x^{2}+\\sqrt{y}+\\alpha\n$$" in markdown
    assert "En línea $\\sum_{i=1}^{n}i$ y $\\int_{0}^{1}x^{2}dx$." in markdown
    assert (
        "\\left(\\alpha+\\beta\\right)+\\begin{matrix}a & b \\\\ c & d\\end{matrix}+\\hat{x}+"
        "\\frac{\\lim_{n\\to\\infty}1}{n}"
    ) in markdown
    assert "Fuera del subconjunto: `a lsup b`." in markdown
    assert found[NoteKind.FORMULA_KEPT_AS_SOURCE] == (NoteItem("1"),)


def test_the_generated_formulas_and_an_object_outside_the_archive() -> None:
    markdown, found = convert(ODT_DIR / "formulas.odt")
    assert "$$\n\\frac{a}{b}+x^{2}+\\sqrt{y}+\\alpha\n$$" in markdown
    assert "En línea $\\sum_{i=1}^{n}i$ y fin." in markdown
    assert "Fuera: `boxed z`." in markdown
    assert "Afuera: *Formula*." in markdown  # "../escape" is never read
    assert found[NoteKind.FORMULA_KEPT_AS_SOURCE] == (NoteItem("2"),)


def test_formula_text_never_becomes_markdown(tmp_path: Path) -> None:
    hostile = MATHML_SUBSET.replace(
        "<math:mi>α</math:mi>",
        "<math:mtext>![x](http://evil.example/b.png) `y` &lt;img&gt;</math:mtext>",
    )
    body = '<text:p>a <draw:frame><draw:object xlink:href="./Object 1"/></draw:frame> b</text:p>'
    path = tmp_path / "t.odt"
    path.write_bytes(
        odt_package(
            _odt_xml("document-content", body),
            extra={"Object 1/content.xml": f'<?xml version="1.0"?>{hostile}'.encode()},
        )
    )
    markdown, _ = convert(path)
    assert "](" not in markdown and "<img" not in markdown


def test_formula_objects_are_bounded_in_number_and_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.backend.services.conversion import odt

    monkeypatch.setattr(odt, "MAX_FORMULAS", 2)
    frames = "".join(
        f'<draw:frame><draw:object xlink:href="./Object {n}"/></draw:frame> ' for n in (1, 2, 3)
    )
    again = '<draw:frame><draw:object xlink:href="./Object 1"/></draw:frame>' * 50
    path = tmp_path / "t.odt"
    objects = {
        f"Object {n}/content.xml": f'<?xml version="1.0"?>{MATHML_SUBSET}'.encode()
        for n in (1, 2, 3)
    }
    path.write_bytes(
        odt_package(
            _odt_xml("document-content", f"<text:p>{frames}{again}</text:p>"), extra=objects
        )
    )
    markdown, found = convert(path)
    # Three distinct objects, the limit at two: the third shows its source. The first one,
    # referenced 50 more times, is read once and converted every time.
    assert markdown.count("\\frac{a}{b}") == 52 and markdown.count("{a over b}") == 1
    assert found[NoteKind.FORMULA_KEPT_AS_SOURCE] == (NoteItem("1"),)
