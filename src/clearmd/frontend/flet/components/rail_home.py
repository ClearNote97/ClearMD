"""Home on the rail (feature 023): above the steps, a house in place of a number; highlighted
while the start screen is on screen, as a step is."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.flet.components.primitives import label
from clearmd.frontend.flet.components.rail_art import rail_style
from clearmd.frontend.flet.layout.units import BADGE, STEP_HEIGHT
from clearmd.frontend.flet.visuals.look import paint
from clearmd.frontend.flet.visuals.theme import role


class RailHome:
    def __init__(self, on_home: Callable[[], None]) -> None:
        self.icon = ft.Icon(ft.Icons.HOME_OUTLINED, size=BADGE)
        self.name = label("rail")
        self.button = ft.Button(
            content=ft.Row([self.icon, self.name], spacing=SPACE),
            height=STEP_HEIGHT,
            on_click=on_home,
        )

    def draw(self, word: str, *, current: bool, compact: bool) -> None:
        self.name.value = word
        self.name.visible = not compact
        paint(self.name, "railCurrent" if current else "rail")
        self.icon.color = role("on_accent" if current else "rail_dim")
        self.button.tooltip = word
        self.button.style = rail_style(current=current, compact=compact)
