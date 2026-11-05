"""The two themes (``clearmd-light``, ``clearmd-dark``) made from the palettes, for ttkbootstrap.
A module of its own: the only place that writes ttkbootstrap's theme registry, before any widget."""

import ttkbootstrap as tb
from ttkbootstrap.style.theme import ThemeDefinition

from clearmd.frontend.design.palette import PALETTES


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
