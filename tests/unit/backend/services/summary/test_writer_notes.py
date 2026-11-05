"""Resumen_ClearMD.md: notes and long lists."""

from pathlib import Path

import pytest
from support.summary_cases import _noted_report, _write

from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.summary.writer import MarkdownSummaryWriter
from clearmd.i18n import load_catalog


@pytest.mark.parametrize(
    ("language", "heading", "unknown", "include"),
    [
        (
            "en",
            "## Needs your attention",
            "commands ClearMD does not know were left as written: `\\foo`, `\\bar`",
            "includes not followed: `../secret.tex` (outside the document folder)",
        ),
        (
            "es",
            "## Necesita tu atención",
            "se dejaron tal cual comandos que ClearMD no conoce: `\\foo`, `\\bar`",
            "no se siguieron estas inclusiones: `../secret.tex`"
            " (fuera de la carpeta del documento)",
        ),
    ],
)
def test_notes_are_listed_in_the_users_language(
    tmp_path: Path, language: str, heading: str, unknown: str, include: str
) -> None:
    notes = (
        ConversionNote(NoteKind.UNKNOWN_COMMANDS, (NoteItem("\\foo"), NoteItem("\\bar"))),
        ConversionNote(
            NoteKind.INCLUDE_NOT_FOLLOWED, (NoteItem("../secret.tex", "outside_folder"),)
        ),
    )
    writer = MarkdownSummaryWriter(load_catalog(language), version="0.1.0")
    report = _noted_report(tmp_path, notes)
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    section = text.split(heading + "\n", 1)[1].split("\n\n", 1)[0]
    first = {"en": "- ⚠️ `main.tex` in `thesis` — converted, but:",
             "es": "- ⚠️ `main.tex` en `thesis` — se convirtió, pero:"}[language]  # fmt: skip
    assert section.splitlines() == [first, f"  - {unknown}", f"  - {include}"]


def test_a_long_list_of_names_is_cut_at_twenty(tmp_path: Path) -> None:
    items = tuple(NoteItem(f"\\cmd{chr(97 + n)}") for n in range(25))
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    report = _noted_report(tmp_path, (ConversionNote(NoteKind.UNKNOWN_COMMANDS, items),))
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "`\\cmdt` and 5 more" in text
    assert "`\\cmdu`" not in text


def test_files_without_notes_have_no_notes_section(tmp_path: Path) -> None:
    assert "converted, but" not in _write(tmp_path)
