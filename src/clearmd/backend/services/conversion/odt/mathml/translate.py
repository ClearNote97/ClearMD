"""The translation itself: one MathML element to LaTeX, and the StarMath source kept next to it."""

from clearmd.backend.services.conversion.odt.mathml.attributes import (
    MAX_DEPTH,
    STARMATH,
    Unsupported,
    children,
    element_text,
)
from clearmd.backend.services.conversion.odt.mathml.leaves import group, identifier, join, operator
from clearmd.backend.services.conversion.odt.mathml.rows import matrix, sequence
from clearmd.backend.services.conversion.odt.mathml.scripts import script, script_base, under_over
from clearmd.backend.services.conversion.odt.mathml.tables import (
    FENCES,
    LATEX_SPECIAL,
    TEXT_SPECIAL,
    VARIANTS,
)
from clearmd.backend.services.conversion.xmltree import Element


def translate(element: Element, depth: int) -> str:
    if depth > MAX_DEPTH:
        raise Unsupported("nested too deeply")
    tag = element.tag
    kids = children(element)
    if tag == "math:mstyle" and element.get("mathvariant") not in {"", "italic"}:
        command = VARIANTS.get(element.get("mathvariant"))
        if command is None:
            raise Unsupported(f"mstyle mathvariant={element.get('mathvariant')}")
        return f"{command}{group(sequence(kids, depth))}"
    if tag in {"math:mrow", "math:mstyle", "math:mpadded", "math:math"}:
        return sequence(kids, depth)
    if tag == "math:semantics":
        presentation = [k for k in kids if k.tag not in {"math:annotation", "math:annotation-xml"}]
        return sequence(presentation[:1], depth)
    if tag == "math:mi":
        return identifier(element)
    if tag == "math:mn":
        return "".join(LATEX_SPECIAL.get(c, c) for c in element_text(element))
    if tag == "math:mo":
        return operator(element)
    if tag == "math:mtext":
        text = "".join(TEXT_SPECIAL.get(c, c) for c in element.text())
        return f"\\text{{{text}}}"
    if tag == "math:mspace":
        return "\\,"
    if len(kids) == 2 and tag == "math:mfrac":
        top, bottom = (translate(k, depth + 1) for k in kids)
        if element.get("linethickness") in {"0", "0pt", "0px", "0em"}:
            return f"\\genfrac{{}}{{}}{{0pt}}{{}}{group(top)}{group(bottom)}"
        return f"\\frac{group(top)}{group(bottom)}"
    if tag == "math:msqrt":
        return f"\\sqrt{group(sequence(kids, depth))}"
    if tag == "math:mroot" and len(kids) == 2:
        index = group(translate(kids[1], depth + 1))  # braced: an index holding "]" stays one
        return f"\\sqrt[{index}]{group(translate(kids[0], depth + 1))}"
    if tag in {"math:msup", "math:msub", "math:msubsup"}:
        expected = 3 if tag == "math:msubsup" else 2
        if len(kids) != expected:
            raise Unsupported(tag)
        base = script_base(kids[0], depth)
        rest = [translate(k, depth + 1) for k in kids[1:]]
        if tag == "math:msup":
            return script(base, None, rest[0])
        if tag == "math:msub":
            return script(base, rest[0], None)
        return script(base, rest[0], rest[1])
    if tag in {"math:munder", "math:mover", "math:munderover"}:
        return under_over(element, kids, depth)
    if tag == "math:mfenced":
        opening = FENCES.get(element.get("open", "("), element.get("open", "("))
        closing = FENCES.get(element.get("close", ")"), element.get("close", ")"))
        separator = (element.get("separators", ",").strip() or ",")[0]
        inner = separator.join(translate(k, depth + 1) for k in kids)
        return join([f"\\left{opening or '.'}", inner, f"\\right{closing or '.'}"])
    if tag == "math:mtable":
        return matrix(element, depth)
    raise Unsupported(tag)


def to_latex(math: Element) -> str:
    """The LaTeX of a ``math:math`` element; ``Unsupported`` outside the subset."""
    if math.tag != "math:math":
        raise Unsupported(math.tag)
    return sequence(children(math), 0)


def starmath(math: Element) -> str | None:
    """The StarMath source LibreOffice keeps next to the MathML, when there is one."""
    for element in math.walk():
        if element.tag == "math:annotation" and element.get("encoding") == STARMATH:
            source = " ".join(element.text().split())
            return source or None
    return None
