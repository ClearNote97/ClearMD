"""A page that is not flet's, for the flet window's tests (feature 018): ``PagePort`` without
flet's program. It keeps what the window shows, answers the pickers with what a test sets, and
runs the work queued to the page's loop when the test pumps it, on the test's own thread (the
window's "UI thread")."""

import itertools
import threading
import time
from collections.abc import Callable, Sequence

import flet as ft

from clearmd.frontend.flet.window.page_port import KeyPress


class FakePage:
    """``PagePort`` without flet's program."""

    def __init__(self) -> None:
        self.root: ft.Control | None = None
        self.title = ""
        self.themes: tuple[ft.Theme, ft.Theme] | None = None
        self.mode: ft.ThemeMode | None = None
        self.dialogs: list[ft.AlertDialog] = []
        self.files: list[str] = []  # what the next files picker answers
        self.folder: str | None = None  # what the next folder picker answers (None: cancelled)
        self.asked: list[tuple[str, str, str | None]] = []  # (picker, title, start folder)
        self.extensions: list[str] = []
        self.hidden = self.destroyed = False
        self.refreshes = 0  # whole-page refreshes
        self.narrowed: list[ft.Control] = []  # every control sent alone (a progress tick)
        self._narrowing: list[ft.Control] = []
        self._queue: list[tuple[float, int, Callable[[], None]]] = []
        self._lock = threading.Lock()
        self._order = itertools.count()
        self._on_key: Callable[[KeyPress], None] = lambda key: None
        self._on_close: Callable[[], None] = lambda: None
        self._on_resize: Callable[[float, float], None] = lambda width, height: None

    def mount(self, root: ft.Control) -> None:
        self.root = root
        self.refreshes += 1

    def refresh(self) -> None:
        self.refreshes += 1

    def narrow(self, *controls: ft.Control) -> None:
        self._narrowing.extend(controls)

    def set_title(self, title: str) -> None:
        self.title = title

    def set_theme(self, light: ft.Theme, dark: ft.Theme, mode: ft.ThemeMode) -> None:
        self.themes, self.mode = (light, dark), mode

    def show_dialog(self, dialog: ft.AlertDialog) -> None:
        dialog.open = True
        self.dialogs.append(dialog)

    def close_dialog(self, dialog: ft.AlertDialog) -> None:
        dialog.open = False
        self.dialogs.remove(dialog)

    def post(self, seconds: float, callback: Callable[[], None]) -> None:
        with self._lock:
            self._queue.append((time.monotonic() + seconds, next(self._order), callback))

    def run_due(self) -> None:
        """Run what is due on the page's loop, in order, then refresh (as the real page does)."""
        while True:
            with self._lock:
                due = sorted(item for item in self._queue if item[0] <= time.monotonic())
                if not due:
                    return
                self._queue.remove(due[0])
            self._narrowing = []
            due[0][2]()
            if self._narrowing:
                self.narrowed.extend(self._narrowing)  # as the real page: only these are sent
            else:
                self.refreshes += 1

    def pick_files(
        self, title: str, extensions: Sequence[str], done: Callable[[list[str]], None]
    ) -> None:
        self.asked.append(("files", title, None))
        self.extensions = list(extensions)
        done(list(self.files))

    def pick_folder(
        self, title: str, start: str | None, done: Callable[[str | None], None]
    ) -> None:
        self.asked.append(("folder", title, start))
        done(self.folder)

    def listen(
        self,
        *,
        on_key: Callable[[KeyPress], None],
        on_close: Callable[[], None],
        on_resize: Callable[[float, float], None],
    ) -> None:
        self._on_key, self._on_close, self._on_resize = on_key, on_close, on_resize

    def hide(self) -> None:
        self.hidden = True

    def destroy(self) -> None:
        self.destroyed = True

    # --- What the user does to the window -------------------------------------------------------

    def press(self, key: str, *, ctrl: bool = False) -> None:
        self._on_key(KeyPress(key, ctrl=ctrl))

    def close_button(self) -> None:
        """The window's own close button: it only asks (``prevent_close``)."""
        self._on_close()

    def resize(self, width: float, height: float) -> None:
        self._on_resize(width, height)
