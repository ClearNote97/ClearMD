"""Where the results are, as text the user can read, select and copy (feature 035, AC-06): a
read-only text field on the page's ground, as many lines as the text has."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from clearmd.frontend.design.metrics import GAP
from clearmd.frontend.design.palette import Palette


class WhereText(tk.Text):
    """Read-only, yet selectable (and Ctrl+C copies it); hidden while there is nothing to say."""

    def __init__(self, parent: tk.Misc, *, fonts: dict[str, tkfont.Font]) -> None:
        super().__init__(
            parent, height=1, wrap="word", borderwidth=0, highlightthickness=0,
            font=fonts["body"], padx=0, pady=0, takefocus=True, cursor="xterm",
        )  # fmt: skip
        self.configure(state="disabled")
        # Disabled, a Text keeps its selection but drops the keys: copy stays at hand.
        self.bind("<Control-c>", lambda _event: self.event_generate("<<Copy>>"))
        self.bind("<Button-1>", lambda _event: self.focus_set(), add="+")

    def show(self, text: str, *, after: ttk.Widget | None = None) -> None:
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", text)
        self.configure(state="disabled", height=max(1, text.count("\n") + 1))
        if not text:
            self.pack_forget()
        elif not self.winfo_manager() and after is not None:
            self.pack(fill="x", pady=(GAP, 0), after=after)

    def text(self) -> str:
        return self.get("1.0", "end-1c")

    def apply_palette(self, palette: Palette) -> None:
        self.configure(
            background=palette.ground, foreground=palette.text, insertbackground=palette.text,
            selectbackground=palette.shape, selectforeground=palette.text,
            inactiveselectbackground=palette.shape,
        )  # fmt: skip
