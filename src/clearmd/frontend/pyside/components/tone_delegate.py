"""A list row keeps its tone when selected (audit v3, F3-03): a failure stays red and a left-out
row amber on the selection's ground, so the row's kind never vanishes under the selection (the
red there measures 5.01:1 in the light theme)."""

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QBrush, QPalette
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


class ToneDelegate(QStyledItemDelegate):
    """Draws a selected cell's text in the cell's own colour when it has one."""

    def initStyleOption(  # noqa: N802 -- Qt's name
        self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex
    ) -> None:
        super().initStyleOption(option, index)
        tone = index.data(Qt.ItemDataRole.ForegroundRole)
        if isinstance(tone, QBrush):
            option.palette.setBrush(QPalette.ColorRole.HighlightedText, tone)
