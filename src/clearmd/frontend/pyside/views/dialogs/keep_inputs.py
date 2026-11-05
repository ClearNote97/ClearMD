"""The "Convert more" dialog: keep the chosen files, or start empty (asked every time, 007)."""

from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.components.primitives import button, label
from clearmd.i18n import Catalog


class KeepInputsDialog(Dialog):
    """ "Convert more": keep the chosen files, or start empty (asked every time, feature 007)."""

    def __init__(
        self,
        parent: QWidget,
        catalog: Catalog,
        *,
        on_answer: Callable[[bool], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(parent, title=catalog.text("gui.more.title"), on_close=on_close, width=480)
        self._on_answer = on_answer
        self.body.addWidget(label("strong", catalog.text("gui.more.question"), wrap=True))
        self.body.addSpacing(SPACE)
        self.body.addWidget(label("muted", catalog.text("gui.more.explain"), wrap=True))
        self.foot.addStretch(1)
        self.clear = button("", lambda: self.answer(False))
        self.clear.setText(catalog.text("gui.more.clear"))
        self.foot.addWidget(self.clear)
        self.keep = button("primary", lambda: self.answer(True))
        self.keep.setText(catalog.text("gui.more.keep"))
        self.default(self.keep)
        self.foot.addWidget(self.keep)

    def answer(self, keep: bool) -> None:
        self.close_dialog()
        self._on_answer(keep)
