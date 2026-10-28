"""Show a folder in the system's file browser, for every interface (moved from the CLI, 005)."""

import os
import subprocess
import sys
from pathlib import Path


def open_folder(path: Path) -> None:
    """Open ``path`` in the system file browser. Only a real folder given by its absolute path is
    ever opened: never a file, a link (symlink or junction) or anything that is not there
    (``ValueError``). Local only: no network (ADR-0005)."""
    if not path.is_absolute():  # a relative "-x" would reach the opener as an option
        raise ValueError(f"not an absolute path: {path}")
    if path.is_symlink() or path.is_junction() or not path.is_dir():
        raise ValueError(f"not a folder: {path}")
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]  # Windows only
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
