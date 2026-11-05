"""The Choose step's output half: where the results go, the summary's format and the images'
choice. It adds its card to the step's own layout, so the arrangement stays the step's."""

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
from clearmd.frontend.pyside.components.primitives import button, card, label, radio_button


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
    ) -> None:
        output, output_layout = card()
        heading = QHBoxLayout()
        title = label("strong")
        text(title, "gui.main.output_title")
        heading.addWidget(title)
        heading.addStretch(1)
        images_title = label("strong")
        text(images_title, "gui.main.images_title")
        heading.addWidget(images_title)
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

        summary = QHBoxLayout()
        summary_title = label("strong")
        text(summary_title, "gui.main.summary_title")
        summary.addWidget(summary_title)
        self._summary = QButtonGroup(parent)
        self.summary_md = radio_button(self._summary, lambda: on_summary("markdown"))
        self.summary_pdf = radio_button(self._summary, lambda: on_summary("markdown_pdf"))
        text(self.summary_md, "gui.main.summary_md")
        text(self.summary_pdf, "gui.main.summary_pdf")
        for radio in (self.summary_md, self.summary_pdf):
            summary.addSpacing(GAP)
            summary.addWidget(radio)
        summary.addStretch(1)
        output_layout.addLayout(summary)
        layout.addWidget(output)
        self.choice_buttons = (
            self.next_to,
            self.in_folder,
            self.pick,
            self.summary_md,
            self.summary_pdf,
            self.images_omit,
            self.images_folder,
        )
