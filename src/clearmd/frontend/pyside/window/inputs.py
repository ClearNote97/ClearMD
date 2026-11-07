"""What the user does without a pointer on a button: Enter, Ctrl+1..4, Delete, dropped files."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QAbstractSpinBox, QApplication, QPushButton, QTreeWidget, QWidget

from clearmd.frontend.presenter import Action, Presenter
from clearmd.frontend.presenter.state import STEPS
from clearmd.frontend.pyside.window.shown import Shown


class Inputs:
    def __init__(
        self,
        window: QWidget,
        presenter: Presenter,
        shown: Shown,
        press_primary: Callable[[], None],
        tree: QTreeWidget,
        remove: QPushButton,
    ) -> None:
        self._window = window
        self._presenter = presenter
        self._shown = shown
        self._press_primary = press_primary
        self._tree = tree
        self._remove = remove

    def bind(self) -> None:
        for number in range(1, len(STEPS) + 1):  # the rail by keyboard
            shortcut = QShortcut(QKeySequence(f"Ctrl+{number}"), self._window)
            shortcut.activated.connect(lambda n=number: self._presenter.go_to(n))
        for key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            enter = QShortcut(QKeySequence(key), self._window)
            enter.setAutoRepeat(False)  # held down: one press, whatever the page (F-1)
            enter.activated.connect(self._enter)
        delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self._tree)
        delete.setContext(Qt.ShortcutContext.WidgetShortcut)
        delete.activated.connect(self._remove.click)

    def _enter(self) -> None:
        """Enter presses the page's primary action; on a start tile it opens that tile, in a number
        box it is the number done (feature 023)."""
        focused = QApplication.focusWidget()
        if isinstance(focused, QAbstractSpinBox):
            focused.interpretText()
        elif isinstance(focused, QPushButton) and focused.objectName() == "tile":
            focused.click()
        else:
            self._press_primary()

    def drag_enter(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and self._shown.allows(Action.ADD):
            event.acceptProposedAction()

    def dropped(self, event: QDropEvent) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        if paths and self._shown.allows(Action.ADD):
            event.acceptProposedAction()
            self._presenter.add_paths(paths)
