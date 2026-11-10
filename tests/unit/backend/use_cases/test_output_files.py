"""Writes that a pre-planted link cannot redirect (security review of 001, H1)."""

import errno
import os
from pathlib import Path

import pytest

from clearmd.backend.use_cases.output_files import (
    UnsafeOutput,
    atomic_write,
    prepare_root,
    sweep_temporary_files,
)


def _root(tmp_path: Path) -> Path:
    return tmp_path / "ClearMD_Output"


def test_a_normal_write_has_normal_permissions_and_no_temp_left(tmp_path: Path) -> None:
    root = _root(tmp_path)
    target = root / "OutputMD" / "sub" / "a.md"
    atomic_write(target, "hello\r\nworld", inside=root)
    assert target.read_bytes() == b"hello\nworld"
    assert target.stat().st_mode & 0o777 == 0o666 & ~_umask()
    assert [p.name for p in target.parent.iterdir()] == ["a.md"]


def _umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


def test_a_planted_temp_link_cannot_redirect_the_write(tmp_path: Path) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("precious", encoding="utf-8")
    root = _root(tmp_path)
    (root / "OutputMD").mkdir(parents=True)
    (root / "OutputMD" / "report.md.clearmd-tmp").symlink_to(victim)
    atomic_write(root / "OutputMD" / "report.md", "attacker text", inside=root)
    assert victim.read_text(encoding="utf-8") == "precious"


def test_a_planted_target_link_is_replaced_not_followed(tmp_path: Path) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("precious", encoding="utf-8")
    root = _root(tmp_path)
    (root / "OutputMD").mkdir(parents=True)
    (root / "OutputMD" / "report.md").symlink_to(victim)
    atomic_write(root / "OutputMD" / "report.md", "markdown", inside=root)
    assert victim.read_text(encoding="utf-8") == "precious"
    assert not (root / "OutputMD" / "report.md").is_symlink()


@pytest.mark.parametrize(
    "linked", ["ClearMD_Output", "ClearMD_Output/OutputMD", "ClearMD_Output/OutputMD/sub"]
)
def test_a_linked_folder_on_the_way_is_refused(tmp_path: Path, linked: str) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / linked
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)
    root = _root(tmp_path)
    with pytest.raises(UnsafeOutput):
        prepare_root(root)
        atomic_write(root / "OutputMD" / "sub" / "a.md", "x", inside=root)
    assert list(outside.iterdir()) == []


def test_a_file_where_the_output_folder_should_be_is_refused(tmp_path: Path) -> None:
    (tmp_path / "ClearMD_Output").write_text("not a folder", encoding="utf-8")
    with pytest.raises(UnsafeOutput):
        prepare_root(_root(tmp_path))


def test_stale_temporary_files_are_swept(tmp_path: Path) -> None:
    root = _root(tmp_path)
    stale = root / "OutputMD" / "deep" / ".abc.clearmd-tmp"
    stale.parent.mkdir(parents=True)
    stale.write_text("half", encoding="utf-8")
    os.utime(stale, (0, 0))
    fresh = root / "OutputMD" / "deep" / ".def.clearmd-tmp"  # another run's, at work
    fresh.write_text("busy", encoding="utf-8")
    keep = root / "OutputMD" / "deep" / "a.md"
    keep.write_text("ok", encoding="utf-8")
    sweep_temporary_files(root)
    assert not stale.exists()
    assert keep.exists() and fresh.exists()


def test_a_failed_write_removes_its_temp_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path)
    (root / "OutputMD").mkdir(parents=True)

    def full_disk(src: str, dst: str) -> None:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(os, "replace", full_disk)
    with pytest.raises(OSError):
        atomic_write(root / "OutputMD" / "a.md", "x", inside=root)
    assert list((root / "OutputMD").iterdir()) == []


def test_the_sweep_never_follows_a_link_out_of_the_tree(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "keep.clearmd-tmp"
    victim.write_text("not ours", encoding="utf-8")
    root = _root(tmp_path)
    (root / "OutputMD").mkdir(parents=True)
    (root / "OutputMD" / "link").symlink_to(outside, target_is_directory=True)
    sweep_temporary_files(root)
    assert victim.exists()


def test_text_that_cannot_be_encoded_is_still_written(tmp_path: Path) -> None:
    root = _root(tmp_path)
    target = root / "OutputMD" / "a.md"
    atomic_write(target, "ok \udcff end", inside=root)
    assert target.read_bytes().startswith(b"ok ")
