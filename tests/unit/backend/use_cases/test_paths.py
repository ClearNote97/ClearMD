"""Output paths and names (ADR-0016; AC-01, AC-02, AC-04, AC-12 - AC-15)."""

import os
import random
from pathlib import Path

import pytest

from clearmd.backend.use_cases.paths import (
    NameRequest,
    output_parent_for,
    resolve_names,
    target_for,
)

ROOT = Path("/d/ClearMD_Output")


def test_a_file_writes_next_to_itself() -> None:
    assert output_parent_for(Path("/d/report.pdf"), is_dir=False) == Path("/d")


def test_a_folder_writes_next_to_itself() -> None:
    assert output_parent_for(Path("/d/project"), is_dir=True) == Path("/d")


def test_a_drive_root_keeps_its_output_inside() -> None:
    root = Path(Path.cwd().anchor)
    assert output_parent_for(root, is_dir=True) == root


def test_the_home_folder_keeps_its_output_inside(monkeypatch: pytest.MonkeyPatch) -> None:
    home = Path(os.path.abspath("/home/ana"))  # inputs are absolute (on Windows: a drive)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    assert output_parent_for(home, is_dir=True) == home
    assert output_parent_for(home / "docs", is_dir=True) == home


def test_an_explicit_output_folder_replaces_the_parent() -> None:
    assert output_parent_for(Path("/d/report.pdf"), is_dir=False, override=Path("/x")) == Path("/x")
    assert output_parent_for(Path("/d/project"), is_dir=True, override=Path("/x")) == Path("/x")


def test_target_keeps_the_full_stem_and_goes_into_outputmd() -> None:
    assert (
        target_for(Path("/d/report.v2.final.pdf"), ROOT) == ROOT / "OutputMD" / "report.v2.final.md"
    )


def test_target_of_a_file_without_extension() -> None:
    assert target_for(Path("/d/scan"), ROOT) == ROOT / "OutputMD" / "scan.md"


def test_unicode_names_are_preserved() -> None:
    assert target_for(Path("/d/informe_año_ñ.docx"), ROOT).name == "informe_año_ñ.md"


def _request(name: str, label: str | None = None, folder: str = "") -> NameRequest:
    source = Path("/d") / folder / name
    return NameRequest(
        source=source,
        target=target_for(source, ROOT, Path(folder)),
        label=label or source.suffix.lstrip(".").lower() or "docx",  # no extension: detected
    )


def _names(requests: list[NameRequest]) -> list[str]:
    return [target.name for target in resolve_names(requests)]


def test_unique_names_are_left_alone() -> None:
    assert _names([_request("a.pdf"), _request("b.docx")]) == ["a.md", "b.md"]


def test_case_insensitive_collisions_get_the_source_extension() -> None:
    assert _names([_request("report.pdf"), _request("Report.docx")]) == [
        "report (pdf).md",
        "Report (docx).md",
    ]


def test_same_extension_collisions_get_a_counter_in_path_order() -> None:
    # On Linux both can exist; on Windows they cannot, but the rule is the same.
    assert _names([_request("report.pdf"), _request("Report.pdf")]) == [
        "report (pdf 2).md",
        "Report (pdf).md",
    ]


def test_a_file_without_extension_uses_its_detected_format() -> None:
    assert _names([_request("scan", label="docx"), _request("scan.pdf")]) == [
        "scan (docx).md",
        "scan (pdf).md",
    ]


def test_a_suffixed_name_never_steals_an_existing_name() -> None:
    requests = [_request("report.pdf"), _request("report.docx"), _request("report (pdf).txt")]
    names = _names(requests)
    assert len({name.casefold() for name in names}) == 3
    assert names[2] == "report (pdf).md"  # an original name wins over a generated one


def test_different_folders_do_not_collide() -> None:
    assert _names([_request("a.pdf", folder="x"), _request("a.docx", folder="y")]) == [
        "a.md",
        "a.md",
    ]


def test_names_do_not_depend_on_input_order() -> None:
    requests = [
        _request("report.pdf"),
        _request("Report.pdf"),
        _request("REPORT.docx"),
        _request("report"),
        _request("notes.txt"),
    ]
    # Keyed by the text: on Windows "report.pdf" and "Report.pdf" are equal paths.
    expected = dict(zip((str(r.source) for r in requests), resolve_names(requests), strict=True))
    for seed in range(20):
        shuffled = requests[:]
        random.Random(seed).shuffle(shuffled)
        got = dict(zip((str(r.source) for r in shuffled), resolve_names(shuffled), strict=True))
        assert got == expected


def test_very_long_names_are_shortened_to_fit_any_file_system() -> None:
    long_stem = "ñ" * 200  # 400 bytes in UTF-8
    target = target_for(Path(f"/d/{long_stem}.pdf"), ROOT)
    assert len(target.name.encode("utf-8")) <= 200
    assert target.name.endswith(".md")
    collided = resolve_names(
        [
            NameRequest(Path(f"/d/{long_stem}.pdf"), target, "pdf"),
            NameRequest(Path(f"/d/{long_stem}.docx"), target, "docx"),
        ]
    )
    assert all(len(path.name.encode("utf-8")) <= 200 for path in collided)
    assert collided[0] != collided[1]


def test_unicode_forms_of_the_same_name_collide() -> None:
    nfc, nfd = "a\u00f1o.pdf", "an\u0303o.docx"  # "año" composed and decomposed
    names = _names([_request(nfc), _request(nfd)])
    # Same name on macOS (and to the eye): both get the extension, so neither overwrites the other.
    assert [name.endswith((" (pdf).md", " (docx).md")) for name in names] == [True, True]
