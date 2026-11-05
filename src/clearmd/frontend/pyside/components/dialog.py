"""A dialog in ClearMD's look (ADR-0027): modal, over the window, a body and a row of actions at
the foot; Esc closes it (Qt's own reject)."""

from collections.abc import Callable

from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from clearmd.frontend.design.metrics import SPACE


class Dialog(QDialog):
    """A body and a row of actions at the foot; ``on_close`` once, however it is closed."""

    def __init__(
        self, parent: QWidget, *, title: str, on_close: Callable[[], None], width: int = 560
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(width)
        self._on_close = on_close
        self._closed = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(3 * SPACE, 3 * SPACE, 3 * SPACE, 3 * SPACE)
        outer.setSpacing(3 * SPACE)
        self.body = QVBoxLayout()
        self.body.setSpacing(0)
        outer.addLayout(self.body, 1)
        self.foot = QHBoxLayout()
        self.foot.setSpacing(SPACE)
        outer.addLayout(self.foot)
        self.finished.connect(lambda _result: self._finish())

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 -- Qt's name
        """Tall enough for its wrapped lines at the width it opens with: Qt sizes a window from
        the layout's hint, which does not know where the text will wrap."""
        layout = self.layout()
        if layout is not None:
            needed = layout.totalHeightForWidth(self.width())
            if needed > self.height():
                self.resize(self.width(), needed)
        super().showEvent(event)

    def _finish(self) -> None:
        if not self._closed:
            self._closed = True
            self._on_close()

    def close_dialog(self) -> None:
        self.done(QDialog.DialogCode.Accepted)

    def default(self, widget: QPushButton) -> None:
        widget.setDefault(True)
        widget.setAutoDefault(True)
