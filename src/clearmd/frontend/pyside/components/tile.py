"""A start tile (feature 023): a large button with an icon, a title and what it does. The look of
flet's tiles of feature 021: the page's ground, a 1 px border turning to the accent, and the
selection's ground under the pointer, its height: the style sheet's ``QPushButton#tile``."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.pyside.components.primitives import button, label

ICON_SIZE = 6 * SPACE  # 48


class Tile:
    """The button (``self.button``: Enter or Space presses it) and the texts drawn on it."""

    def __init__(self, on_click: Callable[[], None]) -> None:
        self.button: QPushButton = button("tile", on_click)
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self.button)
        # From the top, not centred: the two tiles' icons and titles line up whatever the length
        # of their texts.
        layout.setContentsMargins(GAP, 5 * SPACE, GAP, GAP)
        layout.setSpacing(HALF)
        self.icon = QLabel()
        self.title = label("strong")
        self.body = label("muted", wrap=True)
        for widget in (self.icon, self.title, self.body):
            widget.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            # The pointer and the clicks go to the button under them.
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            layout.addWidget(widget)
        layout.insertSpacing(1, SPACE)  # the icon a little apart from the words
        layout.addStretch(1)

    def show_text(self, title: str, body: str) -> None:
        self.title.setText(title)
        self.body.setText(body)
        self.button.setAccessibleName(title)
        self.button.setAccessibleDescription(body)

    def show_icon(self, pixmap: QPixmap) -> None:
        self.icon.setPixmap(pixmap)
