"""Builders shared by the ODT code-review regressions (feature 003)."""

from pathlib import Path

from build_fixtures import ODT_AUTOMATIC_STYLES, _odt_xml, odt_package
from markdown_it import MarkdownIt

from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.odt import OdtConverter
from clearmd.backend.services.conversion.odt.mathml import to_latex
from clearmd.backend.services.conversion.xmltree import parse_part

MATH = 'xmlns="http://www.w3.org/1998/Math/MathML"'


STYLES = ODT_AUTOMATIC_STYLES.replace(
    "</office:automatic-styles>",
    '<style:style style:name="PH" style:family="paragraph">'
    '<style:text-properties text:display="none"/></style:style>'
    '<style:style style:name="PB" style:family="paragraph">'
    '<style:text-properties fo:font-weight="bold"/></style:style>'
    "</office:automatic-styles>",
)


PARSER = MarkdownIt("commonmark")


def md(tmp_path: Path, body: str, extra: dict[str, bytes] | None = None) -> str:
    return convert(tmp_path, body, extra)[0]


def convert(
    tmp_path: Path, body: str, extra: dict[str, bytes] | None = None
) -> tuple[str, set[NoteKind]]:
    path = tmp_path / "r.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", body, automatic=STYLES), extra=extra))
    result = OdtConverter().convert(path, None, path.with_suffix(".md"))  # type: ignore[arg-type]
    return result.markdown, {note.kind for note in result.notes}


def latex(body: str) -> str:
    return to_latex(
        parse_part(f"<math {MATH}><semantics><mrow>{body}</mrow></semantics></math>".encode())
    )
