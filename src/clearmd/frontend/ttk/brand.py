"""ClearMD's look in Tk (ADR-0027): the palette, the two themes and the rounded widgets.

ttkbootstrap carries the palette (radio buttons, the progress bar and the lists take the accent by
themselves). Rounded buttons and cards are ttk image elements drawn by ``art``: real ttk widgets,
with keyboard focus (a ring in the image) and a disabled look.
"""

import tkinter as tk
from dataclasses import dataclass
from typing import Any

import ttkbootstrap as tb
from PIL import ImageTk
from ttkbootstrap.style.theme import ThemeDefinition

from clearmd.frontend.ttk import art
from clearmd.frontend.ttk.layout import RADIUS


@dataclass(frozen=True)
class Palette:
    mode: str  # "light" or "dark"
    rail: str
    rail_text: str
    rail_muted: str
    rail_hover: str
    ground: str  # the working area behind the cards
    card: str
    text: str
    muted: str
    border: str
    accent: str  # the primary action, the current step
    accent_hover: str
    accent_text: str  # the accent as text on the ground (the step counter)
    on_accent: str
    clear: str  # the light accent: the "Clear" tone
    shape: str  # the background shape
    warning: str
    danger: str
    success: str

    @property
    def theme(self) -> str:
        return f"clearmd-{self.mode}"


LIGHT = Palette(
    mode="light",
    rail="#1B2733",
    rail_text="#F3F5F7",
    rail_muted="#A9B4BE",
    rail_hover="#26333F",
    ground="#F3F5F7",
    card="#FFFFFF",
    text="#1B2733",
    muted="#5B6672",
    border="#DCE2E7",
    accent="#0F766E",
    accent_hover="#0B5A54",
    accent_text="#0F766E",
    on_accent="#FFFFFF",
    clear="#0D9488",
    shape="#D7EEEA",
    warning="#B45309",
    danger="#B91C1C",
    success="#15803D",
)
DARK = Palette(
    mode="dark",
    rail="#0F161C",
    rail_text="#E6EBEF",
    rail_muted="#93A0AB",
    rail_hover="#1A242D",
    ground="#18212A",
    card="#202B36",
    text="#E6EBEF",
    muted="#A3AEB8",
    border="#2E3B47",
    accent="#2DD4BF",
    accent_hover="#5EEAD4",
    accent_text="#5EEAD4",
    on_accent="#0B1F1C",
    clear="#99F6E4",
    shape="#1E3A3A",
    warning="#F59E0B",
    danger="#F87171",
    success="#4ADE80",
)
PALETTES = {"light": LIGHT, "dark": DARK}

# The ttk styles ClearMD adds (on top of ttkbootstrap's).
PRIMARY = "Primary.ClearMD.TButton"  # the one primary action of a screen
SOFT = "Soft.ClearMD.TButton"  # a secondary action: white, a thin border
SOFT_ON_CARD = "SoftOnCard.ClearMD.TButton"  # the same, inside a card
STRONG = "Strong.ClearMD.TButton"  # a second action that matters as much (Convert more)
RAIL = "Rail.ClearMD.TButton"  # Settings and Help on the dark rail
LINK = "Link.ClearMD.TButton"  # a quiet action on the ground
CARD = "Card.ClearMD.TFrame"  # a white, rounded card
PAGE = "Page.ClearMD.TFrame"  # the working area's ground
MUTED = "Muted.ClearMD.TLabel"  # secondary text on a card
WARNING = "Warning.ClearMD.TLabel"  # a message on the ground
ON_PAGE = "OnPage.ClearMD.TLabel"  # text on the ground
HINT = "Hint.ClearMD.TLabel"  # why an action is disabled, on the ground
CHECK_ON_PAGE = "OnPage.ClearMD.TCheckbutton"  # a check box on the ground

_BUTTON_HEIGHT = 44  # a comfortable target (UX §5)


def register_themes(style: tb.Style) -> None:
    """Make ``clearmd-light`` and ``clearmd-dark`` available to ``style.theme_use``."""
    for palette in PALETTES.values():
        colours = {
            "primary": palette.accent,
            "secondary": palette.muted,
            "success": palette.success,
            "info": palette.accent,
            "warning": palette.warning,
            "danger": palette.danger,
            "light": palette.ground,
            "dark": palette.rail,
            "bg": palette.card,  # widgets sit on cards by default; the ground is a style
            "fg": palette.text,
            "selectbg": palette.accent,
            "selectfg": palette.on_accent,
            "border": palette.border,
            "inputfg": palette.text,
            "inputbg": palette.card,
            "active": palette.ground,
        }
        style.register_theme(ThemeDefinition(palette.theme, colours, mode=palette.mode))


class Look:
    """Installs ClearMD's styles in the theme in use, once per theme, and keeps their images."""

    def __init__(self, style: tb.Style, root: tk.Misc, fonts: dict[str, Any]) -> None:
        self._style = style
        self._root = root
        self._fonts = fonts
        self._images: dict[str, list[ImageTk.PhotoImage]] = {}

    def use(self, palette: Palette) -> None:
        self._style.theme_use(palette.theme)
        if palette.theme not in self._images:
            self._images[palette.theme] = []
            self._install(palette)

    def _image(self, palette: Palette, picture: Any) -> ImageTk.PhotoImage:
        image = ImageTk.PhotoImage(picture, master=self._root)
        self._images[palette.theme].append(image)  # Tk forgets an image Python does not hold
        return image

    def _button(
        self,
        palette: Palette,
        name: str,
        *,
        fill: str,
        hover: str,
        text: str,
        border: str | None = None,
        disabled_fill: str,
        disabled_text: str,
        ground: str,
        font: Any,
        padding: tuple[int, int],
    ) -> None:
        size, radius = 3 * RADIUS, RADIUS - 2

        def picture(colour: str, ring: str | None = None) -> ImageTk.PhotoImage:
            shape = art.rounded(size, size, radius, colour, border=border, ring=ring, ground=ground)
            return self._image(palette, shape)

        normal, active = picture(fill), picture(hover)
        focus, focus_active = picture(fill, palette.clear), picture(hover, palette.clear)
        disabled = picture(disabled_fill)
        element = f"{name}.face"
        self._style.element_create(
            element,
            "image",
            normal,
            ("disabled", disabled),
            ("pressed", active),
            ("focus", "active", focus_active),
            ("active", active),
            ("focus", focus),
            border=RADIUS,
            sticky="nsew",
        )
        label: Any = ("Button.label", {"sticky": ""})
        padding_node: Any = ("Button.padding", {"children": [label]})
        self._style.layout(name, [(element, {"sticky": "nsew", "children": [padding_node]})])
        self._style.configure(
            name, foreground=text, background=ground, font=font, padding=padding, anchor="center"
        )
        self._style.map(name, foreground=[("disabled", disabled_text)], background=[])

    def _install(self, p: Palette) -> None:
        style, fonts = self._style, self._fonts
        self._button(
            p, PRIMARY, fill=p.accent, hover=p.accent_hover, text=p.on_accent,
            disabled_fill=p.border, disabled_text=p.muted, ground=p.ground,
            font=fonts["strong"], padding=(24, 4),
        )  # fmt: skip
        self._button(
            p, SOFT, fill=p.card, hover=p.ground, text=p.text, border=p.border,
            disabled_fill=p.card, disabled_text=p.muted, ground=p.ground,
            font=fonts["strong"], padding=(16, 0),
        )  # fmt: skip
        self._button(
            p, SOFT_ON_CARD, fill=p.card, hover=p.ground, text=p.text, border=p.border,
            disabled_fill=p.card, disabled_text=p.muted, ground=p.card,
            font=fonts["strong"], padding=(16, 0),
        )  # fmt: skip
        self._button(
            p, STRONG, fill=p.shape, hover=p.border, text=p.accent_text, border=p.accent_text,
            disabled_fill=p.ground, disabled_text=p.muted, ground=p.ground,
            font=fonts["strong"], padding=(16, 0),
        )  # fmt: skip
        self._button(
            p, RAIL, fill=p.rail, hover=p.rail_hover, text=p.rail_text,
            disabled_fill=p.rail, disabled_text=p.rail_muted, ground=p.rail,
            font=fonts["body"], padding=(8, 0),
        )  # fmt: skip
        self._button(
            p, LINK, fill=p.ground, hover=p.border, text=p.accent_text,
            disabled_fill=p.ground, disabled_text=p.muted, ground=p.ground,
            font=fonts["strong"], padding=(4, 0),
        )  # fmt: skip

        card = art.rounded(3 * RADIUS, 3 * RADIUS, RADIUS, p.card, border=p.border, ground=p.ground)
        card_face = self._image(p, card)
        style.element_create("Card.ClearMD.face", "image", card_face, border=RADIUS, sticky="nsew")
        style.layout(CARD, [("Card.ClearMD.face", {"sticky": "nsew"})])
        style.configure(CARD, background=p.ground)
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
        cell = self._image(p, art.heading_cell(36, p.card, p.border))
        style.element_create(
            "Heading.ClearMD.cell", "image", cell, border=(0, 0, 2, 0), sticky="nsew"
        )
        text: Any = ("Treeheading.text", {"sticky": "we"})
        image: Any = ("Treeheading.image", {"side": "left", "sticky": ""})
        inner: Any = ("Treeheading.padding", {"sticky": "nsew", "children": [image, text]})
        style.layout(
            "Treeview.Heading", [("Heading.ClearMD.cell", {"sticky": "nsew", "children": [inner]})]
        )
        # A soft tint for the selection: the row's number, icon and text stay readable on it.
        style.map("Treeview", background=[("selected", p.shape)], foreground=[("selected", p.text)])
        style.configure("Horizontal.TProgressbar", thickness=8)
