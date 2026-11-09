"""``FletPage``, the window's port on flet's real page (feature 018): the window's sizes and close
button, the theme, the dialogs, the work queued to the page's loop, the pickers and the events."""

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import flet as ft
import pytest
from support.flet_page_stub import StubPage

from clearmd.frontend.design.metrics import MIN_HEIGHT, MIN_WIDTH, START_HEIGHT, START_WIDTH
from clearmd.frontend.flet.layout.units import FRAME_HEIGHT, FRAME_WIDTH
from clearmd.frontend.flet.window.flet_page import FletPage
from clearmd.frontend.flet.window.page_port import KeyPress


class FakePicker:
    files: list[ft.FilePickerFile] = []
    folder: str | None = None
    asked: list[dict[str, Any]] = []

    async def pick_files(self, **options: Any) -> list[ft.FilePickerFile]:
        self.asked.append(options)
        return self.files

    async def get_directory_path(self, **options: Any) -> str | None:
        self.asked.append(options)
        return self.folder


@pytest.fixture
def picker(monkeypatch: pytest.MonkeyPatch) -> type[FakePicker]:
    monkeypatch.setattr(ft, "FilePicker", FakePicker)  # the one flet_page makes
    FakePicker.asked = []
    return FakePicker


def test_the_window_has_clearmds_sizes_and_its_close_button_only_asks() -> None:
    stub = StubPage()
    FletPage(stub.as_page())
    window = stub.window
    # The shared sizes are the page's; flet's window adds its frame (layout/units.py).
    frame = (FRAME_WIDTH, FRAME_HEIGHT)
    assert (window.width, window.height) == (START_WIDTH + frame[0], START_HEIGHT + frame[1])
    assert (window.min_width, window.min_height) == (MIN_WIDTH + frame[0], MIN_HEIGHT + frame[1])
    assert window.prevent_close is True and window.icon and Path(window.icon).is_file()
    assert stub.padding == 0 and stub.spacing == 0


def test_mount_title_theme_refresh_and_dialogs() -> None:
    stub = StubPage()
    page = FletPage(stub.as_page())
    root = ft.Container()
    page.mount(root)
    page.set_title("ClearMD")
    light, dark = ft.Theme(), ft.Theme()
    page.set_theme(light, dark, ft.ThemeMode.DARK)
    page.refresh()
    assert stub.added == [root] and stub.title == "ClearMD" and stub.updates == 1
    assert (stub.theme, stub.dark_theme, stub.theme_mode) == (light, dark, ft.ThemeMode.DARK)
    dialog = ft.AlertDialog()
    page.show_dialog(dialog)
    assert stub.dialogs == [dialog] and dialog.open
    page.close_dialog(dialog)
    page.close_dialog(dialog)  # already closed: nothing else is popped
    assert stub.dialogs == [] and not dialog.open


def test_work_is_queued_to_the_loop_and_the_screen_refreshed_after_it() -> None:
    stub = StubPage()
    page = FletPage(stub.as_page())
    ran: list[str] = []
    page.post(0.25, lambda: ran.append("work"))
    assert ran == [] and stub.loop.later[0][0] == 0.25
    stub.loop.run_all()
    assert ran == ["work"] and stub.updates == 1
    closed = StubPage(closed=True)
    FletPage(closed.as_page()).post(0, lambda: ran.append("late"))  # the window is gone: dropped
    assert ran == ["work"]


class _Card:
    """A control that counts the times it is sent alone."""

    def __init__(self) -> None:
        self.sent = 0

    def update(self) -> None:
        self.sent += 1


def test_a_narrowed_callback_sends_only_its_controls_not_the_page() -> None:
    stub = StubPage()
    page = FletPage(stub.as_page())
    card = _Card()
    page.post(0, lambda: page.narrow(cast(ft.Control, card)))  # a progress tick
    stub.loop.run_all()
    assert card.sent == 1 and stub.updates == 0  # flet's program redraws the card alone
    page.post(0, lambda: None)  # anything else: the whole page, as before
    stub.loop.run_all()
    assert card.sent == 1 and stub.updates == 1


def test_the_pickers_ask_on_the_loop_and_answer_with_paths(picker: type[FakePicker]) -> None:
    stub = StubPage()
    page = FletPage(stub.as_page())
    picker.files = [
        ft.FilePickerFile(id=1, name="a.pdf", size=1, path="/docs/a.pdf"),
        ft.FilePickerFile(id=2, name="web", size=1, path=None),  # no path (the web): skipped
    ]
    picker.folder = "/docs"
    answers: list[object] = []
    page.pick_files("Choose documents", ["pdf", "docx"], answers.append)
    page.pick_folder("Choose a folder", "/home", answers.append)
    assert answers == []  # asked later, on the page's loop
    stub.run_tasks()
    assert answers == [["/docs/a.pdf"], "/docs"] and stub.updates == 2
    files, folder = picker.asked
    assert files["allow_multiple"] and files["allowed_extensions"] == ["pdf", "docx"]
    assert files["file_type"] is ft.FilePickerFileType.CUSTOM
    assert folder == {"dialog_title": "Choose a folder", "initial_directory": "/home"}


def test_keys_the_close_button_and_the_size_reach_the_window() -> None:
    stub = StubPage()
    page = FletPage(stub.as_page())
    keys: list[KeyPress] = []
    closes: list[bool] = []
    sizes: list[tuple[float, float]] = []
    page.listen(
        on_key=keys.append,
        on_close=lambda: closes.append(True),
        on_resize=lambda width, height: sizes.append((width, height)),
    )
    stub.on_keyboard_event(SimpleNamespace(key="1", ctrl=False, meta=True, shift=False))
    window_event = cast(Callable[[object], None], stub.window.on_event)
    window_event(SimpleNamespace(type=ft.WindowEventType.FOCUS))
    window_event(SimpleNamespace(type=ft.WindowEventType.CLOSE))
    stub.on_resize(SimpleNamespace(width=900.0, height=700.0))
    assert keys == [KeyPress("1", ctrl=True)]  # Cmd on a Mac is Ctrl
    assert closes == [True] and sizes == [(900.0, 700.0)]


def test_hide_and_destroy() -> None:
    stub = StubPage()
    page = FletPage(stub.as_page())
    page.hide()
    assert stub.window.visible is False and stub.updates == 1
    page.destroy()
    assert stub.tasks == [stub.window.destroy]  # flet's program ends; ``ft.run`` returns


class FakeClipboard:
    copied: list[str] = []

    async def set(self, value: str) -> None:
        self.copied.append(value)


def test_copy_text_sets_flets_clipboard_on_the_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    """flet 1.0.5: the clipboard is a page service whose ``set`` is a coroutine (036)."""
    monkeypatch.setattr(ft, "Clipboard", FakeClipboard)  # the one flet_page makes
    FakeClipboard.copied = []
    stub = StubPage()
    page = FletPage(stub.as_page())
    page.copy_text("ClearMD 2.9 · flet · <file>.pdf")
    assert FakeClipboard.copied == []  # set later, on the page's loop
    stub.run_tasks()
    assert FakeClipboard.copied == ["ClearMD 2.9 · flet · <file>.pdf"]
