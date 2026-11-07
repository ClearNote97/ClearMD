"""The bar at the foot of every page (ADR-0029): why the primary action is disabled, one secondary
action and the page's primary action."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.flet.components.primitives import button, label, restyle
from clearmd.frontend.presenter.models import Primary


class ActionBar:
    """Why the primary action is disabled, one secondary action (Back, Cancel or Convert more),
    the offer to split the large PDFs before it (Review, Results), and the page's primary
    action."""

    def __init__(self, *, on_primary: Callable[[], None], on_offer: Callable[[], None]) -> None:
        self.hint = label("hint", expand=True)
        self.hint.text_align = ft.TextAlign.RIGHT
        self.secondary = button("", self._secondary)
        self.secondary.visible = False
        self.strong = False  # the secondary drawn as prominent as the primary (Convert more)
        self.primary = button("primary", on_primary)
        self.offer = button("", on_offer)  # "Split the Large PDFs" (feature 025)
        self.offer.visible = False
        self.control = ft.Row(
            [self.hint, self.offer, self.secondary, self.primary],
            spacing=SPACE,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._command: Callable[[], None] | None = None

    def show(self, primary: Primary) -> None:
        self.primary.content = primary.label
        self.primary.disabled = not primary.enabled
        self.hint.value = primary.hint

    def show_secondary(
        self, text: str | None, command: Callable[[], None] | None = None, *, strong: bool = False
    ) -> None:
        if text is None or command is None:
            self.secondary.visible = False
            self._command = None
            return
        self._command = command
        self.secondary.content = text
        self.strong = strong
        restyle(self.secondary, "strong" if strong else "")
        self.secondary.visible = True

    def show_offer(self, text: str) -> None:
        """A second secondary action, before the other one: shown with a label only."""
        self.offer.content = text
        self.offer.visible = bool(text)

    def _secondary(self) -> None:
        if self._command is not None:
            self._command()
