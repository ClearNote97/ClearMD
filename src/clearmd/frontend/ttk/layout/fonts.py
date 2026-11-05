"""The named fonts of the window: the body font and the bold ones the styles and widgets use."""

import tkinter as tk
import tkinter.font as tkfont
from typing import Literal

from clearmd.frontend.ttk.layout.units import BODY, EYEBROW, STRONG, TITLE, WORDMARK

_NAMED_FONTS = ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont")


def make_fonts(root: tk.Misc) -> dict[str, tkfont.Font]:
    for name in _NAMED_FONTS:
        tkfont.nametofont(name, root=root).configure(size=BODY)
    family = tkfont.nametofont("TkDefaultFont", root=root).actual("family")

    def font(size: int, weight: Literal["normal", "bold"] = "normal") -> tkfont.Font:
        return tkfont.Font(root=root, family=family, size=size, weight=weight)

    return {
        "body": tkfont.nametofont("TkDefaultFont", root=root),
        "strong": font(STRONG, "bold"),
        "eyebrow": font(EYEBROW, "bold"),
        "title": font(TITLE, "bold"),
        "wordmark": font(WORDMARK, "bold"),
    }
