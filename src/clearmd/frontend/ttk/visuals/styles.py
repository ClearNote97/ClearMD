"""ClearMD's ttk styles in one theme: buttons, cards, labels, the list and its heading."""

from collections.abc import Callable
from typing import Any

import ttkbootstrap as tb
from PIL import ImageTk

from clearmd.frontend.design.colors import blend
from clearmd.frontend.design.metrics import RADIUS
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.visuals import marks, shapes
from clearmd.frontend.ttk.visuals.buttons import rounded_button
from clearmd.frontend.ttk.visuals.style_names import (
    CARD,
    CHECK_ON_PAGE,
    DIM,
    DIM_CARD,
    HINT,
    LINK,
    MUTED,
    ON_PAGE,
    PAGE,
    PRIMARY,
    RAIL,
    RAIL_COMPACT,
    RAIL_TEXT_X,
    SOFT,
    SOFT_ON_CARD,
    STRONG,
    WARNING,
)

DIM_STRENGTH = 0.45  # a faded card: this much of the card's colour on the ground's
DIM_TEXT = 0.8  # its text: this much of the muted colour on the faded card (3:1, review of 014)


def install(
    style: tb.Style,
    photo: Callable[[Palette, Any], ImageTk.PhotoImage],
    fonts: dict[str, Any],
    p: Palette,
) -> None:
    """Install ClearMD's styles in the theme in use; ``photo`` keeps each picture Tk is shown."""
    rounded_button(
        style, photo, p, PRIMARY, fill=p.accent, hover=p.accent_hover, text=p.on_accent,
        disabled_fill=p.border, disabled_text=p.muted, ground=p.ground,
        font=fonts["strong"], padding=(24, 4),
    )  # fmt: skip
    rounded_button(
        style, photo, p, SOFT, fill=p.card, hover=p.ground, text=p.text, border=p.border,
        disabled_fill=p.card, disabled_text=p.muted, ground=p.ground,
        font=fonts["strong"], padding=(16, 0),
    )  # fmt: skip
    rounded_button(
        style, photo, p, SOFT_ON_CARD, fill=p.card, hover=p.ground, text=p.text, border=p.border,
        disabled_fill=p.card, disabled_text=p.muted, ground=p.card,
        font=fonts["strong"], padding=(16, 0),
    )  # fmt: skip
    rounded_button(
        style, photo, p, STRONG, fill=p.shape, hover=p.border, text=p.accent_text,
        border=p.accent_text, disabled_fill=p.ground, disabled_text=p.muted, ground=p.ground,
        font=fonts["strong"], padding=(16, 0),
    )  # fmt: skip
    rounded_button(
        style, photo, p, RAIL, fill=p.rail, hover=p.rail_hover, text=p.rail_text,
        disabled_fill=p.rail, disabled_text=p.rail_muted, ground=p.rail,
        font=fonts["body"], padding=(RAIL_TEXT_X, 0, 0, 0), align="w",
    )  # fmt: skip
    rounded_button(
        style, photo, p, RAIL_COMPACT, fill=p.rail, hover=p.rail_hover, text=p.rail_text,
        disabled_fill=p.rail, disabled_text=p.rail_muted, ground=p.rail,
        font=fonts["body"], padding=(0, 0),
    )  # fmt: skip
    rounded_button(
        style, photo, p, LINK, fill=p.ground, hover=p.border, text=p.accent_text,
        disabled_fill=p.ground, disabled_text=p.muted, ground=p.ground,
        font=fonts["strong"], padding=(4, 0),
    )  # fmt: skip

    card = shapes.rounded(3 * RADIUS, 3 * RADIUS, RADIUS, p.card, border=p.border, ground=p.ground)
    card_face = photo(p, card)
    style.element_create("Card.ClearMD.face", "image", card_face, border=RADIUS, sticky="nsew")
    style.layout(CARD, [("Card.ClearMD.face", {"sticky": "nsew"})])
    style.configure(CARD, background=p.ground)
    dim_fill = blend(p.card, p.ground, DIM_STRENGTH)
    dim = shapes.rounded(3 * RADIUS, 3 * RADIUS, RADIUS, dim_fill, border=p.border, ground=p.ground)
    style.element_create(
        "Dim.Card.ClearMD.face", "image", photo(p, dim), border=RADIUS, sticky="nsew"
    )
    style.layout(DIM_CARD, [("Dim.Card.ClearMD.face", {"sticky": "nsew"})])
    style.configure(DIM_CARD, background=p.ground)
    style.configure(DIM, background=dim_fill, foreground=blend(p.muted, dim_fill, DIM_TEXT))
    style.configure(PAGE, background=p.ground)
    style.configure(MUTED, background=p.card, foreground=p.muted)
    style.configure(ON_PAGE, background=p.ground, foreground=p.text)
    style.configure(WARNING, background=p.ground, foreground=p.warning)
    style.configure(HINT, background=p.ground, foreground=p.muted)

    style.configure("TRadiobutton", background=p.card, foreground=p.text)
    style.configure("TCheckbutton", background=p.card, foreground=p.text)
    style.configure(CHECK_ON_PAGE, background=p.ground, foreground=p.text)
    style.configure("TLabel", background=p.card, foreground=p.text)
    style.configure(
        "Treeview",
        background=p.card,
        fieldbackground=p.card,
        foreground=p.text,
        rowheight=36,
        borderwidth=0,
        relief="flat",
    )
    style.configure(
        "Treeview.Heading",
        background=p.card,
        foreground=p.muted,
        relief="flat",
        borderwidth=0,
        font=fonts["strong"],
        padding=(8, 8),
    )
    style.map("Treeview.Heading", background=[("active", p.card)])
    # Faint separators between the headings, where a column can be resized (feature 007).
    cell = photo(p, marks.heading_cell(36, p.card, p.border))
    style.element_create("Heading.ClearMD.cell", "image", cell, border=(0, 0, 2, 0), sticky="nsew")
    text: Any = ("Treeheading.text", {"sticky": "we"})
    image: Any = ("Treeheading.image", {"side": "left", "sticky": ""})
    inner: Any = ("Treeheading.padding", {"sticky": "nsew", "children": [image, text]})
    style.layout(
        "Treeview.Heading", [("Heading.ClearMD.cell", {"sticky": "nsew", "children": [inner]})]
    )
    # A soft tint for the selection: the row's number, icon and text stay readable on it.
    style.map("Treeview", background=[("selected", p.shape)], foreground=[("selected", p.text)])
    style.configure("Horizontal.TProgressbar", thickness=8)
    # A number field (Split's sizes, feature 023): ttkbootstrap leaves the spin box to clam's
    # white field, unreadable in the dark theme.
    style.configure(
        "TSpinbox", fieldbackground=p.card, background=p.card, foreground=p.text,
        insertcolor=p.text, arrowcolor=p.text, bordercolor=p.border, lightcolor=p.card,
        darkcolor=p.card,
    )  # fmt: skip
    style.map(
        "TSpinbox",
        fieldbackground=[("disabled", p.ground)],
        foreground=[("disabled", p.muted)],
        bordercolor=[("focus", p.accent)],
    )
