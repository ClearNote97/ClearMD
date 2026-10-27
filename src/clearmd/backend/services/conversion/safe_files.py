"""Open untrusted sources safely: never through a link, only regular files.

From the security review of feature 001."""

import os
import stat
from pathlib import Path
from typing import BinaryIO

_NO_FOLLOW = getattr(os, "O_NOFOLLOW", 0)
_BINARY = getattr(os, "O_BINARY", 0)
_NON_BLOCKING = getattr(os, "O_NONBLOCK", 0)  # a FIFO opens at once (and is then refused)


class NotARegularFile(OSError):
    """A link, a folder, a device: never read as a document."""


def open_regular_file(path: Path) -> BinaryIO:
    """Open ``path`` for reading without following a symbolic link (where the OS allows it)."""
    descriptor = os.open(path, os.O_RDONLY | _NO_FOLLOW | _BINARY | _NON_BLOCKING)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode) or path.is_symlink():
        os.close(descriptor)
        raise NotARegularFile(f"not a regular file: {path}")
    return os.fdopen(descriptor, "rb")


def read_regular_file(path: Path, max_bytes: int) -> bytes:
    """The bytes of a regular file, refusing one larger than ``max_bytes``."""
    with open_regular_file(path) as stream:
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise NotARegularFile(f"larger than {max_bytes} bytes: {path}")
    return data
