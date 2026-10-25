"""Includes followed only inside the document folder (ADR-0022, AC-14, AC-15)."""

import shutil
from pathlib import Path

import pytest
from support import TEX_DIR

from clearmd.backend.schemas.models import ConversionResult
from clearmd.backend.schemas.notes import NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.tex.document import convert_document
from clearmd.backend.services.conversion.tex.includes import (
    MAX_DEPTH,
    MAX_FILES,
    IncludeState,
    resolve_include,
)


def _state(folder: Path) -> IncludeState:
    return IncludeState(folder)


def _refused(result: ConversionResult) -> list[NoteItem]:
    return [
        item
        for note in result.notes
        if note.kind is NoteKind.INCLUDE_NOT_FOLLOWED
        for item in note.items
    ]


@pytest.fixture
def hostile(tmp_path: Path) -> Path:
    shutil.copytree(TEX_DIR / "hostile", tmp_path / "hostile")
    shutil.copyfile(TEX_DIR / "paper.tex", tmp_path / "paper.tex")  # what "../paper" would reach
    return tmp_path / "hostile"


@pytest.mark.parametrize(
    ("argument", "reason"),
    [
        ("/etc/passwd", NoteReason.ABSOLUTE),
        ("C:/Windows/win.ini", NoteReason.ABSOLUTE),
        ("~/secret", NoteReason.ABSOLUTE),
        ("../paper", NoteReason.PARENT_SEGMENT),
        ("chapters/../../paper", NoteReason.PARENT_SEGMENT),
        ("data.csv", NoteReason.NOT_TEX),
        ("nowhere", NoteReason.MISSING),
        ("", NoteReason.MISSING),
    ],
)
def test_refusals_happen_before_touching_the_disk(
    hostile: Path, argument: str, reason: NoteReason
) -> None:
    assert resolve_include(argument, _state(hostile)) == reason


def test_a_relative_tex_file_inside_the_folder_is_allowed(hostile: Path) -> None:
    assert resolve_include("cycle_b", _state(hostile)) == hostile / "cycle_b.tex"


def test_a_link_on_the_way_is_refused(hostile: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.tex"
    outside.write_text("secreto", encoding="utf-8")
    (hostile / "linked.tex").symlink_to(outside)
    (hostile / "dirlink").symlink_to(tmp_path, target_is_directory=True)
    assert resolve_include("linked", _state(hostile)) == NoteReason.LINK
    assert resolve_include("dirlink/outside", _state(hostile)) == NoteReason.LINK


def test_the_absolute_include_never_reads_the_file(hostile: Path) -> None:
    result = convert_document(hostile / "absolute.tex")
    assert "root:" not in result.markdown
    assert "`\\input{/etc/passwd}`" in result.markdown
    assert _refused(result) == [NoteItem("/etc/passwd", NoteReason.ABSOLUTE)]


def test_a_cycle_is_cut_and_reported(hostile: Path) -> None:
    result = convert_document(hostile / "cycle_a.tex")
    assert result.markdown.count("A") == 1 and result.markdown.count("B") == 1
    assert _refused(result) == [NoteItem("cycle_a", NoteReason.CYCLE)]


def test_nesting_stops_after_eight_levels(hostile: Path) -> None:
    result = convert_document(hostile / "deep0.tex")
    assert f"nivel {MAX_DEPTH}" in result.markdown
    assert f"nivel {MAX_DEPTH + 1}" not in result.markdown
    assert _refused(result) == [NoteItem(f"deep{MAX_DEPTH + 1}", NoteReason.TOO_DEEP)]


def test_no_more_than_two_hundred_files(tmp_path: Path) -> None:
    (tmp_path / "parts").mkdir()
    for n in range(MAX_FILES + 1):
        (tmp_path / "parts" / f"p{n}.tex").write_text(f"parte{n} ", encoding="utf-8")
    main = "".join(f"\\input{{parts/p{n}}}" for n in range(MAX_FILES + 1))
    (tmp_path / "main.tex").write_text(main, encoding="utf-8")
    result = convert_document(tmp_path / "main.tex")
    assert f"parte{MAX_FILES - 1} " in result.markdown
    assert f"parte{MAX_FILES} " not in result.markdown
    assert _refused(result) == [NoteItem(f"parts/p{MAX_FILES}", NoteReason.TOO_MANY)]


def test_a_thesis_becomes_one_markdown_file(tmp_path: Path) -> None:
    shutil.copytree(TEX_DIR / "thesis", tmp_path / "thesis")
    result = convert_document(tmp_path / "thesis" / "main.tex")
    text = result.markdown
    for marker in ("fixture-tex-ch1", "fixture-tex-ch2", "fixture-tex-deeper"):
        assert marker in text
    assert text.index("fixture-tex-ch1") < text.index("fixture-tex-ch2")
    assert "## Primer capítulo" in text and "### Más hondo" in text
    assert _refused(result) == []
