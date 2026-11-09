"""A numbered list of files (ADR-0027): ``#``, the file's icon and name, the extra columns, a
message in place of an empty list; optionally a box on each row."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
from typing import Any

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF, RADIUS, SPACE
from clearmd.frontend.flet.components.primitives import card, label
from clearmd.frontend.flet.layout.units import CHECK_WIDTH, ICON, NUMBER_WIDTH, ROW_HEIGHT
from clearmd.frontend.flet.visuals.images import icon_src
from clearmd.frontend.flet.visuals.theme import role


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


def tint(texts: Sequence[ft.Text], tone: str) -> None:
    """A row's texts in its tone's colour, or the page's text colour."""
    for text in texts:
        text.color = role(tone or "text")


@dataclass(frozen=True)
class Line:
    """A row on screen: its frame, its box (a list with boxes) and its texts."""

    frame: ft.Container
    box: ft.Checkbox | None
    texts: tuple[ft.Text, ...]
    picture: ft.Image


class FileList:
    """``#``, the file's icon and name, then the extra columns; a message in place of an empty
    list. ``checks``: a box on each row, for a list whose selection does something (Choose's
    Remove selected); a click there checks or unchecks. A list to read has none: a click selects
    its row (feature 014)."""

    def __init__(
        self,
        columns: int,
        *,
        checks: bool = False,
        widths: Sequence[int] = (),
        on_selection: Callable[[], None] | None = None,
    ) -> None:
        self.checks = checks
        self._widths = (*widths, *([None] * columns))[: columns + 1]
        self._rows: tuple[ListRow, ...] = ()
        self._selected: set[int] = set()
        self._on_selection = on_selection
        self.lines: list[Line] = []
        self.header = ft.Row(spacing=SPACE)
        self.list = ft.ListView(spacing=0, expand=True)
        self.table = card([self.header, self.list], padding=SPACE, spacing=HALF, expand=True)
        self.empty = label("empty")
        self.empty.text_align = ft.TextAlign.CENTER
        # Empty: the list's own frame with its sentence in the middle, as in Qt.
        self.placeholder = ft.Container(
            content=self.empty,
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=ft.Padding.all(GAP),
            bgcolor=role("card"),
            border=ft.Border.all(1, role("border")),
            border_radius=ft.BorderRadius.all(RADIUS),
        )
        self.control = ft.Column(
            [self.table, self.placeholder],
            spacing=0,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self._show_which()

    def apply_headings(self, headings: Sequence[str], empty: str) -> None:
        first = label("strong", "#")
        first.color = role("muted")
        first.width = NUMBER_WIDTH + (CHECK_WIDTH if self.checks else 0)
        cells: list[ft.Control] = [first]
        for index, heading in enumerate(headings):
            cell = label("strong", heading)
            cell.color = role("muted")
            self._size(cell, index)
            cells.append(cell)
        self.header.controls = cells
        self.empty.value = empty
        self._show_which()

    def show_rows(self, rows: Sequence[ListRow]) -> None:
        self._rows = tuple(rows)
        self._selected.clear()
        self.lines = [self._line(index, row) for index, row in enumerate(self._rows)]
        self.list.controls = [line.frame for line in self.lines]
        self._show_which()

    def rows(self) -> tuple[ListRow, ...]:
        return self._rows

    def selected_rows(self) -> list[ListRow]:
        return [self._rows[index] for index in sorted(self._selected)]

    def selected(self) -> list[Any]:
        """What the selected rows stand for (their payloads)."""
        return [row.payload for row in self.selected_rows()]

    def current(self) -> ListRow | None:
        chosen = self.selected_rows()
        return chosen[0] if chosen else None

    def select(self, index: int) -> None:
        """Only this row selected (a list to read: the row whose detail is shown)."""
        if 0 <= index < len(self._rows):
            self._set({index})

    def toggle(self, index: int) -> None:
        """A row's box clicked: it joins or leaves the selection."""
        if 0 <= index < len(self._rows):
            self._set(self._selected ^ {index})

    def select_all(self) -> None:
        self._set(set(range(len(self._rows))))

    def clear_selection(self) -> None:
        self._set(set())

    def click(self, index: int) -> None:
        """A click on a row: its box on a list with boxes, the row itself on one without."""
        (self.toggle if self.checks else self.select)(index)

    def _set(self, selected: set[int]) -> None:
        self._selected = selected
        for index, line in enumerate(self.lines):
            chosen = index in selected
            line.frame.bgcolor = role("selected") if chosen else None
            tint(line.texts, "" if chosen else self._rows[index].tone)
            if line.box is not None:
                line.box.value = chosen
        if self._on_selection is not None:
            self._on_selection()

    def _line(self, index: int, row: ListRow) -> Line:
        number = label("onPage", str(index + 1))
        number.width = NUMBER_WIDTH
        picture = ft.Image(src=icon_src(row.icon), width=ICON, height=ICON)
        texts = [label("onPage", text) for text in (row.name, *row.values)]
        for text in texts:
            text.max_lines, text.overflow = 1, ft.TextOverflow.ELLIPSIS
            text.tooltip = text.value
        tint(texts, row.tone)
        texts[0].expand = True
        name = ft.Row([picture, texts[0]], spacing=SPACE)
        cells: list[ft.LayoutControl] = [number, name, *texts[1:]]
        for column, cell in enumerate(cells[1:]):
            self._size(cell, column)
        if row.extra is not None:
            cells.append(row.extra)
        box = None
        if self.checks:
            box = ft.Checkbox(value=False, on_change=partial(self.toggle, index))
            box.width = CHECK_WIDTH
            cells.insert(0, box)
        shown: list[ft.Control] = list(cells)
        frame = ft.Container(
            content=ft.Row(shown, spacing=SPACE),
            height=ROW_HEIGHT,
            padding=ft.Padding.symmetric(horizontal=SPACE),
            border_radius=ft.BorderRadius.all(RADIUS // 2),
            on_click=partial(self.click, index),  # flet passes no event to it
        )
        return Line(frame, box, tuple(texts), picture)

    def _size(self, cell: ft.LayoutControl, column: int) -> None:
        size(cell, column, self._widths)

    def _show_which(self) -> None:
        empty = not self._rows and bool(self.empty.value)
        self.table.visible = not empty
        self.placeholder.visible = empty
