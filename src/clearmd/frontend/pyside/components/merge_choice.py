"""How to Merge (feature 026): into one Markdown or one PDF (PDF files only). Shown on step 1's
results card in place of the images, when the tool is Merge; in the order of the three windows:
the title, Into, the note. The choice goes to the presenter like Split's (``choose_split``)."""

from collections.abc import Callable
from functools import partial

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
from clearmd.frontend.pyside.components.primitives import label, radio_button

Text = Callable[[QLabel | QPushButton | QRadioButton, str], None]
INTO = ("markdown", "pdf")


class MergeChoice:
    """The block (``self.widget``) and its radios (``into`` by value)."""

    def __init__(
        self,
        parent: QWidget,
        *,
        text: Text,
        on_split: Callable[..., None],  # the presenter's choose_split, by keyword
    ) -> None:
        self.widget = QWidget()
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE)
        title = label("strong")
        text(title, "gui.merge.title")
        layout.addWidget(title)
        row = QHBoxLayout()
        into = label("strong")
        text(into, "gui.merge.into")
        row.addWidget(into)
        self._group = QButtonGroup(parent)
        self.into = {
            value: radio_button(self._group, partial(on_split, into=value)) for value in INTO
        }
        for value, radio in self.into.items():
            text(radio, f"gui.merge.{value}")
            row.addSpacing(GAP)
            row.addWidget(radio)
        row.addStretch(1)
        layout.addLayout(row)
        note = label("muted", wrap=True)
        text(note, "gui.merge.note")
        layout.addWidget(note)
        layout.addSpacing(SPACE)  # apart from the results' heading under it
        self.controls = tuple(self.into.values())

    def show(self, choice: OutputChoice) -> None:
        self.into.get(choice.merge_into, self.into["markdown"]).setChecked(True)
