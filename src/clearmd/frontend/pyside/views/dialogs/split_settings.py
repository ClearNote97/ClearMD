"""The settings dialog's Split a PDF group (feature 023, AC-10): the cut (into N parts or every N
pages, each with its number) and what to keep of the parts. The same values as step 1's How to
Split; Save writes them with the others."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.pyside.components.primitives import label
from clearmd.frontend.pyside.components.split_choice import number_box
from clearmd.i18n import Catalog

KEEPS = ("pdf", "markdown", "both")


class SplitSettings:
    """The group's rows, added to the dialog's ``rows``; ``load`` and ``chosen`` as the dialog's."""

    def __init__(self, rows: QVBoxLayout, catalog: Catalog, control_width: int) -> None:
        text = catalog.text
        row = QHBoxLayout()
        row.setSpacing(GAP)
        cell = QWidget()
        cell_layout = QVBoxLayout(cell)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setSpacing(0)
        cell_layout.addWidget(label("strong", text("gui.settings.split")))
        cell_layout.addWidget(label("muted", text("gui.settings.split_help"), wrap=True))
        cell_layout.addStretch(1)  # the name and its line together, at the top of the group
        row.addWidget(cell, 1)

        holder = QWidget()  # the dialog's column of controls
        holder.setFixedWidth(control_width)
        grid = QGridLayout(holder)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(SPACE)
        grid.setVerticalSpacing(SPACE)
        self._cut = QButtonGroup(holder)
        self.by_parts = QRadioButton(text("gui.settings.split_parts"))
        self.by_pages = QRadioButton(text("gui.settings.split_pages"))
        self.parts = number_box("split_parts", lambda _value: None)
        self.pages = number_box("split_pages", lambda _value: None)
        for line, (radio, box) in enumerate(
            ((self.by_parts, self.parts), (self.by_pages, self.pages))
        ):
            self._cut.addButton(radio)
            box.setAccessibleName(radio.text())
            grid.addWidget(radio, line, 0)
            grid.addWidget(box, line, 1)
        self.keep = QComboBox()
        self.keep.addItems([text(f"gui.split.keep_{value}") for value in KEEPS])
        self.keep.setAccessibleName(text("gui.settings.split_keep"))
        keep_name = label("strong", text("gui.settings.split_keep"))
        keep_name.setBuddy(self.keep)
        grid.addWidget(keep_name, 2, 0)
        grid.addWidget(self.keep, 3, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        row.addWidget(holder, 0, Qt.AlignmentFlag.AlignVCenter)
        rows.addLayout(row)

    def load(self, settings: Settings) -> None:
        (self.by_pages if settings.split_cut == "pages" else self.by_parts).setChecked(True)
        self.parts.setValue(settings.split_parts)
        self.pages.setValue(settings.split_pages)
        self.keep.setCurrentIndex(KEEPS.index(settings.split_keep))

    def chosen(self) -> dict[str, object]:
        for box in (self.parts, self.pages):
            box.interpretText()  # a number still being typed counts
        return {
            "split_cut": "pages" if self.by_pages.isChecked() else "parts",
            "split_parts": self.parts.value(),
            "split_pages": self.pages.value(),
            "split_keep": KEEPS[self.keep.currentIndex()],
        }
