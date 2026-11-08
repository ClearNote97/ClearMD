"""Merge's order (feature 032): on each row of step 1's list, ▲ moves the document one place up
and ▼ one place down; the first cannot go up, the last cannot go down."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import HALF, SPACE
from clearmd.frontend.flet.visuals.theme import role

ARROW = 4 * SPACE  # 32: the button fits a list row (36)
ARROW_ICON = 2 * SPACE + HALF  # 20


def arrow(
    icon: ft.IconData, tooltip: str, enabled: bool, on_click: Callable[[], None]
) -> ft.IconButton:
    return ft.IconButton(
        icon=icon,
        icon_size=ARROW_ICON,
        # the colour follows the state: flet keeps an explicit icon_color when disabled
        icon_color=role("accent_text") if enabled else role("disabled"),
        disabled_color=role("disabled"),
        tooltip=tooltip,
        disabled=not enabled,
        width=ARROW,
        height=ARROW,
        style=ft.ButtonStyle(padding=ft.Padding.all(0)),
        visual_density=ft.VisualDensity.COMPACT,
        on_click=on_click,
    )


def order_cell(
    *,
    up: bool,
    down: bool,
    on_move: Callable[[int], None],
    tooltips: tuple[str, str],
) -> ft.Row:
    """▲ and ▼ for one row: ``on_move(-1)`` or ``on_move(+1)``, enabled as the presenter says."""
    return ft.Row(
        [
            arrow(ft.Icons.ARROW_UPWARD, tooltips[0], up, lambda: on_move(-1)),
            arrow(ft.Icons.ARROW_DOWNWARD, tooltips[1], down, lambda: on_move(+1)),
        ],
        spacing=0,
        tight=True,
    )
