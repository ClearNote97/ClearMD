"""Closing the window while a task runs (feature 038, audit v2 F1-01): asked once, and only then.
Keep Working (the default, and Esc) leaves the task going; Close cancels it and closes."""

from collections.abc import Callable

from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.components.primitives import button, label, stretch
from clearmd.frontend.flet.layout.units import QUESTION_WIDTH
from clearmd.i18n import Catalog


class CloseQuestionDialog(Dialog):
    """``keep`` (the default) only closes the question; ``close`` calls ``on_close_window``."""

    def __init__(
        self,
        catalog: Catalog,
        *,
        on_close_window: Callable[[], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            title=catalog.text("gui.close.title"), on_close=on_close, width=QUESTION_WIDTH
        )
        self._on_close_window = on_close_window
        self.body.controls.append(label("onPage", catalog.text("gui.close.body")))
        self.close = button("", self.close_window, catalog.text("gui.close.close"))
        self.keep = button("primary", self.close_dialog, catalog.text("gui.close.keep"))
        self.default(self.close_dialog)  # Enter, as Esc: the task goes on
        self.foot.controls.extend([stretch(), self.close, self.keep])

    def close_window(self) -> None:
        self.close_dialog()
        self._on_close_window()
