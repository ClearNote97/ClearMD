"""The PySide6 GUI's entry: build the window and run it (ADR-0038)."""

import sys
from collections.abc import Sequence

from PySide6.QtCore import QTimer

import clearmd.frontend.launch as launch
from clearmd.frontend.pyside.window import toolkit
from clearmd.frontend.pyside.window.window import PySideApp


def main(argv: Sequence[str] | None = None) -> int:
    """``clearmd-pyside``: the window, until it is closed. ``--smoke`` opens it and closes it
    after a few seconds: CI checks that the executable starts (its data, its toolkit)."""
    import multiprocessing

    multiprocessing.freeze_support()  # a no-op unless running as a packaged executable
    arguments = sys.argv[1:] if argv is None else list(argv)
    app = toolkit.application()
    window = PySideApp(application=app)
    window.start()
    if launch.is_smoke(arguments):
        QTimer.singleShot(launch.SMOKE_SECONDS * 1000, window.close)
    return app.exec()
