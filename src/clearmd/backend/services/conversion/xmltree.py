"""A minimal element tree for untrusted XML, built by ``pyexpat`` under ClearMD's limits (ADR-0024).

Shared by the ``.odt`` converter and the HTML article mode (ADR-0025). ``xml.etree`` gives no hook
to refuse a ``DOCTYPE`` before it is processed; here any document type or entity declaration
refuses the part (neither OpenDocument nor trafilatura's XML uses them), whatever the expat version.
Elements, nesting depth and characters are counted while parsing; the tree is built with an
explicit stack and walked without recursion.
"""

import pyexpat
import re
from collections.abc import Iterator
from dataclasses import dataclass, field

# ClearMD's mark for its own block lines (markdown_out.MARK): a document can never carry it.
_MARK = "\ue000"

# Namespace URIs → the prefixes OpenDocument uses (MathML's default namespace gets "math").
PREFIXES = {
    "urn:oasis:names:tc:opendocument:xmlns:office:1.0": "office",
    "urn:oasis:names:tc:opendocument:xmlns:style:1.0": "style",
    "urn:oasis:names:tc:opendocument:xmlns:text:1.0": "text",
    "urn:oasis:names:tc:opendocument:xmlns:table:1.0": "table",
    "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0": "draw",
    "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0": "fo",
    "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0": "svg",
    "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0": "manifest",
    "urn:oasis:names:tc:opendocument:xmlns:meta:1.0": "meta",
    "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0": "number",
    "http://www.w3.org/1999/xlink": "xlink",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://www.w3.org/1998/Math/MathML": "math",
}


# The encodings OpenDocument allows (UTF-8, UTF-16) and the ones expat reads natively.
_ENCODINGS = frozenset(
    {"utf-8", "utf8", "utf-16", "utf-16le", "utf-16be", "us-ascii", "iso-8859-1"}
)
_DECLARED = re.compile(rb"^(?:\xef\xbb\xbf)?\s*<\?xml\b([^>]*?)\?>")
_ENCODING = re.compile(rb"encoding\s*=\s*[\"']([^\"']*)[\"']")


class XmlRefused(Exception):
    """The part is not XML ClearMD reads: malformed, a DOCTYPE or entity, or over a limit."""


@dataclass(frozen=True)
class XmlLimits:
    """Per part. Real documents: a few thousand elements, nesting under 50 (ADR-0024)."""

    max_elements: int = 2_000_000
    max_depth: int = 256
    max_characters: int = 128 * 1024**2


@dataclass
class Element:
    tag: str
    attributes: dict[str, str] = field(default_factory=dict)
    children: list["Element | str"] = field(default_factory=list)

    def get(self, name: str, default: str = "") -> str:
        return self.attributes.get(name, default)

    def elements(self, tag: str | None = None) -> Iterator["Element"]:
        """Direct child elements (with ``tag``, when given)."""
        for child in self.children:
            if isinstance(child, Element) and (tag is None or child.tag == tag):
                yield child

    def find(self, tag: str) -> "Element | None":
        return next(self.elements(tag), None)

    def walk(self) -> Iterator["Element"]:
        """This element and every element under it, in document order, without recursion."""
        pending: list[Element] = [self]
        while pending:
            element = pending.pop()
            yield element
            pending.extend(reversed([c for c in element.children if isinstance(c, Element)]))

    def text(self) -> str:
        """All the text under this element, in order."""
        parts: list[str] = []
        pending: list[Element | str] = [self]
        while pending:
            item = pending.pop()
            if isinstance(item, str):
                parts.append(item)
            else:
                pending.extend(reversed(item.children))
        return "".join(parts)


def int_attribute(value: str, default: int, *, cap: int = 1_000_000) -> int:
    """A whole number written in an attribute: ASCII digits only ("²" is a digit to ``isdigit``),
    a bounded length (``int`` refuses over 4,300 digits) and a cap."""
    if not (value.isascii() and value.isdigit()):
        return default
    return min(int(value), cap) if len(value) <= 9 else cap


def _check_encoding(data: bytes) -> None:
    """Only the encodings OpenDocument uses: the declaration is read whole (a BOM before it, or
    padding inside it, never hides it)."""
    if not data.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"<?xml"):
        return  # no declaration (UTF-8), or UTF-16, which expat reads by its BOM
    declared = _DECLARED.match(data[:65_536])
    if declared is None:
        raise XmlRefused("an XML declaration ClearMD does not read")
    encoding = _ENCODING.search(declared.group(1))
    if encoding is not None and encoding.group(1).decode("latin-1").lower() not in _ENCODINGS:
        raise XmlRefused("an encoding OpenDocument does not use")


def _name(expat_name: str) -> str:
    uri, _, local = expat_name.rpartition(" ")
    if not uri:
        return local
    prefix = PREFIXES.get(uri)
    return f"{prefix}:{local}" if prefix else f"{{{uri}}}{local}"


def parse_part(data: bytes, limits: XmlLimits | None = None) -> Element:
    """The root element of ``data``; ``XmlRefused`` for anything ClearMD does not read."""
    limits = limits or XmlLimits()
    _check_encoding(data)
    parser = pyexpat.ParserCreate(namespace_separator=" ")
    parser.SetParamEntityParsing(pyexpat.XML_PARAM_ENTITY_PARSING_NEVER)
    stack: list[Element] = []
    roots: list[Element] = []
    counts = {"elements": 0, "characters": 0}

    def refuse(*_: object) -> None:
        raise XmlRefused("a document type or entity declaration")

    def refuse_external(*_: object) -> int:
        raise XmlRefused("an external entity")

    def count_characters(size: int) -> None:
        counts["characters"] += size
        if counts["characters"] > limits.max_characters:
            raise XmlRefused(f"more than {limits.max_characters} characters")

    def namespace(prefix: str | None, uri: str | None) -> None:
        counts["elements"] += 1  # a declaration costs like an attribute
        if counts["elements"] > limits.max_elements:
            raise XmlRefused(f"more than {limits.max_elements} elements and attributes")
        count_characters(len(prefix or "") + len(uri or ""))

    def start(name: str, attributes: dict[str, str]) -> None:
        counts["elements"] += 1
        if counts["elements"] > limits.max_elements:
            raise XmlRefused(f"more than {limits.max_elements} elements")
        if len(stack) >= limits.max_depth:
            raise XmlRefused(f"nested deeper than {limits.max_depth} levels")
        counts["elements"] += len(attributes)  # an attribute costs like an element
        if counts["elements"] > limits.max_elements:
            raise XmlRefused(f"more than {limits.max_elements} elements and attributes")
        # Names count too (an element or attribute name can be as long as any text).
        count_characters(len(name) + sum(len(k) + len(v) for k, v in attributes.items()))
        element = Element(
            _name(name), {_name(k): v.replace(_MARK, "") for k, v in attributes.items()}
        )
        if stack:
            stack[-1].children.append(element)
        else:
            roots.append(element)
        stack.append(element)

    def end(_: str) -> None:
        stack.pop()

    def characters(text: str) -> None:
        counts["characters"] += len(text)
        if counts["characters"] > limits.max_characters:
            raise XmlRefused(f"more than {limits.max_characters} characters")
        if not stack:
            return
        # A CR (from "&#13;") ends a line to CommonMark: one line ending, "\n" (audit of 004).
        text = text.replace(_MARK, "").replace("\r\n", "\n").replace("\r", "\n")
        children = stack[-1].children
        if children and isinstance(children[-1], str):
            children[-1] += text
        else:
            children.append(text)

    parser.StartDoctypeDeclHandler = refuse
    parser.EntityDeclHandler = refuse
    parser.UnparsedEntityDeclHandler = refuse
    parser.ExternalEntityRefHandler = refuse_external
    parser.StartNamespaceDeclHandler = namespace
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = characters
    parser.buffer_text = True
    try:
        parser.Parse(data, True)
    except pyexpat.ExpatError as error:
        raise XmlRefused(f"not well-formed XML: {error}") from None
    except RecursionError:
        raise XmlRefused("nested too deeply") from None
    except (ValueError, LookupError) as error:  # an encoding expat or Python cannot read
        raise XmlRefused(f"an encoding ClearMD does not read: {error}") from None
    if not roots:
        raise XmlRefused("no root element")
    return roots[0]
