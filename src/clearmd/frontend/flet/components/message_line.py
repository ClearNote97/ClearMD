"""The page's message line above the action bar, with "Copy Details" beside it after an unexpected
error (feature 036, D3: the technical line is only copied, never shown) or "Undo" after Clear All
(039, F1-03)."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.flet.components.primitives import button, label


class MessageLine:
    """``text`` (the message, taking no room without one) and ``details`` (a secondary button,
    shown only with a label). Clearing the message hides the button too."""

    def __init__(
        self, *, on_details: Callable[[], None], on_undo: Callable[[], None] = lambda: None
    ) -> None:
        self.text = label("message")
        self.details = button("", on_details)
        self.undo = button("", on_undo)  # BUTTON_HEIGHT (44): a comfortable target
        self.control = ft.Row(
            [self.text, self.details, self.undo],
            spacing=SPACE,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.show("")

    def show(self, text: str) -> None:
        """A message, or none: without one the line takes no room and the button goes."""
        self.text.value = text
        self.text.visible = bool(text)
        if not text:
            self.show_details(None)
            self.undo.visible = False
        self._fit()

    def show_details(self, text: str | None) -> None:
        """The button with ``text``, or no button (``None``)."""
        self.details.content = text or ""
        self.details.visible = text is not None
        self._fit()

    def show_undo(self, text: str | None, label_text: str) -> None:
        """After Clear All: ``text`` with "Undo" (``label_text``) beside it; ``None`` hides both."""
        if text is None:
            if self.undo.visible:
                self.undo.visible = False
                self.show("")
            return
        self.show(text)
        self.undo.content = label_text
        self.undo.visible = True
        self._fit()

    def _fit(self) -> None:
        """The line takes room only with something on it."""
        self.control.visible = bool(self.text.value) or bool(
            self.details.visible or self.undo.visible
        )
