"""The QApplication. A module of its own: the one place that knows the toolkit's start-up (one
application per process, its name, icon and font)."""

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from clearmd.frontend.design.typography import BODY
from clearmd.frontend.pyside.visuals.images import app_icon


def application() -> QApplication:
    """The one QApplication of the process, made once; its font is the system's at 14 px."""
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        return existing
    app = QApplication(sys.argv[:1])
    app.setApplicationName("ClearMD")
    app.setWindowIcon(app_icon())
    font = QFont(app.font())
    font.setPixelSize(BODY)
    app.setFont(font)
    return app
