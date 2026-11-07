"""The settings dialog's Split group (features 023, 024): the cut (into N parts, every N pages or
parts of about N words, each with its number) and what to keep of the parts. The same values as
step 1's How to Split; Save writes them with the others."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.pyside.components.primitives import label
from clearmd.frontend.pyside.components.split_choice import number_box
from clearmd.i18n import Catalog

KEEPS = ("pdf", "markdown", "both")
CUTS = ("parts", "pages", "words")  # the settings split_<cut>, named gui.settings.split_<cut>
GROUP_EXTRA = 8 * SPACE  # "Parts of about N words" and its seven digits


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

        holder = QWidget()  # the dialog's column of controls, wider: a cut's name and its number
        holder.setFixedWidth(control_width + GROUP_EXTRA)
        grid = QGridLayout(holder)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(SPACE)
        grid.setVerticalSpacing(SPACE)
        self._cut = QButtonGroup(holder)
        self.cuts: dict[str, QRadioButton] = {}
        self.boxes: dict[str, QSpinBox] = {}
        for line, cut in enumerate(CUTS):
            radio = QRadioButton(text(f"gui.settings.split_{cut}"))
            box = number_box(f"split_{cut}", lambda _value: None)
            self._cut.addButton(radio)
            box.setAccessibleName(radio.text())
            grid.addWidget(radio, line, 0)
            grid.addWidget(box, line, 1, Qt.AlignmentFlag.AlignRight)
            self.cuts[cut], self.boxes[cut] = radio, box
        self.by_parts, self.by_pages, self.by_words = self.cuts.values()
        self.parts, self.pages, self.words = self.boxes.values()
        keep_line = len(CUTS)
        self.keep = QComboBox()
        self.keep.addItems([text(f"gui.split.keep_{value}") for value in KEEPS])
        self.keep.setAccessibleName(text("gui.settings.split_keep"))
        keep_name = label("strong", text("gui.settings.split_keep"))
        keep_name.setBuddy(self.keep)
        keep_name.setFixedWidth(control_width)  # over the choice, flush with it
        grid.addWidget(keep_name, keep_line, 0, 1, 2, Qt.AlignmentFlag.AlignRight)
        self.keep.setFixedWidth(control_width)  # as wide as the other settings' choices
        grid.addWidget(self.keep, keep_line + 1, 0, 1, 2, Qt.AlignmentFlag.AlignRight)
        grid.setColumnStretch(0, 1)
        row.addWidget(holder, 0, Qt.AlignmentFlag.AlignVCenter)
        rows.addLayout(row)

    def load(self, settings: Settings) -> None:
        self.cuts.get(settings.split_cut, self.by_parts).setChecked(True)
        for cut, box in self.boxes.items():
            box.setValue(getattr(settings, f"split_{cut}"))
        self.keep.setCurrentIndex(KEEPS.index(settings.split_keep))

    def chosen(self) -> dict[str, object]:
        chosen: dict[str, object] = {
            "split_cut": next((c for c, r in self.cuts.items() if r.isChecked()), "parts"),
            "split_keep": KEEPS[self.keep.currentIndex()],
        }
        for cut, box in self.boxes.items():
            box.interpretText()  # a number still being typed counts
            chosen[f"split_{cut}"] = box.value()
        return chosen
