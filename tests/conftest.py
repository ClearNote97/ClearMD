"""Shared fixtures: no network (ADR-0005, AC-39) and an isolated settings folder per test."""

import socket
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR, blocked


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


@pytest.fixture(autouse=True)
def _isolated_settings(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The user's real settings.toml never affects a test, and no test writes it.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


@pytest.fixture
def documents_dir() -> Path:
    return DOCUMENTS_DIR
