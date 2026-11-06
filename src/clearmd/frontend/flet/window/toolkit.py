"""The start inside flet: what ``ft.run`` calls once its window program is connected. A module of
its own: the one place that turns flet's page into ClearMD's window."""

import flet as ft

import clearmd.frontend.launch as launch
from clearmd.frontend.flet.window.flet_page import FletPage
from clearmd.frontend.flet.window.window import FletApp


def open_window(page: ft.Page, *, smoke: bool = False) -> FletApp:
    """ClearMD's window on ``page``. ``smoke``: it closes by itself after a few seconds (CI
    checks that the executable starts, ADR-0028)."""
    app = FletApp(FletPage(page))
    app.start()
    if smoke:
        app.after(launch.SMOKE_SECONDS * 1000, app.close)
    return app
