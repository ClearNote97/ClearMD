"""How to Split (feature 023): into N parts or every N pages, and what to keep of the parts. Shown
on step 1's results card in place of the images, when the tool is Split. A number is sent when it
is done (Enter, leaving the box, the arrow keys), not on every key; the presenter refuses one out
of range and the box shows again what it keeps."""

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
from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.presenter.models import OutputChoice
from clearmd.frontend.pyside.components.primitives import label, radio_button

NUMBER_WIDTH = 8 * SPACE  # five digits, centred
Text = Callable[[QLabel | QPushButton | QRadioButton, str], None]


def number_box(setting: str, on_value: Callable[[int], None]) -> QSpinBox:
    """A number without arrows (the arrow keys and the wheel still change it), in its range.
    The arrows go in the style sheet: Qt's NoButtons leaves a styled box's text 1 px wide."""
    box = QSpinBox()
    low, high = RANGES[setting]
    box.setRange(low, high)
    box.setFixedWidth(NUMBER_WIDTH)
    box.setAlignment(Qt.AlignmentFlag.AlignCenter)  # its arrows are hidden by the style sheet
    box.setKeyboardTracking(False)  # valueChanged once the number is done, not per key
    box.valueChanged.connect(on_value)
    return box


class SplitChoice:
    """The block (``self.widget``) and its controls."""

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
        heading = QHBoxLayout()  # Keep on the right, where the images' choice is for Convert
        title = label("strong")
        text(title, "gui.split.title")
        heading.addWidget(title)
        heading.addStretch(1)
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
        layout.addLayout(heading)

        cut = QHBoxLayout()
        cut.setSpacing(SPACE)
        self._cut = QButtonGroup(parent)
        self.by_parts = radio_button(self._cut, lambda: on_split(cut="parts"))
        self.by_pages = radio_button(self._cut, lambda: on_split(cut="pages"))
        self.parts = number_box("split_parts", lambda value: on_split(parts=value))
        self.pages = number_box("split_pages", lambda value: on_split(pages=value))
        text(self.by_parts, "gui.split.into")
        text(self.by_pages, "gui.split.every")
        parts_word, pages_word = label("onPage"), label("onPage")
        text(parts_word, "gui.split.parts")
        text(pages_word, "gui.split.pages")
        for radio, box, word in (
            (self.by_parts, self.parts, parts_word),
            (self.by_pages, self.pages, pages_word),
        ):
            cut.addWidget(radio)
            cut.addWidget(box)
            cut.addWidget(word)
            cut.addSpacing(GAP)
        cut.addStretch(1)
        layout.addLayout(cut)
        note = label("muted", wrap=True)
        text(note, "gui.split.note")
        layout.addWidget(note)
        self.controls = (self.by_parts, self.parts, self.by_pages, self.pages, *self.keep.values())

    def show(self, choice: OutputChoice) -> None:
        """What the presenter keeps; setting the numbers sends nothing back."""
        (self.by_pages if choice.split_cut == "pages" else self.by_parts).setChecked(True)
        for box, value in ((self.parts, choice.split_parts), (self.pages, choice.split_pages)):
            blocked = box.blockSignals(True)
            box.setValue(value)
            box.blockSignals(blocked)
        self.keep.get(choice.split_keep, self.keep["both"]).setChecked(True)
