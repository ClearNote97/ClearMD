"""The look of the controls (ADR-0027): what each kind of text is (size, weight, colour) and how
each kind of button is drawn. Colours are theme slots (``theme.role``), so a theme change redraws
nothing. A module of its own: Qt's style sheet, as data flet's controls take."""

import flet as ft

from clearmd.frontend.design.metrics import GAP, RADIUS, SPACE
from clearmd.frontend.design.typography import (
    BODY,
    EYEBROW,
    FIGURE,
    SMALL,
    STRONG,
    SUBTITLE,
    TITLE,
    WORDMARK,
)
from clearmd.frontend.flet.visuals.theme import role

# kind of text: (size in px, bold, colour role)
TEXTS: dict[str, tuple[int, bool, str]] = {
    "onPage": (BODY, False, "text"),
    "strong": (STRONG, True, "text"),
    "muted": (BODY, False, "muted"),
    "hint": (SMALL, False, "muted"),
    "empty": (BODY, False, "muted"),
    "message": (BODY, False, "warning"),
    "warning": (BODY, False, "warning"),
    "title": (TITLE, True, "text"),
    "subtitle": (BODY, False, "muted"),
    "eyebrow": (EYEBROW, True, "accent_text"),
    "dialogTitle": (SUBTITLE, True, "text"),
    "figure": (FIGURE, True, "text"),
    "bigText": (TITLE, True, "text"),
    "wordmark": (WORDMARK, True, "rail_text"),
    "local": (SMALL, False, "rail_muted"),
    "rail": (BODY, False, "rail_dim"),
    "railCurrent": (BODY, True, "on_accent"),
    "railButton": (BODY, False, "rail_text"),
    "badge": (SMALL, True, "rail_dim"),
}
TONES = {"accent": "accent_text", "warning": "warning", "danger": "danger", "neutral": "text"}
DEFAULT, HOVERED = ft.ControlState.DEFAULT, ft.ControlState.HOVERED
DISABLED = ft.ControlState.DISABLED


def paint(text: ft.Text, kind: str) -> ft.Text:
    """Give ``text`` the size, weight and colour of its kind."""
    size, bold, colour = TEXTS[kind]
    text.size = size
    text.weight = ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL
    text.color = role(colour)
    return text


def text_style(kind: str) -> ft.TextStyle:
    size, bold, colour = TEXTS[kind]
    weight = ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL
    return ft.TextStyle(size=size, weight=weight, color=role(colour))


def _states(
    normal: str, *, hovered: str | None = None, disabled: str | None = None
) -> dict[ft.ControlState, ft.ColorValue]:
    found: dict[ft.ControlState, ft.ColorValue] = {DEFAULT: role(normal)}
    if hovered is not None:
        found[HOVERED] = role(hovered)
    if disabled is not None:
        found[DISABLED] = role(disabled)
    return found


def button_style(kind: str) -> ft.ButtonStyle:
    """``""`` a plain button, ``primary`` the page's action, ``strong`` as prominent as it,
    ``link`` a text link."""
    shape = ft.RoundedRectangleBorder(radius=RADIUS - 2)
    bold = ft.TextStyle(size=STRONG, weight=ft.FontWeight.BOLD)
    if kind == "primary":
        return ft.ButtonStyle(
            color=_states("on_accent", disabled="disabled"),
            bgcolor=_states("accent", hovered="accent_hover", disabled="border"),
            shape=shape,
            padding=ft.Padding.symmetric(horizontal=GAP),
            text_style=bold,
            elevation=0,
        )
    if kind == "link":
        return ft.ButtonStyle(
            color=_states("accent_text", disabled="disabled"),
            # Every state named: Flutter fills a state left out (disabled) with its own grey box.
            bgcolor={
                DEFAULT: ft.Colors.TRANSPARENT,
                DISABLED: ft.Colors.TRANSPARENT,
                HOVERED: role("selected"),
            },
            shadow_color=ft.Colors.TRANSPARENT,
            shape=shape,
            padding=ft.Padding.symmetric(horizontal=SPACE),
            text_style=bold,
            elevation=0,
        )
    strong = kind == "strong"
    side = ft.BorderSide(2 if strong else 1, role("accent" if strong else "border"))
    return ft.ButtonStyle(
        color=_states("accent_text" if strong else "text", disabled="disabled"),
        bgcolor=_states("card", disabled="card"),
        shadow_color=ft.Colors.TRANSPARENT,
        side={DEFAULT: side, HOVERED: ft.BorderSide(side.width, role("accent"))},
        shape=shape,
        padding=ft.Padding.symmetric(horizontal=GAP),
        text_style=bold,
        elevation=0,
    )


def tile_style(top: int = GAP, *, current: bool = False, centred: bool = False) -> ft.ButtonStyle:
    """A start tile (feature 021): the page's ground in the card, its border turning to the accent
    and its ground to the selection under the pointer; its content from the top, ``top`` below
    the edge (feature 024: two tiles' icons at the same height). ``current``: the accent border
    at rest too ("What Next?"'s tool just used, feature 033); ``centred``: the content in the
    middle (a tile without a body, as Qt and ttk draw it)."""
    border = ft.BorderSide(2, role("accent")) if current else ft.BorderSide(1, role("border"))
    return ft.ButtonStyle(
        color=_states("text", disabled="disabled"),
        bgcolor={DEFAULT: role("ground"), HOVERED: role("selected"), DISABLED: role("ground")},
        overlay_color=ft.Colors.TRANSPARENT,
        shadow_color=ft.Colors.TRANSPARENT,
        side={DEFAULT: border, HOVERED: ft.BorderSide(2, role("accent"))},
        shape=ft.RoundedRectangleBorder(radius=RADIUS),
        padding=ft.Padding.only(left=GAP, top=GAP if centred else top, right=GAP, bottom=GAP),
        # icons and titles in line, whatever the text below; a lone title: in the middle
        alignment=ft.Alignment.CENTER if centred else ft.Alignment.TOP_CENTER,
        elevation=0,
    )
