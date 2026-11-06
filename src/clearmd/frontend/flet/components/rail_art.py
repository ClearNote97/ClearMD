"""What the rail draws: a step's numbered badge, and the look of its buttons."""

import flet as ft

from clearmd.frontend.design.metrics import RADIUS, SPACE
from clearmd.frontend.flet.components.primitives import label
from clearmd.frontend.flet.layout.units import BADGE
from clearmd.frontend.flet.visuals.look import DEFAULT, HOVERED
from clearmd.frontend.flet.visuals.theme import role


def badge(number: int) -> tuple[ft.Container, ft.Text]:
    """A step's number in its circle; ``paint_badge`` gives it its colours."""
    digit = label("badge", str(number))
    circle = ft.Container(
        content=digit,
        width=BADGE,
        height=BADGE,
        shape=ft.BoxShape.CIRCLE,
        alignment=ft.Alignment.CENTER,
    )
    return circle, digit


def paint_badge(circle: ft.Container, digit: ft.Text, *, current: bool) -> None:
    colour = role("on_accent" if current else "rail_dim")
    circle.bgcolor = role("accent" if current else "rail")
    circle.border = ft.Border.all(1.5, colour)
    digit.color = colour


def rail_style(
    *, current: bool = False, compact: bool = False, inset: int = SPACE
) -> ft.ButtonStyle:
    """A step or a rail button: flat on the rail, the step on screen filled with the accent."""
    fill = role("accent") if current else ft.Colors.TRANSPARENT
    return ft.ButtonStyle(
        bgcolor={DEFAULT: fill, HOVERED: role("accent") if current else role("rail_hover")},
        shape=ft.RoundedRectangleBorder(radius=RADIUS - 2),
        padding=ft.Padding.symmetric(horizontal=0 if compact else inset),
        alignment=ft.Alignment.CENTER if compact else ft.Alignment.CENTER_LEFT,
        elevation=0,
    )
