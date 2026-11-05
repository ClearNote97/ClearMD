"""Scripts and limits: sub/superscript bases and ``munder``, ``mover`` and ``munderover``."""

from clearmd.backend.services.conversion.odt.mathml.attributes import Unsupported, element_text
from clearmd.backend.services.conversion.odt.mathml.leaves import CONTROL_WORD_END, group
from clearmd.backend.services.conversion.odt.mathml.tables import (
    ACCENTS,
    FUNCTIONS,
    SYMBOLS,
    UNDER_ACCENTS,
    WIDE_ACCENTS,
    WORDS,
)
from clearmd.backend.services.conversion.xmltree import Element


def script(base: str, under: str | None, over: str | None) -> str:
    out = base
    if under is not None:
        out += f"_{group(under)}"
    if over is not None:
        out += f"^{group(over)}"
    return out


def script_base(element: Element, depth: int) -> str:
    from clearmd.backend.services.conversion.odt.mathml.translate import translate

    latex = translate(element, depth + 1)
    simple = element.tag in {"math:mi", "math:mn", "math:mo"} and len(element_text(element)) == 1
    return latex if simple or CONTROL_WORD_END.fullmatch(latex) else group(latex)


def under_over(element: Element, kids: list[Element], depth: int) -> str:
    from clearmd.backend.services.conversion.odt.mathml.translate import translate

    tag = element.tag
    expected = 3 if tag == "math:munderover" else 2
    if len(kids) != expected:
        raise Unsupported(tag)
    base_element = kids[0]
    base_text = element_text(base_element)
    big = base_element.tag in {"math:mo", "math:mi"} and (
        base_text in SYMBOLS or base_text in FUNCTIONS or base_text in WORDS
    )
    if tag == "math:mover" and not big:
        mark = element_text(kids[1])
        wide = kids[1].get("stretchy") == "true" and len(element_text(base_element)) > 1
        if kids[1].tag == "math:mo" and wide and mark in WIDE_ACCENTS:
            return f"{WIDE_ACCENTS[mark]}{group(translate(base_element, depth + 1))}"
        if kids[1].tag == "math:mo" and mark in ACCENTS:
            return f"{ACCENTS[mark]}{group(translate(base_element, depth + 1))}"
        above = group(translate(kids[1], depth + 1))
        return f"\\overset{above}{group(translate(base_element, depth + 1))}"
    if tag == "math:munder" and not big:
        mark = element_text(kids[1])
        if kids[1].tag == "math:mo" and mark in UNDER_ACCENTS:
            return f"{UNDER_ACCENTS[mark]}{group(translate(base_element, depth + 1))}"
        below = group(translate(kids[1], depth + 1))
        return f"\\underset{below}{group(translate(base_element, depth + 1))}"
    base = translate(base_element, depth + 1)
    under = translate(kids[1], depth + 1) if tag != "math:mover" else None
    over = translate(kids[-1], depth + 1) if tag != "math:munder" else None
    return script(base, under, over)
