"""What goes with the message line at the page's foot (features 036, 039): "Copy Details" after
an unexpected error, the line and "Undo" after Clear All, and the clipboard. A class of its own
(as Qt's ``window/note.py``): the window only forwards the presenter's calls to it."""

from typing import Any

from clearmd.frontend.presenter import Presenter
from clearmd.frontend.ttk.components.action_bar import ActionBar
from clearmd.frontend.ttk.window import undo
from clearmd.frontend.ttk.window.shown import Shown


class Note:
    def __init__(
        self, root: Any, message: Any, actions: ActionBar, presenter: Presenter, shown: Shown
    ) -> None:
        self._root = root
        self._message = message
        self._actions = actions
        self._presenter = presenter
        self._shown = shown

    def show_undo(self, text: str | None) -> None:
        """After Clear All: ``text`` and "Undo" (039); ``None`` hides both."""
        label = self._shown.need_catalog().text("gui.main.undo")
        undo.show_undo(self._message, self._actions, text, label, self._presenter.undo_clear)

    def show_details_button(self, label: str | None) -> None:
        """ "Copy Details" after an unexpected error; ``None`` hides it (036)."""
        self._actions.show_details(label, self._presenter.copy_details)

    def copy_text(self, text: str) -> None:
        """The system clipboard (036); kept by Tk until another program takes it."""
        self._root.clipboard_clear()
        self._root.clipboard_append(text)
        self._root.update()
