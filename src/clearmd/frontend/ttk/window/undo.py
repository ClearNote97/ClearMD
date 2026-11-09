""" "Undo" after Clear All (feature 039, audit v3 F1-03): the line that says the list was emptied,
in the message area in the text's colour (it is not a warning), and the bar's Undo button that
gives the list back. A module of its own: the window class stays within its size."""

from collections.abc import Callable
from tkinter import ttk

from clearmd.frontend.ttk.components.action_bar import ActionBar
from clearmd.frontend.ttk.visuals.style_names import ON_PAGE, WARNING


def show_undo(
    message: ttk.Label,
    actions: ActionBar,
    text: str | None,
    label: str,
    on_undo: Callable[[], None],
) -> None:
    """``text`` beside Undo (``label``), or neither (``None``: undone, or the list changed)."""
    if text is None:
        actions.show_undo(None)
        if str(message.cget("style")) == ON_PAGE:  # the line was the Undo's: it goes with it
            message.configure(text="", style=WARNING)
        return
    message.configure(text=text, style=ON_PAGE)
    actions.show_undo(label, on_undo)
