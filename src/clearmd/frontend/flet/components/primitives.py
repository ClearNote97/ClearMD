"""The small controls every other one is made of: a text of a kind, a button, a rounded card, a
gap, one choice among radio buttons, and the texts a piece takes from the catalog.

flet's controls are plain objects: they are built, changed and read here without a window; the
window sends what changed to flet's program."""

from collections.abc import Callable, Sequence

import flet as ft

from clearmd.frontend.design.metrics import BUTTON_HEIGHT, GAP, RADIUS, SPACE
from clearmd.frontend.flet.visuals.look import button_style, paint, text_style
from clearmd.frontend.flet.visuals.theme import role
from clearmd.i18n import Catalog

Worded = ft.Text | ft.Button | ft.Radio | ft.Checkbox


def label(kind: str, value: str = "", *, expand: bool = False) -> ft.Text:
    return paint(ft.Text(value, expand=expand or None), kind)


def button(kind: str, on_click: Callable[[], None] | None = None, text: str = "") -> ft.Button:
    """A button of a kind (``""``, ``primary``, ``strong``, ``link``); its text is its content."""
    return ft.Button(
        content=text, style=button_style(kind), height=BUTTON_HEIGHT, on_click=on_click
    )


def restyle(widget: ft.Button, kind: str) -> None:
    widget.style = button_style(kind)


def card(
    controls: Sequence[ft.Control],
    *,
    padding: int = GAP,
    spacing: int = SPACE,
    expand: bool = False,
) -> ft.Container:
    """A rounded card holding ``controls`` one under the other, ``padding`` on every side."""
    return ft.Container(
        content=ft.Column(list(controls), spacing=spacing, tight=not expand, expand=expand or None),
        padding=ft.Padding.all(padding),
        bgcolor=role("card"),
        border=ft.Border.all(1, role("border")),
        border_radius=ft.BorderRadius.all(RADIUS),
        expand=expand or None,
    )


def gap(height: int) -> ft.Container:
    """Room between two controls of a column."""
    return ft.Container(height=height)


def stretch() -> ft.Container:
    """The room left in a row, so what follows goes to its end."""
    return ft.Container(expand=True)


class Choice:
    """One value among radio buttons (a ``RadioGroup``): ``choose`` is the user's click."""

    def __init__(
        self,
        values: Sequence[str],
        on_choose: Callable[[str], None] | None = None,
        *,
        spacing: int = GAP,
    ) -> None:
        self._on_choose = on_choose
        self.radios = {
            value: ft.Radio(value=value, label_style=text_style("onPage")) for value in values
        }
        self.row = ft.Row(list(self.radios.values()), spacing=spacing, tight=True)
        self.control = ft.RadioGroup(content=self.row, value=values[0], on_change=self._changed)

    @property
    def value(self) -> str:
        return str(self.control.value)

    def set(self, value: str) -> None:
        """Show ``value`` chosen (the presenter's choice), without telling anyone."""
        self.control.value = value

    def choose(self, value: str) -> None:
        """The user picks ``value``: as a click on its radio button."""
        self.control.value = value
        self._changed()

    def set_disabled(self, disabled: bool) -> None:
        for radio in self.radios.values():
            radio.disabled = disabled

    def _changed(self) -> None:
        if self._on_choose is not None:
            self._on_choose(self.value)


class Wording:
    """The controls of a piece and their catalog keys: a language change rewrites them all."""

    def __init__(self) -> None:
        self._keys: list[tuple[Worded, str]] = []

    def add(self, control: Worded, key: str) -> None:
        self._keys.append((control, key))

    def apply(self, catalog: Catalog) -> None:
        for control, key in self._keys:
            text = catalog.text(key)
            if isinstance(control, ft.Text):
                control.value = text
            elif isinstance(control, ft.Button):
                control.content = text
            else:
                control.label = text
