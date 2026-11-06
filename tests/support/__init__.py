"""Helpers shared by every test: the network guard and the paths of the fixtures."""

import _socket
import shutil
import socket
import sys
from pathlib import Path
from typing import Any

DOCUMENTS_DIR = Path(__file__).parent.parent / "fixtures" / "documents"
TEX_DIR = Path(__file__).parent.parent / "fixtures" / "tex"
ODT_DIR = Path(__file__).parent.parent / "fixtures" / "odt"
HTML_DIR = Path(__file__).parent.parent / "fixtures" / "html"

WINDOWS = sys.platform == "win32"


class NetworkBlockedError(RuntimeError):
    """Raised when code under test tries to open a network connection (ADR-0005)."""


def blocked(*args: Any, **kwargs: Any) -> Any:
    raise NetworkBlockedError(f"network access is forbidden in tests (ADR-0005): {args!r}")


# The real ones, from where the guard never writes: this module may be imported twice (pytest's
# importlib mode), after the guard has replaced ``socket.socket.connect`` and ``socketpair``.
_CONNECT = _socket.socket.connect
_SOCKETPAIR = getattr(socket, "_fallback_socketpair", socket.socketpair)


def _local_pair(*args: Any, **kwargs: Any) -> tuple[socket.socket, socket.socket]:
    """A pipe inside this process, as asyncio's event loop makes one (flet, 018). On Windows,
    Python builds it by connecting to a listener of its own on 127.0.0.1: that is not the network,
    so only that connection goes through, and the guard is back before the pair is returned."""
    socket.socket.connect = _CONNECT  # type: ignore[method-assign]
    try:
        return _SOCKETPAIR(*args, **kwargs)
    finally:
        socket.socket.connect = blocked  # type: ignore[method-assign]


def install_network_guard() -> None:
    """Make every outgoing connection fail in this process (also used inside worker processes)."""
    socket.socket.connect = blocked  # type: ignore[method-assign]
    socket.socket.connect_ex = blocked  # type: ignore[method-assign]
    socket.create_connection = blocked
    if WINDOWS:
        socket.socketpair = _local_pair


def put(folder: Path, name: str, as_name: str | None = None) -> Path:
    """Copy fixture ``name`` into ``folder`` (as ``as_name``) and return the copy."""
    target = folder / (as_name or name)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DOCUMENTS_DIR / name, target)
    return target
