"""The rounded button element: a ttk image element drawn by ``shapes`` for each state."""

from collections.abc import Callable
from typing import Any

import ttkbootstrap as tb
from PIL import ImageTk

from clearmd.frontend.design.metrics import RADIUS
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.visuals import shapes


def rounded_button(
    style: tb.Style,
    image: Callable[[Palette, Any], ImageTk.PhotoImage],
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
    padding: tuple[int, ...],
    align: str = "",
) -> None:
    """Install the ttk style ``name``: a rounded button, a real ttk widget with a focus ring in the
    image and a disabled look."""
    size, radius = 3 * RADIUS, RADIUS - 2

    def picture(colour: str, ring: str | None = None) -> ImageTk.PhotoImage:
        shape = shapes.rounded(size, size, radius, colour, border=border, ring=ring, ground=ground)
        return image(palette, shape)

    normal, active = picture(fill), picture(hover)
    focus, focus_active = picture(fill, palette.clear), picture(hover, palette.clear)
    disabled = picture(disabled_fill)
    element = f"{name}.face"
    style.element_create(
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
    label: Any = ("Button.label", {"sticky": align})
    padding_node: Any = ("Button.padding", {"children": [label]})
    style.layout(name, [(element, {"sticky": "nsew", "children": [padding_node]})])
    style.configure(
        name, foreground=text, background=ground, font=font, padding=padding, anchor="center"
    )
    style.map(name, foreground=[("disabled", disabled_text)], background=[])
