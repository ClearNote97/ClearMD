"""The "What Next?" dialog on Results (features 007, 032): keep the chosen files, start empty, or
go back Home to choose another tool (asked every time)."""

from collections.abc import Callable

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.components.primitives import button, gap, label, stretch
from clearmd.frontend.flet.layout.units import QUESTION_WIDTH
from clearmd.i18n import Catalog

ANSWERS = ("keep", "clear", "home")  # Presenter.what_next's


class KeepInputsDialog(Dialog):
    """ "What Next?": Go Back Home on the left, Start Empty and Keep Them (the default) on the
    right; each answer goes to ``on_answer`` as ``"home"``, ``"clear"`` or ``"keep"``."""

    def __init__(
        self,
        catalog: Catalog,
        *,
        on_answer: Callable[[str], None],
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
        self.home = button("", lambda: self.answer("home"), catalog.text("gui.more.home"))
        self.clear = button("", lambda: self.answer("clear"), catalog.text("gui.more.clear"))
        self.keep = button("primary", lambda: self.answer("keep"), catalog.text("gui.more.keep"))
        self.default(lambda: self.answer("keep"))
        self.foot.controls.extend([self.home, stretch(), self.clear, self.keep])

    def answer(self, choice: str) -> None:
        self.close_dialog()
        self._on_answer(choice)
