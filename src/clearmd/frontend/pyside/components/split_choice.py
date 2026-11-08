"""How to Split (features 023, 024): into N parts, every N pages or parts of about N words, and
what to keep of the parts. Shown on step 1's results card in place of the images, when the tool is
Split; in the order of the three windows: the title with Keep, the cuts, the note and the hint. A
number is sent when it is done (Enter, leaving the box, the arrow keys), not on every key; the
presenter refuses one out of range and the box shows again what it keeps."""

from collections.abc import Callable
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from clearmd.backend.schemas.settings import RANGES
from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.presenter.models import OutputChoice
from clearmd.frontend.pyside.components.fold_row import FoldRow
from clearmd.frontend.pyside.components.primitives import label, radio_button

DIGIT_WIDTH = 9  # a digit at 14 px, with room
Text = Callable[[QLabel | QPushButton | QRadioButton, str], None]
# Each cut: its value, the setting of its number, its radio's words and the unit after the box.
CUTS = (
    ("parts", "split_parts", "gui.split.into", "gui.split.parts"),
    ("pages", "split_pages", "gui.split.every", "gui.split.pages"),
    ("words", "split_words", "gui.split.words", "gui.split.words_unit"),
)


def number_box(setting: str, on_value: Callable[[int], None]) -> QSpinBox:
    """A number without arrows (the arrow keys and the wheel still change it), in its range and
    as wide as its largest value. The arrows go in the style sheet: Qt's NoButtons leaves a styled
    box's text 1 px wide."""
    box = QSpinBox()
    low, high = RANGES[setting]
    box.setRange(low, high)
    box.setFixedWidth(max(8 * SPACE, len(str(high)) * DIGIT_WIDTH + 2 * SPACE))
    box.setAlignment(Qt.AlignmentFlag.AlignCenter)  # its arrows are hidden by the style sheet
    box.setKeyboardTracking(False)  # valueChanged once the number is done, not per key
    box.valueChanged.connect(on_value)
    return box


def _send_number(on_split: Callable[..., None], cut: str, value: int) -> None:
    on_split(**{cut: value})  # parts=N, pages=N or words=N


class SplitChoice:
    """The block (``self.widget``) and its controls: ``cuts`` and ``boxes`` by cut, ``keep``."""

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
        heading = QHBoxLayout()  # Keep on the title's line, as in the three windows
        title = label("strong")
        text(title, "gui.split.title")
        heading.addWidget(title)
        heading.addStretch(1)
        layout.addLayout(heading)

        self.cut_row = FoldRow()
        self._cut = QButtonGroup(parent)
        self.cuts: dict[str, QRadioButton] = {}
        self.boxes: dict[str, QSpinBox] = {}
        for cut, setting, words, unit in CUTS:
            radio = radio_button(self._cut, partial(on_split, cut=cut))
            box = number_box(setting, partial(_send_number, on_split, cut))
            after = label("onPage")
            text(radio, words)
            text(after, unit)
            self.cut_row.add(radio, box, after)
            self.cuts[cut], self.boxes[cut] = radio, box
        layout.addWidget(self.cut_row)

        keep_title = label("strong")
        text(keep_title, "gui.split.keep")
        heading.addWidget(keep_title)
        self._keep = QButtonGroup(parent)
        self.keep = {
            value: radio_button(self._keep, partial(on_split, keep=value))
            for value in ("pdf", "markdown", "both")
        }
        for value, radio in self.keep.items():
            text(radio, f"gui.split.keep_{value}")
            heading.addSpacing(SPACE)
            heading.addWidget(radio)
        for key in ("gui.split.note", "gui.split.hint"):
            line = label("muted", wrap=True)
            text(line, key)
            layout.addWidget(line)
        self.by_parts, self.by_pages = self.cuts["parts"], self.cuts["pages"]
        self.parts, self.pages = self.boxes["parts"], self.boxes["pages"]
        self.by_words, self.words = self.cuts["words"], self.boxes["words"]
        pairs = ((self.cuts[cut], self.boxes[cut]) for cut, *_ in CUTS)
        self.controls = (*(w for pair in pairs for w in pair), *self.keep.values())

    def show(self, choice: OutputChoice) -> None:
        """What the presenter keeps; setting the numbers sends nothing back."""
        self.cuts.get(choice.split_cut, self.by_parts).setChecked(True)
        numbers = {
            "parts": choice.split_parts,
            "pages": choice.split_pages,
            "words": choice.split_words,
        }
        for cut, value in numbers.items():
            box = self.boxes[cut]
            blocked = box.blockSignals(True)
            box.setValue(value)
            box.blockSignals(blocked)
        self.keep.get(choice.split_keep, self.keep["both"]).setChecked(True)
        if self.widget.isVisible():
            self.cut_row.fit()  # the words may have changed with the tool or the language
