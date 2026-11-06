"""The real page behind ``PagePort``: flet's ``Page`` and its window, file picker and loop.

Every call that reaches flet's program (a picker, closing the window) is a coroutine: it runs as
a task on the page's loop. Work coming back from other threads (the presenter's planning and
converting) is queued to that loop too, and the screen is refreshed after it.
"""

from collections.abc import Callable, Sequence

import flet as ft

from clearmd.frontend.design.metrics import MIN_HEIGHT, MIN_WIDTH, START_HEIGHT, START_WIDTH
from clearmd.frontend.flet.layout.units import FRAME_HEIGHT, FRAME_WIDTH
from clearmd.frontend.flet.visuals.images import window_icon
from clearmd.frontend.flet.window.page_port import KeyPress


class FletPage:
    """``PagePort`` on flet's page: a window of ClearMD's sizes whose close button only asks."""

    def __init__(self, page: ft.Page) -> None:
        self._page = page
        self._picker = ft.FilePicker()  # a service of the page: made while the page is current
        window = page.window
        # The shared sizes are the page's; flet's window counts its frame too (layout/units.py).
        window.width, window.height = START_WIDTH + FRAME_WIDTH, START_HEIGHT + FRAME_HEIGHT
        window.min_width, window.min_height = MIN_WIDTH + FRAME_WIDTH, MIN_HEIGHT + FRAME_HEIGHT
        window.icon = window_icon()
        window.prevent_close = True  # closing is the window's: it may wait for a batch to end
        page.padding = 0
        page.spacing = 0
        self._narrowed: list[ft.Control] = []  # what the running ``post`` callback narrowed to

    def narrow(self, *controls: ft.Control) -> None:
        self._narrowed.extend(controls)

    def mount(self, root: ft.Control) -> None:
        self._page.add(root)

    def refresh(self) -> None:
        self._page.update()

    def set_title(self, title: str) -> None:
        self._page.title = title

    def set_theme(self, light: ft.Theme, dark: ft.Theme, mode: ft.ThemeMode) -> None:
        self._page.theme, self._page.dark_theme, self._page.theme_mode = light, dark, mode

    def show_dialog(self, dialog: ft.AlertDialog) -> None:
        self._page.show_dialog(dialog)

    def close_dialog(self, dialog: ft.AlertDialog) -> None:
        if dialog.open:
            self._page.pop_dialog()

    def post(self, seconds: float, callback: Callable[[], None]) -> None:
        def run() -> None:
            self._narrowed = []
            callback()
            narrowed, self._narrowed = self._narrowed, []
            if narrowed:
                for control in narrowed:
                    control.update()
            else:
                self._page.update()

        loop = self._page.loop
        try:
            loop.call_soon_threadsafe(loop.call_later, seconds, run)
        except RuntimeError:  # the loop is gone: the window has closed, nothing to draw
            return

    def pick_files(
        self, title: str, extensions: Sequence[str], done: Callable[[list[str]], None]
    ) -> None:
        async def ask() -> None:
            files = await self._picker.pick_files(
                dialog_title=title,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=list(extensions),
                allow_multiple=True,
            )
            done([file.path for file in files if file.path])
            self._page.update()

        self._page.run_task(ask)

    def pick_folder(
        self, title: str, start: str | None, done: Callable[[str | None], None]
    ) -> None:
        async def ask() -> None:
            done(await self._picker.get_directory_path(dialog_title=title, initial_directory=start))
            self._page.update()

        self._page.run_task(ask)

    def listen(
        self,
        *,
        on_key: Callable[[KeyPress], None],
        on_close: Callable[[], None],
        on_resize: Callable[[float, float], None],
    ) -> None:
        def key(event: ft.KeyboardEvent) -> None:
            on_key(KeyPress(event.key, ctrl=event.ctrl or event.meta, shift=event.shift))

        def window_event(event: ft.WindowEvent[ft.Window]) -> None:
            if event.type is ft.WindowEventType.CLOSE:
                on_close()

        def resized(event: ft.PageResizeEvent) -> None:
            on_resize(event.width, event.height)

        self._page.on_keyboard_event = key
        self._page.window.on_event = window_event
        self._page.on_resize = resized

    def hide(self) -> None:
        self._page.window.visible = False
        self._page.update()

    def destroy(self) -> None:
        self._page.run_task(self._page.window.destroy)
