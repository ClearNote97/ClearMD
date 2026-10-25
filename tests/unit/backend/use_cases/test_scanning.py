"""Scanning rules of AC-02, AC-03 and AC-05 - AC-08 (and the unreadable-folder case)."""

import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.events import ScanProgress
from clearmd.backend.schemas.limits import MIB, Limits
from clearmd.backend.schemas.models import InputProblem
from clearmd.backend.use_cases.scanning import Candidate, ScanResult, is_hidden, scan


def _touch(path: Path, data: bytes = b"x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _names(candidates: tuple[Candidate, ...]) -> list[str]:
    return [c.path.name for c in candidates]


def _reasons(result: ScanResult) -> dict[str, SkipReason]:
    return {item.path.name: item.reason for item in result.skipped}


def test_a_folder_is_walked_recursively_in_a_stable_order(tmp_path: Path) -> None:
    project = tmp_path / "project"
    _touch(project / "b.pdf")
    _touch(project / "A.docx")
    _touch(project / "sub" / "deep" / "c.txt")
    result = scan([project], recursive=True, limits=Limits())
    assert _names(result.candidates) == ["A.docx", "b.pdf", "c.txt"]
    deep = result.candidates[2]
    assert deep.input == project
    assert deep.relative_dir == Path("sub") / "deep"


def test_no_recursive_stays_at_the_top_level(tmp_path: Path) -> None:
    _touch(tmp_path / "p" / "top.pdf")
    _touch(tmp_path / "p" / "sub" / "inner.pdf")
    result = scan([tmp_path / "p"], recursive=False, limits=Limits())
    assert _names(result.candidates) == ["top.pdf"]


def test_input_files_keep_no_relative_folder(tmp_path: Path) -> None:
    source = _touch(tmp_path / "report.pdf")
    (candidate,) = scan([source], recursive=True, limits=Limits()).candidates
    assert candidate.input == source
    assert candidate.relative_dir == Path()
    assert not candidate.input_is_dir


@pytest.mark.parametrize("name", ["ClearMD_Output", "clearmd_output", "CLEARMD_OUTPUT"])
def test_output_folders_are_never_entered(tmp_path: Path, name: str) -> None:
    _touch(tmp_path / "p" / name / "OutputMD" / "old.md")
    _touch(tmp_path / "p" / name / "again.pdf")
    result = scan([tmp_path / "p"], recursive=True, limits=Limits())
    assert result.candidates == ()
    assert _reasons(result) == {name: SkipReason.OUTPUT_FOLDER}
    assert result.skipped[0].is_dir


def test_hidden_files_and_folders_are_skipped_once(tmp_path: Path) -> None:
    _touch(tmp_path / "p" / ".secret.pdf")
    _touch(tmp_path / "p" / ".git" / "a.pdf")
    _touch(tmp_path / "p" / ".git" / "b.pdf")
    result = scan([tmp_path / "p"], recursive=True, limits=Limits())
    assert result.candidates == ()
    assert _reasons(result) == {".git": SkipReason.HIDDEN, ".secret.pdf": SkipReason.HIDDEN}


def test_symbolic_links_are_not_followed(tmp_path: Path) -> None:
    target = _touch(tmp_path / "outside" / "real.pdf")
    project = tmp_path / "p"
    project.mkdir()
    os.symlink(target, project / "link.pdf")
    os.symlink(target.parent, project / "linked_folder")
    result = scan([project], recursive=True, limits=Limits())
    assert result.candidates == ()
    assert _reasons(result) == {"link.pdf": SkipReason.SYMLINK, "linked_folder": SkipReason.SYMLINK}


def test_an_input_that_is_a_symlink_is_not_followed(tmp_path: Path) -> None:
    target = _touch(tmp_path / "real.pdf")
    link = tmp_path / "link.pdf"
    os.symlink(target, link)
    result = scan([link], recursive=True, limits=Limits())
    assert result.candidates == ()
    assert _reasons(result) == {"link.pdf": SkipReason.SYMLINK}


def test_office_lock_files_are_skipped(tmp_path: Path) -> None:
    _touch(tmp_path / "p" / "~$report.docx")
    result = scan([tmp_path / "p"], recursive=True, limits=Limits())
    assert _reasons(result) == {"~$report.docx": SkipReason.LOCK_FILE}


def test_files_over_the_size_limit_are_skipped_without_reading_them(tmp_path: Path) -> None:
    big = tmp_path / "p" / "huge.pdf"
    big.parent.mkdir()
    with big.open("wb") as handle:  # sparse: no real disk space
        handle.truncate(251 * MIB)
    result = scan([tmp_path / "p"], recursive=True, limits=Limits())
    assert _reasons(result) == {"huge.pdf": SkipReason.TOO_LARGE}


@pytest.mark.parametrize(
    ("name", "reason"),
    [
        ("notes.md", SkipReason.ALREADY_MARKDOWN),
        ("NOTES.MARKDOWN", SkipReason.ALREADY_MARKDOWN),
        ("bundle.zip", SkipReason.ZIP_ARCHIVE),
    ],
)
def test_markdown_and_zip_are_skipped_with_their_reason(
    tmp_path: Path, name: str, reason: SkipReason
) -> None:
    _touch(tmp_path / "p" / name)
    assert _reasons(scan([tmp_path / "p"], recursive=True, limits=Limits())) == {name: reason}


def test_missing_inputs_are_reported_and_the_rest_continues(tmp_path: Path) -> None:
    present = _touch(tmp_path / "a.pdf")
    result = scan([tmp_path / "missing.pdf", present], recursive=True, limits=Limits())
    assert _names(result.candidates) == ["a.pdf"]
    assert [(e.path.name, e.problem) for e in result.input_errors] == [
        ("missing.pdf", InputProblem.NOT_FOUND)
    ]


def test_an_empty_folder_yields_nothing(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    result = scan([tmp_path / "empty"], recursive=True, limits=Limits())
    assert (result.candidates, result.skipped, result.input_errors) == ((), (), ())


def test_an_unreadable_folder_is_skipped_not_fatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    locked = tmp_path / "p" / "locked"
    _touch(locked / "a.pdf")
    _touch(tmp_path / "p" / "ok.pdf")
    real_scandir = os.scandir

    def scandir(path: Path) -> object:  # root reads everything, so the denial is simulated
        if Path(path) == locked:
            raise PermissionError(13, "Permission denied", str(path))
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", scandir)
    result = scan([tmp_path / "p"], recursive=True, limits=Limits())
    assert _names(result.candidates) == ["ok.pdf"]
    assert _reasons(result) == {"locked": SkipReason.UNREADABLE}


def test_scan_reports_progress_per_folder(tmp_path: Path) -> None:
    _touch(tmp_path / "p" / "a.pdf")
    _touch(tmp_path / "p" / "sub" / "b.pdf")
    events: list[ScanProgress] = []
    scan([tmp_path / "p"], recursive=True, limits=Limits(), on_progress=events.append)
    assert [e.current.name for e in events] == ["p", "sub"]
    assert events[-1].found == 1  # b.pdf is counted after its folder was announced


def test_windows_hidden_attribute_is_honored() -> None:
    hidden_attr = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 2)
    windows_hidden = SimpleNamespace(st_file_attributes=hidden_attr)
    visible = SimpleNamespace(st_file_attributes=0)
    assert is_hidden("report.pdf", windows_hidden)  # type: ignore[arg-type]
    assert not is_hidden("report.pdf", visible)  # type: ignore[arg-type]
    assert is_hidden(".bashrc", visible)  # type: ignore[arg-type]
    assert not is_hidden("report.pdf", SimpleNamespace())  # type: ignore[arg-type]


def test_windows_junctions_count_as_links() -> None:
    from clearmd.backend.use_cases.scanning import is_link_entry

    junction = SimpleNamespace(is_symlink=lambda: False, is_junction=lambda: True)
    folder = SimpleNamespace(is_symlink=lambda: False, is_junction=lambda: False)
    assert is_link_entry(junction)  # type: ignore[arg-type]
    assert not is_link_entry(folder)  # type: ignore[arg-type]


def test_any_error_reading_a_folder_skips_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import errno

    broken = tmp_path / "p" / "network_drive"
    _touch(broken / "a.pdf")
    _touch(tmp_path / "p" / "ok.pdf")
    real_scandir = os.scandir

    def scandir(path: Path) -> object:
        if Path(path) == broken:
            raise OSError(errno.EIO, "Input/output error", str(path))
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", scandir)
    result = scan([tmp_path / "p"], recursive=True, limits=Limits())
    assert _names(result.candidates) == ["ok.pdf"]
    assert _reasons(result) == {"network_drive": SkipReason.UNREADABLE}


def test_absurdly_deep_folders_are_cut_without_crashing(tmp_path: Path) -> None:
    from clearmd.backend.use_cases.scanning import MAX_DEPTH

    deep = tmp_path / "p"
    for _ in range(MAX_DEPTH + 5):
        deep = deep / "d"
    _touch(deep / "bottom.pdf")
    _touch(tmp_path / "p" / "top.pdf")
    result = scan([tmp_path / "p"], recursive=True, limits=Limits())
    assert _names(result.candidates) == ["top.pdf"]
    assert [item.reason for item in result.skipped] == [SkipReason.TOO_DEEP]


def test_files_come_before_subfolders_and_subfolders_in_order(tmp_path: Path) -> None:
    _touch(tmp_path / "p" / "b" / "x.pdf")
    _touch(tmp_path / "p" / "a" / "y.pdf")
    _touch(tmp_path / "p" / "a" / "deep" / "z.pdf")
    _touch(tmp_path / "p" / "top.pdf")
    result = scan([tmp_path / "p"], recursive=True, limits=Limits())
    assert _names(result.candidates) == ["top.pdf", "y.pdf", "z.pdf", "x.pdf"]
