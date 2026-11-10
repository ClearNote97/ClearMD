"""A list's "What Happens" text shown whole (feature 040, audit v4 F3-01): wrapped to its column's
width on as many lines as it needs, never cut with "…". A ttk Treeview has one row height for
all its rows, so the list's own style takes the height of its tallest row; it is measured again
when the column's width changes, and set again after a theme change (styles are per theme)."""

import tkinter.font as tkfont
from collections.abc import Mapping
from itertools import count
from tkinter import ttk
from typing import Any, Protocol

ROW = 36  # the one-line row's height (styles.py)
_PAD = 12  # the cell's own margins
_names = count(1)


class Row(Protocol):
    @property
    def values(self) -> tuple[str, ...]: ...


def wrapped(text: str, width: int, font: tkfont.Font) -> list[str]:
    """``text`` in lines that fit ``width`` pixels; a word longer than a line is cut by
    characters (a path), never dropped."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            candidate = f"{line} {word}" if line else word
            if font.measure(candidate) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
            while font.measure(word) > width and len(word) > 1:  # a long path: by characters
                cut = max(1, next((i for i in range(len(word), 0, -1)
                                   if font.measure(word[:i]) <= width), 1))  # fmt: skip
                lines.append(word[:cut])
                word = word[cut:]
            line = word
        lines.append(line)
    return lines


class RowWrap:
    """Wraps the value at ``index`` of each row of ``tree`` (whose rows are ``rows``)."""

    def __init__(self, tree: ttk.Treeview, rows: Mapping[str, Row], index: int) -> None:
        self._tree = tree
        self._rows = rows
        self._index = index
        self._key = f"c{index}"
        self.style = f"Wrap{next(_names)}.Treeview"
        tree.configure(style=self.style)
        self._pending: str | None = None
        self._width = 0
        self.lines = 1  # the tallest row's lines, for tests
        tree.bind("<Configure>", lambda _event: self.soon(), add="+")

    def soon(self) -> None:
        if self._pending is None:
            self._pending = self._tree.after_idle(self.refresh)

    def refresh(self, *, force: bool = False) -> None:
        """Wrap every row to the column's width, and size the rows to the tallest."""
        self._pending = None
        # The column's own width, or what the list shows of it (a column never shrinks below its
        # width: past the list's edge its end would be cut).
        others = sum(int(self._tree.column(c, "width")) for c in ("#0", *self._others()))
        shown = self._tree.winfo_width() - others
        width = min(int(self._tree.column(self._key, "width")), shown) - _PAD
        if width < 40 or (width == self._width and not force):
            return
        self._width = width
        font = _font(self._tree)
        tallest = 1
        for item in self._tree.get_children():
            values = list(self._rows[item].values)
            lines = wrapped(values[self._index], width, font)
            values[self._index] = "\n".join(lines)
            self._tree.item(item, values=values)
            tallest = max(tallest, len(lines))
        self.lines = tallest
        height = max(ROW, tallest * font.metrics("linespace") + _PAD)
        ttk.Style(self._tree).configure(self.style, rowheight=height)

    def _others(self) -> list[str]:
        return [str(c) for c in self._tree.cget("columns") if str(c) != self._key]

    def rows_changed(self) -> None:
        self._width = 0  # new rows: wrapped again even at the same width
        self.soon()


def _font(tree: Any) -> tkfont.Font:
    name = ttk.Style(tree).lookup("Treeview", "font") or "TkDefaultFont"
    try:
        return tkfont.nametofont(str(name), root=tree)
    except Exception:  # noqa: BLE001 -- a font given as a description, not a name
        return tkfont.Font(root=tree, font=name)
