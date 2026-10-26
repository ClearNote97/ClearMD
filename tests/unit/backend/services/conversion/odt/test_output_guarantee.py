"""The output guarantee of ADR-0023 holds for .odt (AC-18), checked with a CommonMark parser."""

import itertools
import random
from pathlib import Path

import pytest
from build_fixtures import ODT_AUTOMATIC_STYLES, _odt_xml, odt_package
from support.markdown_guarantee import broken_promises

from clearmd.backend.services.conversion.odt import OdtConverter

OK_LINK = "https://ok.example/page"
BAD = [
    "&lt;img src=x&gt;",
    "![x](http://evil.example/b.png)",
    "[t](javascript:alert(1))",
    "`",
    "a ` b",
    "!",
    "]",
    "[a]: http://evil.example/r",
    "# h",
    "&gt; q",
    "- i",
    "1. i",
    "===",
    "--",
    "***",
    "~~~",
    "| a | b |",
    "\\",
    "\\`",
    "\\!",
    "a\\\\!",
    "&#10;",
    "a\\",
    "&amp;#58;",
    "# forged",
    "x\ty",
    "    indented",
]
# Where document text reaches the output, with the blocks ClearMD itself writes there: a span, a
# link's text, a note, a cell, an image title, a formula's text, code, a list item, a quotation.
PLACES: list[tuple[str, frozenset[str]]] = [
    ("<text:p>{t}</text:p>", frozenset()),
    ('<text:p><text:span text:style-name="T1">{t}</text:span>{t}</text:p>', frozenset()),
    ('<text:p><text:span text:style-name="T7">{t}</text:span> after</text:p>', frozenset()),
    (f'<text:p><text:a xlink:href="{OK_LINK}">{{t}}</text:a>{{t}}</text:p>', frozenset()),
    (
        '<text:p>x<text:note text:note-class="footnote"><text:note-body><text:p>{t}</text:p>'
        "</text:note-body></text:note>{t}</text:p>",
        frozenset(),
    ),
    (
        "<table:table><table:table-row><table:table-cell><text:p>{t}</text:p></table:table-cell>"
        "</table:table-row></table:table>",
        frozenset({"table_open"}),
    ),
    (
        '<text:p><draw:frame><draw:image xlink:href="Pictures/x.png"/><svg:title>{t}</svg:title>'
        "</draw:frame>{t}</text:p>",
        frozenset(),
    ),
    (
        "<text:p><draw:frame><draw:object><math:math><math:semantics><math:mrow>"
        "<math:mtext>{t}</math:mtext><math:mi>{t}</math:mi></math:mrow></math:semantics>"
        "</math:math></draw:object></draw:frame> {t}</text:p>",
        frozenset(),
    ),
    ('<text:p text:style-name="P2">{t}</text:p><text:p>{t}</text:p>', frozenset()),
    (
        '<text:list text:style-name="L1"><text:list-item><text:p>{t}</text:p></text:list-item>'
        "</text:list>",
        frozenset({"bullet_list_open"}),
    ),
    ('<text:p text:style-name="P1">{t}</text:p>', frozenset({"blockquote_open"})),
    (  # a note, then a link whose address holds the text, then a code run: N1 of the verification
        "<text:p>{t}<text:note><text:note-body><text:p>n</text:p></text:note-body></text:note>"
        f'<text:a xlink:href="{OK_LINK}">{{t}}</text:a><text:span text:style-name="T7">{{t}}'
        "</text:span></text:p>",
        frozenset(),
    ),
    (  # a code run with backticks opening a second paragraph of a list item: R3
        '<text:list text:style-name="L1"><text:list-item><text:p>a</text:p>'
        '<text:p><text:span text:style-name="T7">x``y</text:span>{t}</text:p></text:list-item>'
        "</text:list><text:p>{t}</text:p>",
        frozenset({"bullet_list_open"}),
    ),
    (
        '<text:p><text:a xlink:href="x&#10;{t}">x</text:a></text:p>',
        frozenset(),
    ),
    (
        '<text:p><text:a xlink:href="https://ok.example/a`b\\c">x</text:a>'
        '<text:span text:style-name="T7">{t}</text:span>{t}</text:p>',
        frozenset(),
    ),
    ('<text:h text:outline-level="1">{t}</text:h>', frozenset({"heading_open"})),
]


def _markdown(tmp_path: Path, body: str) -> str:
    path = tmp_path / "g.odt"
    path.write_bytes(
        odt_package(_odt_xml("document-content", body, automatic=ODT_AUTOMATIC_STYLES))
    )
    return OdtConverter().convert(path, None, path.with_suffix(".md")).markdown  # type: ignore[arg-type]


def _check(tmp_path: Path, body: str, blocks: frozenset[str] = frozenset()) -> list[str]:
    markdown = _markdown(tmp_path, body)
    allowed = frozenset({OK_LINK, "https://ok.example/a%60b%5Cc"})
    found = broken_promises(markdown, allowed_links=allowed, blocks=blocks)
    # The document's own link whose address starts "x" and a line break (R1): a link, never HTML.
    return [problem for problem in found if not problem.startswith(("link: 'x%0A", "link: 'x'"))]


@pytest.mark.parametrize(("place", "blocks"), PLACES)
def test_hostile_text_in_every_place_never_breaks_the_guarantee(
    place: str, blocks: frozenset[str], tmp_path: Path
) -> None:
    broken = {
        text: problems
        for text in BAD
        if (problems := _check(tmp_path, place.format(t=text), blocks))
    }
    assert broken == {}


def test_a_backtick_next_to_a_code_run_never_reopens_it(tmp_path: Path) -> None:
    body = (
        '<text:p>x `<text:span text:style-name="T7">``&lt;img src=x&gt;!</text:span> after</text:p>'
    )
    assert _check(tmp_path, body) == []
    at_start = '<text:p><text:span text:style-name="T7">``&lt;img src=x&gt;!</text:span> b</text:p>'
    assert _check(tmp_path, at_start) == []


def test_dangerous_neighbours_across_runs_never_break_it(tmp_path: Path) -> None:
    pieces = ["!", "\\!", "]", "`", "(http://evil.example/b.png)", ": http://evil.example/r", "["]
    broken = {}
    for left, right in itertools.product(pieces, repeat=2):
        body = (
            f'<text:p><text:span text:style-name="T1">{left}</text:span>'
            f'<text:span text:style-name="T2">{right}</text:span>'
            f'<text:note text:note-class="footnote"><text:note-body><text:p>n</text:p>'
            f"</text:note-body></text:note>{right}</text:p>"
        )
        if problems := _check(tmp_path, body):
            broken[(left, right)] = problems
    assert broken == {}


def test_a_seeded_fuzz_of_places_and_text_never_breaks_it(tmp_path: Path) -> None:
    rng = random.Random(2026)
    broken = {}
    for _ in range(400):
        chosen = [rng.choice(PLACES) for _ in range(rng.randint(1, 4))]
        body = "".join(
            place.format(t="".join(rng.choice(BAD) for _ in range(rng.randint(1, 4))))
            for place, _ in chosen
        )
        blocks = frozenset().union(*(allowed for _, allowed in chosen))
        if problems := _check(tmp_path, body, blocks):
            broken[body] = problems
    assert dict(itertools.islice(broken.items(), 3)) == {}
