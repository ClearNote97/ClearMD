"""Opening a results folder in the system's file browser, shared by every interface (005, T02)."""

import subprocess
import sys
from pathlib import Path

import pytest

from clearmd.backend.services import folders


def test_a_folder_is_opened_with_the_system_browser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launched: list[list[str]] = []
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(subprocess, "Popen", lambda args, **_: launched.append(args))
    folders.open_folder(tmp_path)
    assert launched == [["xdg-open", str(tmp_path)]]


@pytest.mark.parametrize("kind", ["file", "missing", "link"])
def test_only_a_real_folder_is_ever_opened(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launched: list[object] = []
    monkeypatch.setattr(subprocess, "Popen", lambda args, **_: launched.append(args))
    target = tmp_path / "x"
    if kind == "file":
        target.write_text("x")
    elif kind == "link":
        (tmp_path / "real").mkdir()
        target.symlink_to(tmp_path / "real")
    with pytest.raises(ValueError):
        folders.open_folder(target)
    assert launched == []


def test_a_relative_path_is_never_opened(monkeypatch: pytest.MonkeyPatch) -> None:
    launched: list[object] = []
    monkeypatch.setattr(subprocess, "Popen", lambda args, **_: launched.append(args))
    with pytest.raises(ValueError):  # "-a" would reach "open" or "xdg-open" as an option
        folders.open_folder(Path("-a"))
    assert launched == []
