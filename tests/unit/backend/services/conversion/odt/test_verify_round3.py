"""Regressions for the third adversarial verification of feature 003 (R1–R7, P1), each from its
reported input."""

import time
from pathlib import Path

import pytest
from build_fixtures import ODT_AUTOMATIC_STYLES, _odt_xml, odt_package
from markdown_it import MarkdownIt
from support.markdown_guarantee import broken_promises

from clearmd.backend.services.conversion.markdown_out import link_target
from clearmd.backend.services.conversion.odt import OdtConverter
from clearmd.backend.services.conversion.tex.render import render_latex
from clearmd.backend.services.conversion.xmltree import XmlRefused, parse_part

PARSER = MarkdownIt("commonmark")
MONO = '<text:span text:style-name="T7">{}</text:span>'
STYLES = ODT_AUTOMATIC_STYLES.replace(
    "</office:automatic-styles>",
    '<style:style style:name="TU" style:family="text"><style:text-properties fo:font-weight="bold"'
    ' style:text-underline-style="solid"/></style:style></office:automatic-styles>',
)


def md(tmp_path: Path, body: str) -> str:
    path = tmp_path / "r.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", body, automatic=STYLES)))
    return OdtConverter().convert(path, None, path.with_suffix(".md")).markdown  # type: ignore[arg-type]


def tex(body: str) -> str:
    document = f"\\documentclass{{article}}\\begin{{document}}{body}\\end{{document}}"
    return render_latex(document).markdown


def lists(*names: str, between: str = "") -> str:
    one = '<text:list text:style-name="L2"><text:list-item><text:p>{}</text:p></text:list-item>'
    return between.join(one.format(name) + "</text:list>" for name in names)


# --- Critical ------------------------------------------------------------------------------------


@pytest.mark.parametrize("control", ["&#10;", "&#13;", "&#9;"])
def test_r1_a_line_break_in_a_link_address_never_makes_html(control: str, tmp_path: Path) -> None:
    body = (
        f'<text:p>see <text:a xlink:href="x{control}onmouseover=alert(1)">t</text:a> end</text:p>'
    )
    markdown = md(tmp_path, body)
    assert "\n" not in markdown.strip() and "html" not in str(broken_promises(markdown))
    assert link_target("a\nb\rc\x7f") == "a%0Ab%0Dc%7F"


def test_r1_r2_tex_addresses_with_a_line_break_or_no_text_stay_inert() -> None:
    for body in ("\\href{a\nonmouseover=alert(1)}{t}", "\\href{<img src=x onerror=alert(1)>}{}"):
        markdown = tex(body)
        assert not [p for p in broken_promises(markdown) if "html" in p or "image" in p], markdown


# --- High ----------------------------------------------------------------------------------------


def test_r3_code_with_backticks_in_an_item_never_opens_a_fence(tmp_path: Path) -> None:
    body = (
        '<text:list text:style-name="L1"><text:list-item><text:p>a</text:p>'
        f"<text:p>{MONO.format('x``y')} z</text:p></text:list-item></text:list>"
        "<text:p># heading</text:p><text:p>&gt; quote</text:p><text:p>- item</text:p>"
    )
    markdown = md(tmp_path, body)
    assert broken_promises(markdown, blocks=frozenset({"bullet_list_open"})) == []
    assert markdown.count("bullet_list") == 0 and "\\# heading" in markdown


# --- Medium and low ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        lists("one", "restart", between='<draw:frame draw:name=""/>'),
        "<text:section>" + lists("one") + "</text:section>" + lists("restart"),
        '<text:list text:style-name="L1"><text:list-item><text:p>a</text:p>'
        + lists("n1", "restart").replace("L2", "L2")
        + "</text:list-item></text:list>",
    ],
)
def test_r4_a_restarted_list_stays_a_list_of_its_own(body: str, tmp_path: Path) -> None:
    html = PARSER.render(md(tmp_path, body))
    lists_written = html.count("<ol") + html.count("<ul")
    assert lists_written == (3 if "L1" in body else 2), html


def test_r5_emphasis_next_to_clearmds_own_tags_is_judged_by_what_is_written(
    tmp_path: Path,
) -> None:
    body = '<text:p><text:span text:style-name="TU">a</text:span>b</text:p>'
    html = PARSER.render(md(tmp_path, body))
    assert "**" not in html and "<u>a</u>" in md(tmp_path, body)
    kept = PARSER.render(
        md(tmp_path, '<text:p><text:span text:style-name="TU">a</text:span> b</text:p>')
    )
    assert "<strong>" in kept


def test_r6_list_indentation_is_charged(tmp_path: Path) -> None:
    body = "<text:p>" + "a<text:line-break/>" * 100_000 + "</text:p>"
    for _ in range(10):
        body = (
            '<text:list text:style-name="L2"><text:list-item text:start-value="999999">'
            f"{body}</text:list-item></text:list>"
        )
    started = time.monotonic()
    markdown = md(tmp_path, body)
    assert time.monotonic() - started < 30
    assert len(markdown) < 2_500_000 and markdown.count("a") >= 100_000


@pytest.mark.parametrize(
    "data",
    [
        b'\xef\xbb\xbf<?xml version="1.0" encoding="windows-1252"?><p>caf\xe9</p>',
        b'<?xml version="1.0"' + b" " * 600 + b'encoding="cp1252"?><p>caf\xe9</p>',
    ],
)
def test_r7_a_bom_or_a_long_declaration_never_hides_the_encoding(data: bytes) -> None:
    with pytest.raises(XmlRefused):
        parse_part(data)


def test_p1_a_note_that_looks_like_a_block_stays_text(tmp_path: Path) -> None:
    markdown = md(
        tmp_path,
        "<text:p>a<text:note><text:note-body><text:p># x</text:p></text:note-body>"
        "</text:note></text:p>",
    )
    assert "[^1]: \\# x" in markdown


def test_r5_the_emphasis_check_agrees_with_a_commonmark_parser() -> None:
    import random
    import re

    from clearmd.backend.services.conversion.odt.render import _unpaired_delimiters

    parser = MarkdownIt("commonmark", {"html": True}).enable("strikethrough")
    units = ["*", "**", "~~", "a", ".", "(", "<u>", "</u>", " ", '"', "é"]
    rng = random.Random(5)
    wrong = []
    for _ in range(20_000):
        text = "x " + "".join(rng.choice(units) for _ in range(rng.randint(1, 10)))
        shown = re.sub(r"<[^>]+>", "", parser.render(text))
        literal = "*" in shown or "~" in shown
        # Exact for "*"; for tildes it may only be more careful (runs of four are paired by GFM).
        if (
            literal
            and not _unpaired_delimiters(text)
            or (not literal and _unpaired_delimiters(text) and "~~~~" not in text)
        ):
            wrong.append(text)
    assert wrong == []
