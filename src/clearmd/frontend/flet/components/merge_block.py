"""How to Merge (feature 026): into one Markdown or one PDF, and the line that says each document
keeps its content whole, in the list's order. Step 1 of Merge shows it in the results card, in
place of the images' choice (as Split's block)."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import HALF, SPACE
from clearmd.frontend.flet.components.primitives import Choice, Wording, label
from clearmd.frontend.presenter.models import OutputChoice

INTO = ("markdown", "pdf")


class MergeBlock:
    """The title, Into's two radio buttons (``on_split(into=...)``, the presenter's intent for a
    tool's choices) and the note."""

    def __init__(self, wording: Wording, *, on_split: Callable[..., None]) -> None:
        title, into_title = label("strong"), label("strong")
        wording.add(title, "gui.merge.title")
        wording.add(into_title, "gui.merge.into")
        self.into = Choice(INTO, lambda into: on_split(into=into), spacing=SPACE)
        for value in INTO:
            wording.add(self.into.radios[value], f"gui.merge.{value}")
            self.into.radios[value].visual_density = ft.VisualDensity.COMPACT  # as Split's
        into = ft.Row(
            [into_title, self.into.control],
            spacing=SPACE,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.note = label("muted")
        wording.add(self.note, "gui.merge.note")
        self.control = ft.Column([title, into, self.note], spacing=HALF, tight=True)
        self.control.visible = False

    def show(self, choice: OutputChoice) -> None:
        self.into.set(choice.merge_into)

    def set_disabled(self, disabled: bool) -> None:
        self.into.set_disabled(disabled)
