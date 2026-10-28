"""Shared fixtures: no network (ADR-0005, AC-39), an isolated settings folder per test, and one
display for every GUI test of the session."""

import socket
from collections.abc import Iterator
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR, blocked
from support.display import virtual_display


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


@pytest.fixture(autouse=True)
def _isolated_settings(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The user's real settings.toml never affects a test, and no test writes it. platformdirs
    # ignores XDG_CONFIG_HOME on Windows and macOS: ClearMD's own variable works everywhere, and
    # reaches the CLI processes some tests start.
    config = tmp_path_factory.mktemp("config")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config))
    monkeypatch.setenv("CLEARMD_CONFIG_DIR", str(config / "ClearMD"))


@pytest.fixture
def documents_dir() -> Path:
    return DOCUMENTS_DIR


@pytest.fixture(scope="session")
def display() -> Iterator[str]:
    """One display for the whole run: a virtual one stopped while Tk still holds a connection to
    it ends the process (Xlib), so it lives until the last GUI test."""
    with virtual_display() as name:
        if name is None:
            pytest.skip("no display and no Xvfb: GUI tests need one")
        yield name
