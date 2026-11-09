"""The Choose step's output half: where the results go, the summary's format and the images'
choice; for Split and Merge, their block in place of the images (features 023, 026). It adds its
card to the step's own layout, so the arrangement stays the step's."""

from collections.abc import Callable

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.presenter.models import OutputChoice
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside.components.merge_choice import MergeChoice
from clearmd.frontend.pyside.components.primitives import button, card, label, radio_button
from clearmd.frontend.pyside.components.split_choice import SplitChoice


class OutputCard:
    """The output choice (next to the originals, in a folder), the summary's format, the images."""

    def __init__(
        self,
        parent: QWidget,
        layout: QVBoxLayout,
        *,
        text: Callable[[QLabel | QPushButton | QRadioButton, str], None],
        on_next_to: Callable[[], None],
        on_pick_folder: Callable[[], None],
        on_summary: Callable[[str], None],
        on_images: Callable[[str], None],
        on_split: Callable[..., None],
    ) -> None:
        output, output_layout = card()
        self.split = SplitChoice(parent, text=text, on_split=on_split)
        self.split.widget.hide()
        output_layout.addWidget(self.split.widget)
        self.merge = MergeChoice(parent, text=text, on_split=on_split)
        self.merge.widget.hide()
        output_layout.addWidget(self.merge.widget)
        heading = QHBoxLayout()
        title = label("strong")
        text(title, "gui.main.output_title")
        heading.addWidget(title)
        heading.addStretch(1)
        self.images_title = label("strong")
        text(self.images_title, "gui.main.images_title")
        heading.addWidget(self.images_title)
        self._images = QButtonGroup(parent)
        self.images_omit = radio_button(self._images, lambda: on_images("omit"))
        self.images_folder = radio_button(self._images, lambda: on_images("folder"))
        text(self.images_omit, "gui.main.images_omit")
        text(self.images_folder, "gui.main.images_folder")
        heading.addSpacing(SPACE)
        heading.addWidget(self.images_omit)
        heading.addSpacing(SPACE)
        heading.addWidget(self.images_folder)
        output_layout.addLayout(heading)

        choices = QHBoxLayout()
        self._mode = QButtonGroup(parent)
        self.next_to = radio_button(self._mode, on_next_to)
        self.in_folder = radio_button(self._mode, on_pick_folder)
        text(self.next_to, "gui.output.next_to")
        text(self.in_folder, "gui.main.in_folder")
        self.pick = button("", on_pick_folder)
        text(self.pick, "gui.main.pick_folder")
        choices.addWidget(self.next_to)
        choices.addSpacing(GAP)
        choices.addWidget(self.in_folder)
        choices.addSpacing(SPACE)
        choices.addWidget(self.pick)
        choices.addStretch(1)
        output_layout.addLayout(choices)
        self.output_label = label("muted", wrap=True)
        output_layout.addWidget(self.output_label)

        # The summary keeps its own line for every tool, so its label is never cut (038).
        self._summary_row = QWidget()
        summary = QHBoxLayout(self._summary_row)
        summary.setContentsMargins(0, 0, 0, 0)
        summary.setSpacing(SPACE)
        self.summary_title = label("strong")
        text(self.summary_title, "gui.main.summary_title")
        summary.addWidget(self.summary_title)
        self._summary = QButtonGroup(parent)
        self.summary_md = radio_button(self._summary, lambda: on_summary("markdown"))
        self.summary_pdf = radio_button(self._summary, lambda: on_summary("markdown_pdf"))
        self.summary_pdf_only = radio_button(self._summary, lambda: on_summary("pdf"))
        text(self.summary_md, "gui.main.summary_md")
        text(self.summary_pdf, "gui.main.summary_pdf")
        text(self.summary_pdf_only, "gui.main.summary_pdf_only")
        for radio in (self.summary_md, self.summary_pdf, self.summary_pdf_only):
            summary.addSpacing(GAP)
            summary.addWidget(radio)
        self._summary_line = QHBoxLayout()
        self._summary_line.addWidget(self._summary_row)
        self._summary_line.addStretch(1)
        output_layout.addLayout(self._summary_line)
        self.frame = output
        layout.addWidget(output)
        self.choice_buttons = (
            self.next_to,
            self.in_folder,
            self.pick,
            self.summary_md,
            self.summary_pdf,
            self.summary_pdf_only,
            self.images_omit,
            self.images_folder,
            *self.split.controls,
            *self.merge.controls,
        )

    def show_tool(self, choice: OutputChoice) -> None:
        """Split's or Merge's block in place of the images, with what the presenter keeps."""
        convert = choice.tool is Tool.CONVERT
        for widget in (self.images_title, self.images_omit, self.images_folder):
            widget.setVisible(convert)
        for tool, block in ((Tool.SPLIT, self.split), (Tool.MERGE, self.merge)):
            block.widget.setVisible(choice.tool is tool)
            block.show(choice)

    def hold(self, width: int) -> None:
        """Never shorter than its wrapped lines need at ``width``: Qt's box layout would squeeze
        it to its one-line minimum to grow the list (032, 800 px)."""
        layout = self.frame.layout()
        if layout is not None:
            self.frame.setMinimumHeight(layout.totalHeightForWidth(width))
