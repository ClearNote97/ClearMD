"""A display for GUI tests: the one the session has, or a virtual one (Xvfb) started for the run.

GUI tests use the ``display`` fixture (tests/conftest.py); without a display and
without Xvfb they are skipped, never failed. The GUI is never shown from the container (ADR-0026).
"""

import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def virtual_display(width: int = 1280, height: int = 800) -> Iterator[str | None]:
    """The display to use: ``$DISPLAY``, or a new Xvfb one (stopped at the end); ``None`` if
    there is neither. Windows and macOS need none: Tk draws on the desktop (CI, feature 006)."""
    if sys.platform in {"win32", "darwin"}:
        yield "native"
        return
    if os.environ.get("DISPLAY"):
        yield os.environ["DISPLAY"]
        return
    xvfb = shutil.which("Xvfb")
    if xvfb is None:
        yield None
        return
    for number in range(90, 140):
        if os.path.exists(f"/tmp/.X11-unix/X{number}") or os.path.exists(f"/tmp/.X{number}-lock"):
            continue
        name = f":{number}"
        process = subprocess.Popen(
            [xvfb, name, "-screen", "0", f"{width}x{height}x24", "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not os.path.exists(f"/tmp/.X11-unix/X{number}"):
            if process.poll() is not None:
                break
            time.sleep(0.05)
        if process.poll() is None:
            os.environ["DISPLAY"] = name
            try:
                yield name
            finally:
                os.environ.pop("DISPLAY", None)
                process.terminate()
                process.wait(timeout=10)
            return
    yield None
