"""Builders shared by the ODT text-subset tests (spec 003)."""

from pathlib import Path

from builders.odt_package import _odt_xml, odt_package
from builders.odt_styles import ODT_AUTOMATIC_STYLES

from clearmd.backend.schemas.notes import NoteItem, NoteKind
from clearmd.backend.services.conversion.odt import OdtConverter


def convert(path: Path) -> tuple[str, dict[NoteKind, tuple[NoteItem, ...]]]:
    result = OdtConverter().convert(path, None, path.with_suffix(".md"))  # type: ignore[arg-type]
    return result.markdown, {note.kind: note.items for note in result.notes}


def body(tmp_path: Path, xml: str, automatic: str = ODT_AUTOMATIC_STYLES) -> str:
    path = tmp_path / "t.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", xml, automatic=automatic)))
    return convert(path)[0]


def notes(tmp_path: Path, xml: str) -> dict[NoteKind, tuple[NoteItem, ...]]:
    path = tmp_path / "t.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", xml)))
    return convert(path)[1]
