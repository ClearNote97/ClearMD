"""A list's keyboard focus made visible (feature 040, audit v4 F2-01): while the list has the
focus its card wears an accent ring, and the row the arrows are on (the Treeview's focus item) is
tinted, selected or not. A ttk Treeview draws neither by itself."""

from tkinter import ttk

from clearmd.frontend.design.colors import blend
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.visuals.style_names import CARD, FOCUS_CARD

FOCUSED = "focused"  # the tag of the row with the keyboard's focus
_TINT = 0.12  # how much accent tints that row


class ListFocus:
    def __init__(self, card: ttk.Frame, tree: ttk.Treeview) -> None:
        self._card = card
        self._tree = tree
        self._marked = ""
        tree.bind("<FocusIn>", lambda _event: self.mark(), add="+")
        tree.bind("<FocusOut>", lambda _event: self.mark(), add="+")
        tree.bind("<<TreeviewSelect>>", lambda _event: self.mark(), add="+")
        tree.bind("<KeyRelease>", lambda _event: self.mark(), add="+")  # the arrows move it

    @property
    def shown(self) -> bool:
        """Whether the ring shows (for tests)."""
        return str(self._card.cget("style")) == FOCUS_CARD

    def apply_palette(self, palette: Palette) -> None:
        self._tree.tag_configure(FOCUSED, background=blend(palette.accent, palette.card, _TINT))

    def mark(self) -> None:
        """The ring and the tinted row, now; neither when the list does not have the focus."""
        focused = self._tree.focus_get() is self._tree
        self._card.configure(style=FOCUS_CARD if focused else CARD)
        item = self._tree.focus() if focused else ""
        if item == self._marked:
            return
        for old, add in ((self._marked, False), (item, True)):
            if old and self._tree.exists(old):
                tags = [t for t in self._tree.item(old, "tags") if t != FOCUSED]
                self._tree.item(old, tags=(*tags, FOCUSED) if add else tuple(tags))
        self._marked = item
