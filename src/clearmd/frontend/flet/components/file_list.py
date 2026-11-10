"""A numbered list of files (ADR-0027): ``#``, the file's icon and name, the extra columns, a
message in place of an empty list; optionally a box on each row."""

from collections.abc import Callable, Sequence
from typing import Any

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF, RADIUS, SPACE
from clearmd.frontend.flet.components.list_line import Line as Line
from clearmd.frontend.flet.components.list_line import ListRow as ListRow
from clearmd.frontend.flet.components.list_line import build_line
from clearmd.frontend.flet.components.list_line import size as size
from clearmd.frontend.flet.components.primitives import card, label
from clearmd.frontend.flet.components.row_tone import tint
from clearmd.frontend.flet.layout.units import CHECK_WIDTH, NUMBER_WIDTH
from clearmd.frontend.flet.visuals.theme import role


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
        wrap: bool = False,
    ) -> None:
        self.checks = checks
        self._wrap = wrap  # a list to read: its texts wrapped whole (040)
        # The window's: brings a row into view (the list scrolls on flet's side), after the arrows.
        self.on_reveal: Callable[[ft.ListView, int], None] | None = None
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
            size(cell, index, self._widths)
            cells.append(cell)
        self.header.controls = cells
        self.empty.value = empty
        self._show_which()

    def show_rows(self, rows: Sequence[ListRow]) -> None:
        self._rows = tuple(rows)
        self._selected.clear()
        self.lines = [
            build_line(index, row, self._widths, self._wrap, self.toggle if self.checks else None,
                       self.click)
            for index, row in enumerate(self._rows)
        ]  # fmt: skip
        self.list.controls = [line.frame for line in self.lines]
        self._show_which()

    def rows(self) -> tuple[ListRow, ...]:
        return self._rows

    def selected_rows(self) -> list[ListRow]:
        return [self._rows[index] for index in sorted(self._selected)]

    def selected(self) -> list[Any]:
        """What the selected rows stand for (their payloads)."""
        return [row.payload for row in self.selected_rows()]

    def holds(self, control: object) -> bool:
        """Whether ``control`` is one of the list's own (a row's box): the list has the focus."""
        return any(line.box is control for line in self.lines)

    def current(self) -> ListRow | None:
        chosen = self.selected_rows()
        return chosen[0] if chosen else None

    def select(self, index: int) -> None:
        """Only this row selected (a list to read: the row whose detail is shown)."""
        if 0 <= index < len(self._rows):
            self._set({index})

    def step(self, offset: int) -> None:
        """The arrow keys (040): the next or previous row selected, the first or last when none
        is, and brought into view."""
        if not self._rows:
            return
        last = len(self._rows) - 1
        current = min(self._selected) if self._selected else (-1 if offset > 0 else last + 1)
        index = max(0, min(last, current + offset))
        self.select(index)
        if self.on_reveal is not None:
            self.on_reveal(self.list, index)

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

    def _show_which(self) -> None:
        empty = not self._rows and bool(self.empty.value)
        self.table.visible = not empty
        self.placeholder.visible = empty
