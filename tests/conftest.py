"""Shared fixtures: no test may open a network connection (ADR-0005, AC-39)."""

import socket
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR, blocked


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


@pytest.fixture
def documents_dir() -> Path:
    return DOCUMENTS_DIR
