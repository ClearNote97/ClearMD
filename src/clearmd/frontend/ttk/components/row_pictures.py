"""A file list's row pictures (feature 035, AC-07): its checkbox, its number and its file icon in
one image. Drawn only for the rows on screen and kept by what they show (the icon, the number,
the box, the colours), so a thousand rows appear at once and a theme or a move in Merge's order
draws again only what is new."""

import tkinter as tk
from collections.abc import Iterable
from typing import Any

from PIL import Image, ImageTk

from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.visuals import marks

_FALLBACK = ("#0F766E", "#5B6672", "#FFFFFF")  # accent, muted, on accent: before a palette

Key = tuple[str, int, int, str, tuple[str, str, str]]  # icon, number, digits, box, colours


class RowPictures:
    """The pictures of ``tree``'s rows; ``paint`` draws those of the given rows on demand."""

    def __init__(self, master: tk.Misc, tree: Any, *, checks: bool) -> None:
        self._master = master
        self._tree = tree
        self._checks = checks
        self._colours = _FALLBACK
        self._cache: dict[Key, ImageTk.PhotoImage] = {}
        self._blank: dict[int, ImageTk.PhotoImage] = {}
        self._shown: dict[str, Key] = {}  # the picture each row shows now

    def use(self, palette: Palette) -> None:
        """Other colours: the rows on screen are painted again (the old pictures stay cached)."""
        self._colours = (palette.accent, palette.muted, palette.on_accent)
        self._shown.clear()

    def forget(self) -> None:
        """The rows were replaced: none shows a picture of its own yet."""
        self._shown.clear()

    def blank(self, digits: int) -> ImageTk.PhotoImage:
        """A clear picture the size of a row's: rows not painted yet keep their place."""
        if digits not in self._blank:
            size = self._picture(("unknown", 1, digits, "off", self._colours)).size
            image = Image.new("RGBA", size, (0, 0, 0, 0))
            self._blank[digits] = ImageTk.PhotoImage(image, master=self._master)
        return self._blank[digits]

    def paint(self, rows: Iterable[tuple[str, str, int, int, bool]]) -> None:
        """``(item, icon, number, digits, selected)`` for each row to show as it is now."""
        for item, icon, number, digits, selected in rows:
            box = ("on" if selected else "off") if self._checks else ""
            key: Key = (icon, number, digits, box, self._colours)
            if self._shown.get(item) == key:
                continue
            if key not in self._cache:
                picture = self._picture(key)
                self._cache[key] = ImageTk.PhotoImage(picture, master=self._master)
            self._tree.item(item, image=self._cache[key])
            self._shown[item] = key

    def checked(self, item: str) -> bool:
        """Whether ``item``'s picture shows its box checked (for tests)."""
        key = self._shown.get(item)
        return key is not None and key[3] == "on"

    def _picture(self, key: Key) -> Image.Image:
        icon, number, digits, box, (accent, muted, on_accent) = key
        check = marks.checkbox(box, box=accent, border=muted, mark=on_accent) if box else None
        return marks.numbered(number, marks.icon(icon), muted, digits=digits, check=check)
