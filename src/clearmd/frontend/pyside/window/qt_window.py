"""The Qt widget that is the window: Qt's own event hooks, each one a forward to a callback.

A module of its own: Qt delivers close, resize and drag events only as overrides on a QWidget
subclass. This class is that subclass and nothing more; the logic is in the callbacks that
``PySideApp`` installs, so the window class itself stays a plain object.
"""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QResizeEvent
from PySide6.QtWidgets import QWidget

from clearmd.frontend.design.metrics import MIN_HEIGHT, MIN_WIDTH, START_HEIGHT, START_WIDTH
from clearmd.frontend.pyside.widgets import app_icon


class MainWindow(QWidget):
    """The window's widget; the hooks start as no-ops and the app sets them."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("window")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(START_WIDTH, START_HEIGHT)
        self.setAcceptDrops(True)
        self.on_close: Callable[[QCloseEvent], None] = lambda event: event.accept()
        self.on_resize: Callable[[int, int], None] = lambda width, height: None
        self.on_drag_enter: Callable[[QDragEnterEvent], None] = lambda event: None
        self.on_drop: Callable[[QDropEvent], None] = lambda event: None

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 -- Qt's name
        self.on_close(event)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 -- Qt's name
        super().resizeEvent(event)
        self.on_resize(self.width(), self.height())

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 -- Qt's name
        self.on_drag_enter(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 -- Qt's name
        self.on_drop(event)
