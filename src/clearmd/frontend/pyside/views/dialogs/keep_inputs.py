"""Results' "What Next?" dialog (features 007, 032): keep the chosen files, start empty, or go
back Home to choose another tool (asked every time)."""

from collections.abc import Callable
from functools import partial

from PySide6.QtWidgets import QWidget

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.components.primitives import button, label
from clearmd.i18n import Catalog

ANSWERS = ("home", "clear", "keep")  # the presenter's what_next answers, in the foot's order


class KeepInputsDialog(Dialog):
    """ "What Next?": Go Back Home, Start Empty or Keep Them (the default); the answer goes to the
    presenter's ``what_next``."""

    def __init__(
        self,
        parent: QWidget,
        catalog: Catalog,
        *,
        on_answer: Callable[[str], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(parent, title=catalog.text("gui.more.title"), on_close=on_close, width=560)
        self._on_answer = on_answer
        self.body.addWidget(label("strong", catalog.text("gui.more.question"), wrap=True))
        self.body.addSpacing(SPACE)
        self.body.addWidget(label("muted", catalog.text("gui.more.explain"), wrap=True))
        self.buttons = {
            answer: button("primary" if answer == "keep" else "", partial(self.answer, answer))
            for answer in ANSWERS
        }
        self.home, self.clear, self.keep = (self.buttons[answer] for answer in ANSWERS)
        for answer, widget in self.buttons.items():
            widget.setText(catalog.text(f"gui.more.{answer}"))
            self.foot.addWidget(widget)
            if answer == "home":  # apart: it leaves the tool
                self.foot.addStretch(1)
        self.default(self.keep)

    def answer(self, answer: str) -> None:
        self.close_dialog()
        self._on_answer(answer)
