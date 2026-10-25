"""Helpers shared by every test: the network guard and the paths of the fixtures."""

import shutil
import socket
from pathlib import Path
from typing import Any

DOCUMENTS_DIR = Path(__file__).parent.parent / "fixtures" / "documents"


class NetworkBlockedError(RuntimeError):
    """Raised when code under test tries to open a network connection (ADR-0005)."""


def blocked(*args: Any, **kwargs: Any) -> Any:
    raise NetworkBlockedError(f"network access is forbidden in tests (ADR-0005): {args!r}")


def install_network_guard() -> None:
    """Make every outgoing connection fail in this process (also used inside worker processes)."""
    socket.socket.connect = blocked  # type: ignore[method-assign]
    socket.socket.connect_ex = blocked  # type: ignore[method-assign]
    socket.create_connection = blocked


def put(folder: Path, name: str, as_name: str | None = None) -> Path:
    """Copy fixture ``name`` into ``folder`` (as ``as_name``) and return the copy."""
    target = folder / (as_name or name)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DOCUMENTS_DIR / name, target)
    return target
