"""Which control has the keyboard focus, as far as the window knows.

flet gives every key to the page, and Flutter also gives Enter and Space to the focused control
(a button runs, a box ticks). So Enter runs the page's primary action, or a dialog's default one,
only while no control of the window has the focus: never both. A module of its own: the keys ask
it, the view and the dialogs tell it what to watch.
"""

import dataclasses
from collections.abc import Callable, Iterator
from functools import partial

import flet as ft

FOCUSABLE = (ft.Button, ft.IconButton, ft.Checkbox, ft.Radio, ft.Dropdown, ft.TextField)


def controls_in(control: ft.BaseControl) -> Iterator[ft.BaseControl]:
    """``control`` and every control inside it (flet's controls are dataclasses)."""
    yield control
    for field in dataclasses.fields(control):
        if field.name.startswith("_"):
            continue
        value = getattr(control, field.name, None)
        for child in value if isinstance(value, list) else [value]:
            if isinstance(child, ft.BaseControl):
                yield from controls_in(child)


class _Watched:
    """A focus handler of the watcher, then the control's own one, if it had one."""

    def __init__(self, own: Callable[[], None], then: object = None) -> None:
        self._own, self._then = own, then

    def __call__(self) -> None:
        self._own()
        if callable(self._then):  # the window's own handlers take no event
            self._then()


class Focus:
    def __init__(self) -> None:
        self.holder: ft.BaseControl | None = None

    @property
    def taken(self) -> bool:
        """Whether a control has the focus: Enter is its own then."""
        return self.holder is not None

    def watch(self, root: ft.BaseControl) -> None:
        """Follow the focus of every control under ``root`` that can take it; a control's own
        blur (a number committed when it is left, feature 023) still runs, after it."""
        for control in controls_in(root):
            if isinstance(control, FOCUSABLE) and not isinstance(control.on_focus, _Watched):
                control.on_focus = _Watched(partial(self._gained, control))
                control.on_blur = _Watched(partial(self._lost, control), control.on_blur)

    def forget(self) -> None:
        """The controls that had it are gone (a closed dialog)."""
        self.holder = None

    def _gained(self, control: ft.BaseControl) -> None:
        self.holder = control

    def _lost(self, control: ft.BaseControl) -> None:
        if self.holder is control:
            self.holder = None
