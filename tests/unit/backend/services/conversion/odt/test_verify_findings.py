"""Regressions for the adversarial verification of feature 003's fixes (N1–N21), each from its
reported input."""

import io
import time
import zipfile
from pathlib import Path

import pytest
from build_fixtures import ODT_AUTOMATIC_STYLES, _odt_styles, _odt_xml, odt_package
from markdown_it import MarkdownIt
from support.markdown_guarantee import broken_promises

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.odt import OdtConverter
from clearmd.backend.services.conversion.odt.xmltree import XmlLimits, XmlRefused, parse_part

MATH = 'xmlns="http://www.w3.org/1998/Math/MathML"'
PARSER = MarkdownIt("commonmark")
NOTE = "<text:note><text:note-body><text:p>n</text:p></text:note-body></text:note>"
MONO_HTML = '<text:span text:style-name="T7">&lt;img src=x onerror=alert(1)&gt;</text:span>'
MIB = 1024**2


def content(body: str) -> bytes:
    return _odt_xml("document-content", body, automatic=ODT_AUTOMATIC_STYLES)


def convert_bytes(tmp_path: Path, data: bytes) -> tuple[str, set[NoteKind]]:
    path = tmp_path / "v.odt"
    path.write_bytes(data)
    result = OdtConverter().convert(path, None, path.with_suffix(".md"))  # type: ignore[arg-type]
    return result.markdown, {note.kind for note in result.notes}


def convert(
    tmp_path: Path, body: str, extra: dict[str, bytes] | None = None
) -> tuple[str, set[NoteKind]]:
    return convert_bytes(tmp_path, odt_package(content(body), extra=extra))


def md(tmp_path: Path, body: str, extra: dict[str, bytes] | None = None) -> str:
    return convert(tmp_path, body, extra)[0]


def timed(seconds: float, tmp_path: Path, body: str, extra: dict[str, bytes] | None = None) -> str:
    started = time.monotonic()
    markdown = md(tmp_path, body, extra)
    assert time.monotonic() - started < seconds
    return markdown


def manual_zip(entries: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in entries:
            method = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
            archive.writestr(zipfile.ZipInfo(name), data, compress_type=method)
    return buffer.getvalue()


def manifest(entries: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?><manifest:manifest '
        'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
        '<manifest:file-entry manifest:full-path="/" '
        'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
        f"{entries}</manifest:manifest>"
    ).encode()


MIME = ("mimetype", b"application/vnd.oasis.opendocument.text")


# --- Output guarantee ----------------------------------------------------------------------------


def test_n1_n12_a_footnote_before_a_link_keeps_the_link_and_no_url_is_live(tmp_path: Path) -> None:
    body = f'<text:p>a{NOTE}<text:a xlink:href="https://e.org/a`">t</text:a>{MONO_HTML}</text:p>'
    markdown = md(tmp_path, body)
    assert broken_promises(markdown, allowed_links=frozenset({"https://e.org/a%60"})) == []
    two = md(tmp_path, f'<text:p>see{NOTE}<text:a xlink:href="https://e.org/">the site</text:a>'
                       f"{NOTE}{NOTE}</text:p>")  # fmt: skip
    assert "see[^1][the site](https://e.org/)[^2][^3]" in two


def test_n2_a_backslash_and_bang_of_the_document_never_make_an_image(tmp_path: Path) -> None:
    link = md(tmp_path, '<text:p>a\\!<text:a xlink:href="https://e.org/x.png">t</text:a></text:p>')
    assert broken_promises(link, allowed_links=frozenset({"https://e.org/x.png"})) == []
    note = md(
        tmp_path,
        "<text:p>a\\!<text:note><text:note-body><text:p>http://evil/x.png</text:p>"
        "</text:note-body></text:note></text:p>",
    )
    assert broken_promises(note) == []


def test_the_checker_counts_backslashes_and_sees_images_made_with_definitions() -> None:
    assert broken_promises("a\\\\![^1]\n\n[^1]: http://evil/x.png\n") != []
    assert broken_promises("a\\![^1]\n\n[^1]: http://evil/x.png\n") == []


# --- Growth: everything written is charged -------------------------------------------------------


def test_n3_a_long_link_split_in_pieces_is_written_within_the_budget(tmp_path: Path) -> None:
    url = "https://e.org/" + "a" * 100_000
    pieces = "x<text:line-break/>" * 200
    markdown = timed(20, tmp_path, f'<text:p><text:a xlink:href="{url}">{pieces}</text:a></text:p>')
    assert len(markdown) < 3 * MIB and "x" in markdown


def test_n4_a_starmath_source_referenced_many_times_is_within_the_budget(tmp_path: Path) -> None:
    unsupported = (
        f'<math {MATH}><semantics><mrow><mzzz>u</mzzz></mrow><annotation encoding="StarMath 5.0">'
        + "x" * 200_000
        + "</annotation></semantics></math>"
    )
    frame = '<draw:frame><draw:object xlink:href="./Object 1"/></draw:frame>'
    markdown = timed(
        20, tmp_path, "<text:p>" + ("a " + frame) * 100 + "</text:p>",
        {"Object 1/content.xml": unsupported.encode()},
    )  # fmt: skip
    assert len(markdown) < 3 * MIB and "*Formula*" in markdown


def test_n5_n6_a_wide_sparse_table_is_neither_huge_nor_slow(tmp_path: Path) -> None:
    empty = '<table:table-cell table:number-columns-repeated="64"/>'
    first = f"<table:table-row><table:table-cell><text:p>a</text:p></table:table-cell>{empty * 780}"
    first += "<table:table-cell><text:p>end</text:p></table:table-cell></table:table-row>"
    row = (
        '<table:table-row table:number-rows-repeated="64"><table:table-cell><text:p>y</text:p>'
        "</table:table-cell></table:table-row>"
    )
    markdown = timed(10, tmp_path, f"<table:table>{first}{row * 40}</table:table>")
    assert len(markdown) < 3 * MIB and "end" in markdown and markdown.count("| y |") == 2560


def test_n7_many_pieces_in_one_paragraph_are_linear(tmp_path: Path) -> None:
    markdown = timed(5, tmp_path, "<text:p>" + 'a<text:s text:c="256"/>' * 20_000 + "</text:p>")
    assert markdown.count("a") == 20_000


def test_repeated_spaces_are_charged_too(tmp_path: Path) -> None:
    markdown = timed(10, tmp_path, "<text:p>" + 'a<text:s text:c="256"/>' * 100_000 + "</text:p>")
    assert len(markdown) < 3 * MIB and markdown.count("a") == 100_000


def test_n8_lists_deeper_than_ten_levels_are_flattened(tmp_path: Path) -> None:
    body = "<text:p>" + "line<text:line-break/>" * 5_000 + "</text:p>"
    for _ in range(120):
        body = (
            f'<text:list text:style-name="L1"><text:list-item>{body}</text:list-item></text:list>'
        )
    started = time.monotonic()
    markdown, kinds = convert(tmp_path, body)
    assert time.monotonic() - started < 20
    assert len(markdown) < 1 * MIB and NoteKind.ELEMENTS_SIMPLIFIED in kinds
    assert max(len(line) - len(line.lstrip()) for line in markdown.split("\n")) <= 40


# --- Structure -----------------------------------------------------------------------------------


def test_n10_two_skipped_list_levels_never_become_code(tmp_path: Path) -> None:
    deep = "<text:list-item><text:p>deep &lt;b&gt;</text:p></text:list-item>"
    body = (
        '<text:list text:style-name="L1"><text:list-item><text:p>x</text:p>'
        f"<text:list><text:list-item><text:list>{deep}</text:list></text:list-item></text:list>"
        "</text:list-item></text:list>"
    )
    tokens = [token.type for token in PARSER.parse(md(tmp_path, body))]
    assert "code_block" not in tokens and tokens.count("bullet_list_open") >= 2


def test_paragraphs_deep_in_a_list_keep_their_item(tmp_path: Path) -> None:
    body = (
        '<text:list text:style-name="L1"><text:list-item><text:p>a</text:p><text:list>'
        "<text:list-item><text:p>b</text:p><text:list><text:list-item><text:p>c</text:p>"
        "<text:p>d<text:line-break/>e</text:p></text:list-item></text:list></text:list-item>"
        "</text:list></text:list-item></text:list>"
    )
    markdown = md(tmp_path, body)
    assert "<p>c</p>\n<p>d<br />\ne</p>\n</li>" in PARSER.render(markdown)
    assert "code_block" not in [token.type for token in PARSER.parse(markdown)]


def test_n11_hidden_sections_comments_and_deletions_inside_containers_stay_out(
    tmp_path: Path,
) -> None:
    hidden = '<text:section text:display="none"><text:p>SECRET</text:p></text:section>'
    annotation = "<office:annotation><text:p>COMMENT</text:p></office:annotation>"
    deletion = (
        '<text:tracked-changes><text:changed-region text:id="c"><text:deletion>'
        "<text:p>DELETED</text:p></text:deletion></text:changed-region></text:tracked-changes>"
    )
    body = (
        f"<table:table><table:table-row><table:table-cell>{hidden}{annotation}{deletion}"
        "<text:p>c</text:p></table:table-cell></table:table-row></table:table>"
        f"<text:p>x<text:note><text:note-body>{hidden}<text:p>n</text:p></text:note-body>"
        f"</text:note><draw:frame><draw:text-box>{hidden}<text:p>box</text:p></draw:text-box>"
        "</draw:frame></text:p>"
    )
    markdown, kinds = convert(tmp_path, body)
    assert "SECRET" not in markdown and "COMMENT" not in markdown and "DELETED" not in markdown
    assert NoteKind.REVISIONS_DROPPED in kinds


def test_n13_a_list_that_restarts_stays_a_list_of_its_own(tmp_path: Path) -> None:
    one = '<text:list text:style-name="L2"><text:list-item><text:p>{}</text:p></text:list-item>'
    body = (one.format("one") + "</text:list>") + (one.format("restarted") + "</text:list>")
    html = PARSER.render(md(tmp_path, body))
    assert html.count("<ol") == 2


def test_n14_a_missing_or_huge_chart_is_an_image_never_a_formula(tmp_path: Path) -> None:
    frame = (
        '<text:p><draw:frame draw:name="Chart1"><draw:object xlink:href="./Object 1"/>'
        "</draw:frame></text:p>"
    )
    entry = (
        '<manifest:file-entry manifest:full-path="Object 1/" '
        'manifest:media-type="application/vnd.oasis.opendocument.chart"/>'
    )
    data = manual_zip(
        [MIME, ("META-INF/manifest.xml", manifest(entry)), ("content.xml", content(frame)),
         ("styles.xml", _odt_styles())]
    )  # fmt: skip
    markdown, kinds = convert_bytes(tmp_path, data)
    assert "*Image: Chart1*" in markdown and NoteKind.FORMULA_KEPT_AS_SOURCE not in kinds


# --- Text fidelity -------------------------------------------------------------------------------


def test_n18_formatting_that_markdown_cannot_hold_is_dropped_and_said(tmp_path: Path) -> None:
    body = '<text:p>word<text:span text:style-name="T1">"quoted"</text:span>s</text:p>'
    markdown, kinds = convert(tmp_path, body)
    assert PARSER.render(markdown) == "<p>word&quot;quoted&quot;s</p>\n"
    assert NoteKind.FORMATTING_DROPPED in kinds
    kept = md(tmp_path, '<text:p>a <text:span text:style-name="T1">"b"</text:span> c</text:p>')
    assert "<strong>" in PARSER.render(kept)


def test_n19_entities_the_document_wrote_show_as_written(tmp_path: Path) -> None:
    html = PARSER.render(md(tmp_path, "<text:p>&amp;lt;b&amp;gt; &amp;copy; &amp;#91;</text:p>"))
    assert "&amp;lt;b&amp;gt; &amp;copy; &amp;#91;" in html


# --- XML and ZIP ---------------------------------------------------------------------------------


@pytest.mark.parametrize("encoding", ["Shift_JIS", "UTF-7", "rot13", "no-such-encoding"])
def test_n9_an_xml_part_in_an_encoding_odf_does_not_allow_is_refused(encoding: str) -> None:
    with pytest.raises(XmlRefused):
        parse_part(f'<?xml version="1.0" encoding="{encoding}"?><p>x</p>'.encode())


def test_n9_one_formula_in_a_strange_encoding_never_fails_the_document(tmp_path: Path) -> None:
    formula = f'<?xml version="1.0" encoding="Shift_JIS"?><math {MATH}><mi>x</mi></math>'
    frame = '<draw:frame><draw:object xlink:href="./Object 1"/></draw:frame>'
    markdown = md(
        tmp_path, f"<text:p>a {frame}</text:p>", {"Object 1/content.xml": formula.encode()}
    )
    assert markdown.startswith("a")


@pytest.mark.filterwarnings("ignore:Duplicate name")
def test_n16_an_archive_with_a_name_twice_is_damaged(tmp_path: Path) -> None:
    good = content("<text:p>good</text:p>")
    data = manual_zip(
        [MIME, ("META-INF/manifest.xml", manifest("")), ("content.xml", good),
         ("content.xml", content("<text:p>EVIL</text:p>")), ("styles.xml", _odt_styles())]
    )  # fmt: skip
    with pytest.raises(ConversionError) as raised:
        convert_bytes(tmp_path, data)
    assert raised.value.code is ErrorCode.CORRUPT_FILE


@pytest.mark.parametrize("path", ["./content.xml", "/content.xml"])
def test_n17_encryption_declared_with_another_spelling_is_still_a_password(
    path: str, tmp_path: Path
) -> None:
    entry = (
        f'<manifest:file-entry manifest:full-path="{path}" manifest:media-type="text/xml">'
        "<manifest:encryption-data/></manifest:file-entry>"
    )
    data = manual_zip(
        [MIME, ("META-INF/manifest.xml", manifest(entry)), ("content.xml", content("<text:p/>")),
         ("styles.xml", _odt_styles())]
    )  # fmt: skip
    with pytest.raises(ConversionError) as raised:
        convert_bytes(tmp_path, data)
    assert raised.value.code is ErrorCode.PASSWORD_PROTECTED


def test_n20_names_and_namespace_declarations_count_toward_the_limits() -> None:
    with pytest.raises(XmlRefused):
        parse_part(f"<{'a' * 2000}/>".encode(), XmlLimits(max_characters=1000))
    declarations = " ".join(f'xmlns:n{index}="u{index}"' for index in range(2000))
    with pytest.raises(XmlRefused):
        parse_part(f"<p {declarations}/>".encode(), XmlLimits(max_elements=1000))


def test_n21_a_huge_mimetype_is_never_read(tmp_path: Path) -> None:
    data = manual_zip([("mimetype", b"application/vnd.oasis.opendocument.text" + b" " * 4096)])
    with pytest.raises(ConversionError) as raised:
        convert_bytes(tmp_path, data)
    assert raised.value.code is ErrorCode.CORRUPT_FILE and "larger" in str(raised.value)
