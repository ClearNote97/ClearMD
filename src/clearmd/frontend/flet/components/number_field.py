"""A whole number typed in a small box (feature 023): Split's numbers on step 1. It is given when
it is done (Enter, or leaving the box), never on each keystroke."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.flet.layout.units import ROW_HEIGHT
from clearmd.frontend.flet.visuals.look import text_style
from clearmd.frontend.flet.visuals.theme import role

DIGITS = r"^[0-9]*$"


class NumberField:
    """A whole number, given to ``on_number`` on Enter or when the field loses the focus (never on
    each keystroke); ``set`` shows the presenter's number (a refused one is put back). ``width``
    holds its largest number."""

    def __init__(self, on_number: Callable[[int], None], *, width: int) -> None:
        self._on_number = on_number
        self._shown = ""
        self.field = ft.TextField(
            width=width,
            height=ROW_HEIGHT,  # as low as a list row: the block stays short (024)
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=8),
            text_align=ft.TextAlign.RIGHT,
            text_style=text_style("onPage"),
            bgcolor=role("card"),
            border_color=role("border"),
            focused_border_color=role("accent"),
            input_filter=ft.InputFilter(regex_string=DIGITS, allow=True),  # digits only
            on_submit=self.commit,
            on_blur=self.commit,
        )

    def set(self, number: int) -> None:
        self._shown = str(number)
        self.field.value = self._shown

    def type(self, text: str) -> None:
        """The user types ``text`` (tests): nothing is given until it is committed."""
        self.field.value = text

    def commit(self) -> None:
        text = str(self.field.value or "").strip()
        if text == self._shown:
            return
        try:
            number = int(text)
        except ValueError:
            self.field.value = self._shown  # nothing, or not a number: the shown one stays
            return
        self._on_number(number)
