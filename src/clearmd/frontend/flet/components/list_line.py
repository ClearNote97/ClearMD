"""One row of a ``FileList`` (ADR-0027): the row's data (``ListRow``), what is on screen
(``Line``) and how it is built. A module of its own: the list keeps its state and events.
A list to read (Review, Results) wraps its texts whole, never cut (feature 040, F3-01)."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
from typing import Any

import flet as ft

from clearmd.frontend.design.metrics import RADIUS, SPACE
from clearmd.frontend.flet.components.primitives import label
from clearmd.frontend.flet.components.row_tone import mark, tint
from clearmd.frontend.flet.layout.units import CHECK_WIDTH, ICON, NUMBER_WIDTH, ROW_HEIGHT
from clearmd.frontend.flet.visuals.images import icon_src


@dataclass(frozen=True)
class ListRow:
    icon: str
    name: str
    values: tuple[str, ...]  # one per extra column
    tone: str = ""  # its texts' colour role ("warning", "danger"; "": the page's text), 035
    payload: Any = None  # what the row stands for (a path), returned by ``selected``
    extra: ft.LayoutControl | None = None  # a last cell of its own (Merge's ▲ ▼, feature 032)


def size(cell: ft.LayoutControl, column: int, widths: Sequence[int | None]) -> None:
    """A column's width; the last one takes what is left."""
    width = widths[column] if column < len(widths) else None
    if width is None or column == len(widths) - 1:
        cell.expand = True
    else:
        cell.width = width


@dataclass(frozen=True)
class Line:
    """A row on screen: its frame, its box (a list with boxes) and its texts."""

    frame: ft.Container
    box: ft.Checkbox | None
    texts: tuple[ft.Text, ...]
    picture: ft.Image


def build_line(
    index: int,
    row: ListRow,
    widths: Sequence[int | None],
    wrap: bool,
    on_toggle: Callable[[int], None] | None,
    on_click: Callable[[int], None],
) -> Line:
    """The row on screen; ``on_toggle``: a box on it (a list whose selection does something)."""
    number = label("onPage", str(index + 1))
    number.width = NUMBER_WIDTH
    picture = ft.Image(src=icon_src(row.icon), width=ICON, height=ICON)
    texts = [label("onPage", text) for text in (row.name, *row.values)]
    for text in texts:
        text.tooltip = text.value
        if not wrap:  # a list to read wraps its texts whole (040); Choose's keeps one line
            text.max_lines, text.overflow = 1, ft.TextOverflow.ELLIPSIS
    tint(texts, row.tone)
    texts[0].expand = True
    name = ft.Row([picture, texts[0]], spacing=SPACE)
    cells: list[ft.LayoutControl] = [number, name, *texts[1:]]
    for column, cell in enumerate(cells[1:]):
        size(cell, column, widths)
    if row.extra is not None:
        cells.append(row.extra)
    box = None
    if on_toggle is not None:
        box = ft.Checkbox(value=False, on_change=partial(on_toggle, index))
        box.width = CHECK_WIDTH
        cells.insert(0, box)
    shown: list[ft.Control] = list(cells)
    frame = ft.Container(
        content=ft.Row(shown, spacing=SPACE),
        height=None if wrap else ROW_HEIGHT,  # a wrapped row grows with its text (040)
        padding=ft.Padding.symmetric(horizontal=SPACE, vertical=SPACE if wrap else 0),
        # The arrows bring the selected row into view (040); flet's stub misses the value.
        key=ft.ScrollKey(index),  # type: ignore[call-arg]
        border_radius=ft.BorderRadius.all(RADIUS // 2),
        border=mark(row.tone),  # kept when selected (039)
        on_click=partial(on_click, index),  # flet passes no event to it
    )
    return Line(frame, box, tuple(texts), picture)
