"""A stand-in for flet's ``Page``: the attributes and calls ``FletPage`` uses, recorded. flet's own
page needs its window program connected; this one needs nothing."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, cast

import flet as ft


class StubLoop:
    def __init__(self, *, closed: bool = False) -> None:
        self.closed = closed
        self.later: list[tuple[float, Callable[[], None]]] = []

    def call_soon_threadsafe(self, function: Callable[..., object], *args: Any) -> None:
        if self.closed:
            raise RuntimeError("Event loop is closed")
        function(*args)

    def call_later(self, seconds: float, callback: Callable[[], None]) -> None:
        self.later.append((seconds, callback))

    def run_all(self) -> None:
        while self.later:
            self.later.pop(0)[1]()


class StubPage:
    def __init__(self, *, closed: bool = False) -> None:
        self.window = ft.Window()
        self.loop = StubLoop(closed=closed)
        self.padding: object = None
        self.spacing: object = None
        self.title: str | None = None
        self.theme: ft.Theme | None = None
        self.dark_theme: ft.Theme | None = None
        self.theme_mode: ft.ThemeMode | None = None
        self.added: list[ft.Control] = []
        self.dialogs: list[ft.AlertDialog] = []
        self.tasks: list[Callable[[], Coroutine[Any, Any, Any]]] = []
        self.updates = 0
        self.on_keyboard_event: Any = None
        self.on_resize: Any = None

    def add(self, *controls: ft.Control) -> None:
        self.added.extend(controls)

    def update(self) -> None:
        self.updates += 1

    def show_dialog(self, dialog: ft.AlertDialog) -> None:
        dialog.open = True
        self.dialogs.append(dialog)

    def pop_dialog(self) -> None:
        self.dialogs.pop().open = False

    def run_task(self, handler: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        self.tasks.append(handler)

    def run_tasks(self) -> None:
        """Run the coroutines handed to the page's loop (the pickers' questions)."""
        while self.tasks:
            asyncio.run(self.tasks.pop(0)())

    def as_page(self) -> ft.Page:
        return cast(ft.Page, self)
