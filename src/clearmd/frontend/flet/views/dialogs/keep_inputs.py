"""The "Convert more" dialog: keep the chosen files, or start empty (asked every time, 007)."""

from collections.abc import Callable

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.components.primitives import button, gap, label, stretch
from clearmd.frontend.flet.layout.units import QUESTION_WIDTH
from clearmd.i18n import Catalog


class KeepInputsDialog(Dialog):
    """ "Convert more": keep the chosen files, or start empty (asked every time, feature 007)."""

    def __init__(
        self,
        catalog: Catalog,
        *,
        on_answer: Callable[[bool], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            title=catalog.text("gui.more.title"), on_close=on_close, width=QUESTION_WIDTH
        )
        self._on_answer = on_answer
        self.body.controls.extend(
            [
                label("strong", catalog.text("gui.more.question")),
                gap(SPACE),
                label("muted", catalog.text("gui.more.explain")),
            ]
        )
        self.clear = button("", lambda: self.answer(False), catalog.text("gui.more.clear"))
        self.keep = button("primary", lambda: self.answer(True), catalog.text("gui.more.keep"))
        self.default(lambda: self.answer(True))
        self.foot.controls.extend([stretch(), self.clear, self.keep])

    def answer(self, keep: bool) -> None:
        self.close_dialog()
        self._on_answer(keep)
