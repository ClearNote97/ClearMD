"""ClearMD's colours in flet (ADR-0027, ADR-0039): the shared palette as a Material theme.

Each colour of the palette rides in one slot of the theme's colour scheme, and the controls name
the slot (``ft.Colors.PRIMARY``…), never a colour: flet's program resolves it from the theme on
screen, so changing the theme is one call and no control is drawn again. ``ROLES`` is the one
table from ClearMD's colours to the slots that carry them.
"""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.colors import blend
from clearmd.frontend.design.palette import Palette

DIM_STRENGTH = 0.45  # a faded card: this much of the card's colour on the ground's (as Qt, 014)
DIM_TEXT = 0.8  # its text: this much of the muted colour on the faded card
SELECTED = 0.18  # a selected row: this much of the accent on the card (as Qt)


def _dim_card(p: Palette) -> str:
    return blend(p.card, p.ground, DIM_STRENGTH)


ROLES: dict[str, tuple[str, Callable[[Palette], str]]] = {  # role: (slot, its colour)
    "accent": ("primary", lambda p: p.accent),
    "on_accent": ("on_primary", lambda p: p.on_accent),
    "accent_hover": ("primary_container", lambda p: p.accent_hover),
    "accent_text": ("secondary", lambda p: p.accent_text),
    "clear": ("inverse_primary", lambda p: p.clear),
    "text": ("on_surface", lambda p: p.text),
    "muted": ("on_surface_variant", lambda p: p.muted),
    "card": ("surface", lambda p: p.card),
    "ground": ("surface_container_lowest", lambda p: p.ground),
    "border": ("outline", lambda p: p.border),
    "warning": ("tertiary", lambda p: p.warning),
    "danger": ("error", lambda p: p.danger),
    "rail": ("inverse_surface", lambda p: p.rail),
    "rail_text": ("on_inverse_surface", lambda p: p.rail_text),
    "rail_muted": ("tertiary_fixed_dim", lambda p: p.rail_muted),
    "rail_hover": ("tertiary_fixed", lambda p: p.rail_hover),
    "rail_dim": ("secondary_fixed_dim", lambda p: blend(p.rail_text, p.rail, 0.55)),
    "shape": ("on_secondary_fixed", lambda p: p.shape),
    "selected": ("primary_fixed", lambda p: blend(p.accent, p.card, SELECTED)),
    "dim_card": ("primary_fixed_dim", _dim_card),
    "dim_text": ("secondary_fixed", lambda p: blend(p.muted, _dim_card(p), DIM_TEXT)),
    "disabled": ("on_primary_fixed", lambda p: blend(p.muted, p.card, 0.5)),
}
# Slots Material's own controls read (menus, dialogs, tints): ClearMD's colours, not its defaults.
_MATERIAL: dict[str, Callable[[Palette], str]] = {
    "on_primary_container": lambda p: p.on_accent,
    "on_secondary": lambda p: p.on_accent,
    "on_tertiary": lambda p: p.on_accent,
    "on_error": lambda p: p.on_accent,
    "secondary_container": lambda p: p.border,
    "on_secondary_container": lambda p: p.text,
    "outline_variant": lambda p: p.border,
    "surface_container": lambda p: p.card,
    "surface_container_low": lambda p: p.card,
    "surface_container_high": lambda p: p.ground,
    "surface_container_highest": lambda p: p.card,
    "surface_tint": lambda p: p.card,
}


def role(name: str) -> ft.Colors:
    """The theme slot that carries one of ClearMD's colours, for a control to name."""
    return ft.Colors[ROLES[name][0].upper()]


def theme(p: Palette) -> ft.Theme:
    """The Material theme of one palette: every slot of ``ROLES`` with its colour."""
    slots = {slot: colour(p) for slot, colour in ROLES.values()}
    slots.update({slot: colour(p) for slot, colour in _MATERIAL.items()})
    return ft.Theme(
        color_scheme=ft.ColorScheme(**slots),
        scaffold_bgcolor=p.ground,
        use_material3=True,
    )


def theme_mode(p: Palette) -> ft.ThemeMode:
    return ft.ThemeMode.DARK if p.mode == "dark" else ft.ThemeMode.LIGHT
