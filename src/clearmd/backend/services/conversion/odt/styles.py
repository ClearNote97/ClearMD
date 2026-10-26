"""OpenDocument styles: automatic and named, with their parents (ADR-0024).

What matters for Markdown: the text properties (bold, italic, underline, strike-through,
super/subscript, monospace, hidden) and the paragraph roles (title, subtitle, quotation, code).
A loop in a parent chain stops; a missing style is plain.
"""

from dataclasses import dataclass, replace
from enum import Enum

from clearmd.backend.services.conversion.odt.xmltree import Element

MONOSPACE_FAMILIES = frozenset(
    {
        "liberation mono", "dejavu sans mono", "courier new", "courier", "consolas", "menlo",
        "monaco", "source code pro", "noto sans mono", "lucida console", "cascadia mono",
        "cascadia code", "fira mono", "fira code", "ubuntu mono", "andale mono",
    }
)  # fmt: skip
MAX_PARENTS = 32


class Role(Enum):
    TITLE = "Title"
    SUBTITLE = "Subtitle"
    QUOTE = "Quotations"
    CODE = "Preformatted_20_Text"


ROLE_NAMES = {
    "Title": Role.TITLE,
    "Subtitle": Role.SUBTITLE,
    "Quotations": Role.QUOTE,
    "Preformatted_20_Text": Role.CODE,
    "Source_20_Code": Role.CODE,
}
# Named character styles of LibreOffice, in case a document does not define them.
CHARACTER_NAMES = {
    "Emphasis": {"italic": True},
    "Strong_20_Emphasis": {"bold": True},
    "Source_20_Text": {"mono": True},
}


@dataclass(frozen=True)
class TextProps:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    position: str = ""  # "super", "sub" or ""
    mono: bool = False
    hidden: bool = False


@dataclass(frozen=True)
class ListLevel:
    numbered: bool
    start: int = 1


def _weight_is_bold(value: str) -> bool:
    return value == "bold" or (value.isdigit() and int(value) >= 600)


def _position(value: str) -> str:
    first = value.split()[0] if value.split() else ""
    if first == "super" or (first.endswith("%") and not first.startswith("-") and first != "0%"):
        return "super"
    if first == "sub" or first.startswith("-"):
        return "sub"
    return ""


class Styles:
    def __init__(self, content: Element, styles: Element | None) -> None:
        self._text: dict[str, Element] = {}
        self._paragraph: dict[str, Element] = {}
        self._lists: dict[str, Element] = {}
        self._mono_fonts: set[str] = set()
        for root in (styles, content):  # content's automatic styles win over styles.xml
            if root is None:
                continue
            for group in root.elements():
                if group.tag == "office:font-face-decls":
                    self._fonts(group)
                elif group.tag in {"office:styles", "office:automatic-styles"}:
                    self._collect(group)

    def _fonts(self, decls: Element) -> None:
        for face in decls.elements("style:font-face"):
            family = face.get("svg:font-family").strip("'\" ").lower()
            if face.get("style:font-pitch") == "fixed" or family in MONOSPACE_FAMILIES:
                self._mono_fonts.add(face.get("style:name"))

    def _collect(self, group: Element) -> None:
        for style in group.elements():
            name = style.get("style:name")
            if style.tag == "style:style":
                family = style.get("style:family")
                if family == "text":
                    self._text[name] = style
                elif family == "paragraph":
                    self._paragraph[name] = style
            elif style.tag == "text:list-style":
                self._lists[name] = style

    def _chain(self, table: dict[str, Element], name: str) -> list[Element]:
        """The style and its parents, nearest first (a loop or a missing parent stops it)."""
        chain: list[Element] = []
        seen: set[str] = set()
        while name and name in table and name not in seen and len(chain) < MAX_PARENTS:
            seen.add(name)
            chain.append(table[name])
            name = table[name].get("style:parent-style-name")
        return chain

    def _apply(self, props: TextProps, style: Element) -> TextProps:
        found = style.find("style:text-properties")
        named = CHARACTER_NAMES.get(style.get("style:name"), {})
        changes: dict[str, object] = dict(named)
        if found is not None:
            if "fo:font-weight" in found.attributes:
                changes["bold"] = _weight_is_bold(found.get("fo:font-weight"))
            if "fo:font-style" in found.attributes:
                changes["italic"] = found.get("fo:font-style") in {"italic", "oblique"}
            if "style:text-underline-style" in found.attributes:
                changes["underline"] = found.get("style:text-underline-style") != "none"
            if "style:text-line-through-style" in found.attributes:
                changes["strike"] = found.get("style:text-line-through-style") != "none"
            if "style:text-position" in found.attributes:
                changes["position"] = _position(found.get("style:text-position"))
            font = found.get("style:font-name") or found.get("fo:font-family").strip("'\" ")
            if font:
                changes["mono"] = font in self._mono_fonts or font.lower() in MONOSPACE_FAMILIES
            if found.get("text:display") == "none":
                changes["hidden"] = True
        return replace(props, **changes)  # type: ignore[arg-type]

    def text_props(self, name: str, inherited: TextProps) -> TextProps:
        """``inherited`` (the paragraph's, the outer span's) changed by a text style and parents."""
        props = inherited
        for style in reversed(self._chain(self._text, name)):
            props = self._apply(props, style)
        return props

    def paragraph_props(self, name: str) -> TextProps:
        props = TextProps()
        for style in reversed(self._chain(self._paragraph, name)):
            props = self._apply(props, style)
        return props

    def role(self, name: str) -> Role | None:
        for style in self._chain(self._paragraph, name):
            role = ROLE_NAMES.get(style.get("style:name"))
            if role is not None:
                return role
        return ROLE_NAMES.get(name)

    def list_style_of_paragraph(self, name: str) -> str:
        for style in self._chain(self._paragraph, name):
            if style.get("style:list-style-name"):
                return style.get("style:list-style-name")
        return ""

    def list_level(self, list_style: str, level: int) -> ListLevel:
        style = self._lists.get(list_style)
        if style is None:
            return ListLevel(numbered=False)
        for entry in style.elements():
            if entry.get("text:level") == str(level):
                if entry.tag == "text:list-level-style-number" and entry.get("style:num-format"):
                    start = entry.get("text:start-value")
                    return ListLevel(True, int(start) if start.isdigit() else 1)
                return ListLevel(numbered=False)
        return ListLevel(numbered=False)
