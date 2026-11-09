"""The message area under the page: the message, "Copy Details" after an unexpected error (036)
and "Undo" after Clear All (audit v3, F1-03). Each button goes with the line it explains: a
cleared message takes both away."""

from PySide6.QtWidgets import QLabel, QPushButton

from clearmd.i18n import Catalog


class Note:
    def __init__(self, message: QLabel, details: QPushButton, undo: QPushButton) -> None:
        self._message = message
        self._details = details
        self._undo = undo
        self._undo_line = ""

    def show_message(self, text: str) -> None:
        self._message.setText(text)
        if not text:
            self._details.hide()
            self._undo.hide()

    def show_details_button(self, text: str | None) -> None:
        self._details.setText(text or "")
        self._details.setAccessibleName(text or "")
        self._details.setVisible(bool(text))

    def show_undo(self, text: str | None) -> None:
        """The line that says the list was emptied, beside Undo; ``None`` takes both away."""
        if text:
            self._undo_line = text
            self._details.hide()
            self._message.setText(text)
            self._undo.show()
            return
        if self._message.text() == self._undo_line:
            self._message.setText("")
        self._undo_line = ""
        self._undo.hide()

    def forget(self) -> None:
        self._details.hide()

    def apply_language(self, catalog: Catalog) -> None:
        self._undo.setText(catalog.text("gui.main.undo"))
        self._undo.setAccessibleName(self._undo.text())
