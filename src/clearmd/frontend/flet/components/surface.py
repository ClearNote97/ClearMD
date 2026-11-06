"""The working area (ADR-0027): its soft shape at the top right and the header (step, title,
subtitle); the page goes below the header."""

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF
from clearmd.frontend.flet.components.primitives import label
from clearmd.frontend.flet.visuals.theme import role


def _shape(width: int, height: int, *, right: int, top: int) -> ft.Container:
    """One of the soft shapes, in the theme's shape colour (Qt draws ellipses; these are their
    rounded outlines), placed from the area's top right corner."""
    return ft.Container(
        width=width,
        height=height,
        right=right,
        top=top,
        bgcolor=role("shape"),
        border_radius=ft.BorderRadius.all(min(width, height) // 2),
    )


class Surface:
    """The working area: its soft shape at the top right, the header (step, title, subtitle),
    then ``body``, which takes the rest."""

    def __init__(self, body: ft.Control) -> None:
        self.eyebrow = label("eyebrow")
        self.title = label("title")
        self.subtitle = label("subtitle")
        header = ft.Column([self.eyebrow, self.title, self.subtitle], spacing=HALF)
        # The window's own margin is the gutter above and below: the page ends where the rail ends.
        content = ft.Container(
            content=ft.Column([header, body], spacing=GAP, expand=True),
            padding=ft.Padding.symmetric(horizontal=GAP),
            left=0,
            top=0,
            right=0,
            bottom=0,
        )
        # As Qt's: at (width - 380, -260), 640 × 360; at (width - 560, -300), 380 × 360.
        self.shapes = [
            _shape(640, 360, right=380 - 640, top=-260),
            _shape(380, 360, right=560 - 380, top=-300),
        ]
        self.control = ft.Stack(
            [*self.shapes, content], expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE
        )

    def show_header(self, *, eyebrow: str, title: str, subtitle: str) -> None:
        self.eyebrow.value = eyebrow
        self.title.value = title
        self.subtitle.value = subtitle
