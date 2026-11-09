"""The page's message line above the action bar, and "Copy Details" beside it after an unexpected
error (feature 036, D3): the message is calm; the technical line is only copied, never shown."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.flet.components.primitives import button, label


class MessageLine:
    """``text`` (the message, taking no room without one) and ``details`` (a secondary button,
    shown only with a label). Clearing the message hides the button too."""

    def __init__(self, *, on_details: Callable[[], None]) -> None:
        self.text = label("message")
        self.details = button("", on_details)
        self.control = ft.Row(
            [self.text, self.details],
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
        self.control.visible = bool(text) or bool(self.details.visible)

    def show_details(self, text: str | None) -> None:
        """The button with ``text``, or no button (``None``)."""
        self.details.content = text or ""
        self.details.visible = text is not None
        self.control.visible = bool(self.text.value) or text is not None
