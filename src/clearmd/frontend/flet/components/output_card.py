"""The Choose step's output half: where the results go, the summary's format and the images'
choice, in one card; for Split, How to Split in place of the images (feature 023)."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.flet.components.primitives import (
    Choice,
    Wording,
    button,
    card,
    label,
    stretch,
)
from clearmd.frontend.flet.components.split_block import SplitBlock
from clearmd.frontend.presenter.models import OutputChoice, OutputMode
from clearmd.frontend.presenter.state import Tool


class OutputCard:
    """The output choice (next to the originals, in a folder), the summary's format, the images."""

    def __init__(
        self,
        wording: Wording,
        *,
        on_mode: Callable[[str], None],
        on_pick_folder: Callable[[], None],
        on_summary: Callable[[str], None],
        on_images: Callable[[str], None],
        on_split: Callable[..., None],
    ) -> None:
        title, images_title, summary_title = label("strong"), label("strong"), label("strong")
        wording.add(title, "gui.main.output_title")
        wording.add(images_title, "gui.main.images_title")
        wording.add(summary_title, "gui.main.summary_title")
        self.images = Choice(("omit", "folder"), on_images, spacing=SPACE)
        wording.add(self.images.radios["omit"], "gui.main.images_omit")
        wording.add(self.images.radios["folder"], "gui.main.images_folder")
        self._images_title = images_title
        heading = ft.Row([title, stretch(), images_title, self.images.control], spacing=SPACE)
        self.split = SplitBlock(wording, on_split=on_split)
        self.split.control.visible = False

        self.mode = Choice((OutputMode.NEXT_TO.value, OutputMode.FOLDER.value), on_mode)
        wording.add(self.mode.radios[OutputMode.NEXT_TO.value], "gui.output.next_to")
        wording.add(self.mode.radios[OutputMode.FOLDER.value], "gui.main.in_folder")
        self.pick = button("", on_pick_folder)
        wording.add(self.pick, "gui.main.pick_folder")
        choices = ft.Row([self.mode.control, self.pick], spacing=SPACE)
        self.output_label = label("muted")

        self.summary = Choice(("markdown", "markdown_pdf", "pdf"), on_summary)
        wording.add(self.summary.radios["markdown"], "gui.main.summary_md")
        wording.add(self.summary.radios["markdown_pdf"], "gui.main.summary_pdf")
        wording.add(self.summary.radios["pdf"], "gui.main.summary_pdf_only")
        summary = ft.Row([summary_title, self.summary.control], spacing=GAP)
        self.control = card([self.split.control, heading, choices, self.output_label, summary])
        self.choices = (self.images, self.mode, self.summary)

    def show(self, choice: OutputChoice) -> None:
        """The presenter's choice: for Split, its cut and what it keeps instead of the images."""
        self.mode.set(choice.mode.value)
        self.output_label.value = choice.label
        self.summary.set(choice.summary_format)
        self.images.set(choice.images)
        splitting = choice.tool is Tool.SPLIT
        self.split.control.visible = splitting
        self._images_title.visible = self.images.control.visible = not splitting
        self.split.show(choice)
