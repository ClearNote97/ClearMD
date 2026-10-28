"""Show a folder in the system's file browser, for every interface (moved from the CLI, 005)."""

import os
import subprocess
import sys
from pathlib import Path


def open_folder(path: Path) -> None:
    """Open ``path`` in the system file browser. Only a real folder is ever opened: never a file,
    a link or anything that is not there (``ValueError``). Local only: no network (ADR-0005)."""
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"not a folder: {path}")
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]  # Windows only
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
