"""A dialog in ClearMD's look (ADR-0027): modal, over the window, a body and a row of actions at
the foot; Esc closes it (Qt's own reject). Never taller than the screen (audit v3, F3-01)."""

from collections.abc import Callable

from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from clearmd.frontend.design.metrics import SPACE

SCREEN_MARGIN = 6 * SPACE  # left free above and below a dialog: the title bar, a taskbar's edge


def screen_room(widget: QWidget) -> int:
    """The height a dialog may take on ``widget``'s screen (a function: tests set the screen)."""
    screen = widget.screen()
    return screen.availableGeometry().height() - SCREEN_MARGIN if screen else 10_000


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
        """Tall enough for its wrapped lines at the width it opens with (Qt sizes a window from
        the layout's hint, which does not know where the text will wrap), and never taller than
        the screen: a body that scrolls takes the difference."""
        layout = self.layout()
        room = screen_room(self)
        if layout is not None:
            needed = min(layout.totalHeightForWidth(self.width()), room)
            if needed > self.height():
                self.resize(self.width(), needed)
        if self.height() > room:
            self.resize(self.width(), room)
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
