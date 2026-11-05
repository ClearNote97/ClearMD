"""The small widgets every other one is made of: a named label, a button, a rounded card, a radio
button in a group, and ``restyle``, which draws a widget again after a property changed."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from clearmd.frontend.design.metrics import GAP, SPACE


def label(name: str, text: str = "", *, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


def button(name: str, on_click: Callable[[], None] | None = None) -> QPushButton:
    widget = QPushButton()
    if name:
        widget.setObjectName(name)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if on_click is not None:
        widget.clicked.connect(lambda _checked=False: on_click())
    return widget


def card(
    *, padding: int = GAP, horizontal: bool = False
) -> tuple[QFrame, QVBoxLayout | QHBoxLayout]:
    """A rounded card and its layout, with ``padding`` on every side."""
    frame = QFrame()
    frame.setObjectName("card")
    layout: QVBoxLayout | QHBoxLayout = QHBoxLayout(frame) if horizontal else QVBoxLayout(frame)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(SPACE)
    return frame, layout


def restyle(widget: QWidget, name: str, value: Any) -> None:
    """Set a property the style sheet reads, and draw the widget again with it."""
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    for child in widget.findChildren(QWidget):
        child.style().unpolish(child)
        child.style().polish(child)


def radio_button(group: QButtonGroup, on_click: Callable[[], None] | None = None) -> QRadioButton:
    radio = QRadioButton()
    group.addButton(radio)
    if on_click is not None:
        radio.clicked.connect(lambda _checked=False: on_click())
    return radio
