"""The Choose step's output half: where the results go, the summary's format and the images'
choice, in one card; for Split, How to Split in place of the images (feature 023); for Merge,
How to Merge (feature 026)."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.flet.components.merge_block import MergeBlock
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
        self._beside = ft.Row(spacing=GAP)  # Split's and Merge's summary, in the images' place
        heading = ft.Row(
            [title, stretch(), images_title, self.images.control, self._beside],
            spacing=SPACE,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.split = SplitBlock(wording, on_split=on_split)
        self.split.control.visible = False
        self.merge = MergeBlock(wording, on_split=on_split)

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
        self._summary_title = summary_title
        self._below = ft.Row([summary_title, self.summary.control], spacing=GAP)  # Convert's
        self.control = card(
            [self.split.control, self.merge.control, heading, choices, self.output_label,
             self._below]
        )  # fmt: skip
        self.choices = (self.images, self.mode, self.summary)

    def show(self, choice: OutputChoice) -> None:
        """The presenter's choice: for Split its cut and what it keeps, for Merge what it makes,
        instead of the images."""
        self.mode.set(choice.mode.value)
        self.output_label.value = choice.label
        self.summary.set(choice.summary_format)
        self.images.set(choice.images)
        self.split.control.visible = choice.tool is Tool.SPLIT
        self.merge.control.visible = choice.tool is Tool.MERGE
        converting = choice.tool is Tool.CONVERT
        self._images_title.visible = self.images.control.visible = converting
        # Split and Merge have their own block above: the summary goes up, on the heading's line,
        # so the list keeps its rows at 1080 x 720 (as Qt's; feature 032).
        summary = [self._summary_title, self.summary.control]
        self._below.controls, self._beside.controls = (summary, []) if converting else ([], summary)
        self._below.visible = converting
        self.split.show(choice)
        self.merge.show(choice)
