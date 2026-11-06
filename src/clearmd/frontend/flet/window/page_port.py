"""What the window needs from flet's page: a port, so the window is built and tested without
flet's program (no screen, no network), and one adapter (``flet_page.py``) to the real page.

A module of its own: the window speaks to this protocol only; nothing else knows ``ft.Page``.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

import flet as ft


@dataclass(frozen=True)
class KeyPress:
    """A key pressed on the window: its name as flet gives it ("Enter", "Escape", "1"…)."""

    key: str
    ctrl: bool = False  # Ctrl, or Cmd on a Mac
    shift: bool = False


class PagePort(Protocol):
    def mount(self, root: ft.Control) -> None:
        """Put the window's controls on the page and send them to the screen."""

    def refresh(self) -> None:
        """Send what changed in the controls to the screen."""

    def set_title(self, title: str) -> None: ...

    def set_theme(self, light: ft.Theme, dark: ft.Theme, mode: ft.ThemeMode) -> None: ...

    def show_dialog(self, dialog: ft.AlertDialog) -> None: ...

    def close_dialog(self, dialog: ft.AlertDialog) -> None: ...

    def post(self, seconds: float, callback: Callable[[], None]) -> None:
        """Run ``callback`` on the page's loop after ``seconds``, then refresh the screen (only
        the controls ``narrow`` named, if it was called). Safe to call from any thread."""

    def narrow(self, *controls: ft.Control) -> None:
        """The running ``post`` callback changed only these controls: only they are sent. flet's
        program redraws all it is sent: the whole page each second slowed the conversion 4x on
        the owner's computer (v1.0.1); the progress card alone costs nothing."""

    def pick_files(
        self, title: str, extensions: Sequence[str], done: Callable[[list[str]], None]
    ) -> None:
        """The system's dialog for several files; ``done`` gets the chosen paths (none:
        cancelled), on the page's loop."""

    def pick_folder(
        self, title: str, start: str | None, done: Callable[[str | None], None]
    ) -> None:
        """The system's dialog for a folder; ``done`` gets it (``None``: cancelled)."""

    def listen(
        self,
        *,
        on_key: Callable[[KeyPress], None],
        on_close: Callable[[], None],
        on_resize: Callable[[float, float], None],
    ) -> None:
        """The keyboard, the window's close button (which only asks) and its size."""

    def hide(self) -> None: ...

    def destroy(self) -> None:
        """Close the window for good: flet's program ends, and ``ft.run`` returns."""
