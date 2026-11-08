"""The start screen's three icons (feature 032, AC-04): the shapes of ``design.tool_art``, the same
in the three windows, as an SVG image. Drawn in one colour and tinted with the theme's accent, so a
theme change needs no new picture."""

import flet as ft

from clearmd.frontend.design.tool_art import svg
from clearmd.frontend.flet.visuals.theme import role

INK = "#000000"  # the SVG's own colour: the tint replaces it


def tool_icon(tool: str, size: int) -> ft.Image:
    """``tool``'s icon ("convert", "split", "merge"), ``size`` pixels square."""
    return ft.Image(
        src=svg(tool, INK, size).encode("utf-8"),
        width=size,
        height=size,
        color=role("accent_text"),
        color_blend_mode=ft.BlendMode.SRC_IN,
    )
