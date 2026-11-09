"""Closing the window during a task (audit v2, F1-01): asked once, and only then. Keep Working is
the default and Esc's answer; Close goes on to cancel the task and wait for its summary."""

from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.components.primitives import button, label
from clearmd.i18n import Catalog


class ConfirmCloseDialog(Dialog):
    """``keep`` (the default) only closes the question; ``close`` calls ``on_close_window``."""

    def __init__(
        self,
        parent: QWidget,
        catalog: Catalog,
        *,
        on_close_window: Callable[[], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(parent, title=catalog.text("gui.close.title"), on_close=on_close)
        self._on_close_window = on_close_window
        self.body.addWidget(label("onPage", catalog.text("gui.close.body"), wrap=True))
        self.foot.addStretch(1)
        self.close_window = button("", self.confirm)
        self.close_window.setText(catalog.text("gui.close.close"))
        self.foot.addWidget(self.close_window)
        self.keep = button("primary", self.reject)
        self.keep.setText(catalog.text("gui.close.keep"))
        self.default(self.keep)
        self.foot.addWidget(self.keep)

    def confirm(self) -> None:
        self.close_dialog()
        self._on_close_window()
