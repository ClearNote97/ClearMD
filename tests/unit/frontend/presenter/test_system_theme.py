"""The system's light or dark theme, without a dependency (005, T03, AC-16)."""

import subprocess
import sys
from types import SimpleNamespace

import pytest

from clearmd.frontend.presenter import system_theme


def answering(stdout: str):  # type: ignore[no-untyped-def]
    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(stdout=stdout)

    return run


@pytest.mark.parametrize(
    ("printed", "theme"), [("'prefer-dark'\n", "dark"), ("'default'\n", "light")]
)
def test_linux_reads_gnomes_color_scheme(
    printed: str, theme: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("GTK_THEME", raising=False)
    monkeypatch.setattr(subprocess, "run", answering(printed))
    assert system_theme.detect_system_theme() == theme


def test_linux_falls_back_to_gtk_theme(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(subprocess, "run", answering(""))
    monkeypatch.setenv("GTK_THEME", "Adwaita:dark")
    assert system_theme.detect_system_theme() == "dark"


@pytest.mark.parametrize(("printed", "theme"), [("Dark\n", "dark"), ("", "light")])
def test_macos_reads_the_interface_style(
    printed: str, theme: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(subprocess, "run", answering(printed))
    assert system_theme.detect_system_theme() == theme


@pytest.mark.parametrize(
    "problem", [FileNotFoundError("gsettings"), subprocess.TimeoutExpired("x", 1)]
)
def test_anything_unknown_is_light(problem: Exception, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("GTK_THEME", raising=False)

    def fails(command: list[str], **kwargs: object) -> None:
        raise problem

    monkeypatch.setattr(subprocess, "run", fails)
    assert system_theme.detect_system_theme() == "light"


@pytest.mark.parametrize(("value", "theme"), [(0, "dark"), (1, "light")])
def test_windows_reads_the_registry(
    value: int, theme: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Key:
        def __enter__(self) -> "Key":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    fake = SimpleNamespace(
        HKEY_CURRENT_USER=1,
        OpenKey=lambda root, path: Key(),
        QueryValueEx=lambda key, name: (value, 4),
    )
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "winreg", fake)
    assert system_theme.detect_system_theme() == theme
