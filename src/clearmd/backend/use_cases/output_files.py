"""Write inside ClearMD_Output so that nothing planted there can redirect a write.

The folder that receives ClearMD_Output may come from an archive the user extracted, so links can be
waiting inside it (security review of feature 001): ``OutputMD/report.md.clearmd-tmp -> ~/.bashrc``.
Every folder from the output root down is checked without following links, temporary files get
a fresh random name created exclusively, and ``os.replace`` swaps a planted link instead of
following it.
"""

import os
import stat
import tempfile
from pathlib import Path

from clearmd.backend.schemas.formats import RESULTS_DIR_NAME, TEMP_SUFFIX

# The process umask, read once at import (single-threaded then): results get normal permissions.
_UMASK = os.umask(0)
os.umask(_UMASK)
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class UnsafeOutput(OSError):
    """A link, junction or file sits where ClearMD needs a real folder."""


def _is_link(status: os.stat_result) -> bool:
    attributes = getattr(status, "st_file_attributes", 0)
    return stat.S_ISLNK(status.st_mode) or bool(attributes & _REPARSE_POINT)


def _real_folder(path: Path) -> None:
    """Create ``path`` or accept it only if it is a real folder (never a link or a file)."""
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        os.mkdir(path)
        status = os.lstat(path)
    if _is_link(status) or not stat.S_ISDIR(status.st_mode):
        raise UnsafeOutput(f"not a real folder: {path}")


def prepare_root(root: Path) -> None:
    """``ClearMD_Output`` and its ``OutputMD``, as real folders (the parent may be created)."""
    root.parent.mkdir(parents=True, exist_ok=True)
    _real_folder(root)
    _real_folder(root / RESULTS_DIR_NAME)


def _real_folders_down_to(folder: Path, inside: Path) -> None:
    _real_folder(inside)
    current = inside
    for part in folder.relative_to(inside).parts:
        current = current / part
        _real_folder(current)


def atomic_write(target: Path, text: str, *, inside: Path) -> None:
    """Write UTF-8 with LF endings at ``target`` (within ``inside``); never half-written."""
    _real_folders_down_to(target.parent, inside)
    descriptor, temporary = tempfile.mkstemp(prefix=".", suffix=TEMP_SUFFIX, dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(text.replace("\r\n", "\n").encode("utf-8"))
        os.chmod(temporary, 0o666 & ~_UMASK)  # mkstemp creates 0600; results are normal files
        os.replace(temporary, target)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def sweep_temporary_files(root: Path) -> None:
    """Remove temporary files left by a power cut or a forced stop (never follows links)."""
    results = root / RESULTS_DIR_NAME
    for folder in (root, results):
        if not folder.is_dir() or folder.is_symlink():
            return
    for path in [*root.glob(f"*{TEMP_SUFFIX}"), *results.rglob(f"*{TEMP_SUFFIX}")]:
        if not path.is_symlink() and path.is_file():
            path.unlink(missing_ok=True)


def read_regular_file(path: Path) -> str | None:
    """The text of ``path`` if it is a regular file (not a link); ``None`` if it does not exist."""
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return None
    if _is_link(status) or not stat.S_ISREG(status.st_mode):
        raise UnsafeOutput(f"not a regular file: {path}")
    return path.read_text(encoding="utf-8")
