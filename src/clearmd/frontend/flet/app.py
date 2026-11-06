"""The flet GUI's entry: run flet, which opens its window program and builds the window on it."""

import sys
from collections.abc import Sequence

import flet as ft

import clearmd.frontend.launch as launch
from clearmd.frontend.flet.visuals.images import ASSETS
from clearmd.frontend.flet.window.toolkit import open_window


def main(argv: Sequence[str] | None = None) -> int:
    """``clearmd-flet``: the window, until it is closed. ``--smoke`` opens it and closes it
    after a few seconds: CI checks that the executable starts (its data, flet's program)."""
    import multiprocessing

    multiprocessing.freeze_support()  # a no-op unless running as a packaged executable
    smoke = launch.is_smoke(sys.argv[1:] if argv is None else list(argv))

    async def start(page: ft.Page) -> None:  # on flet's loop, like every event after it
        open_window(page, smoke=smoke)

    ft.run(start, assets_dir=str(ASSETS))  # the icons and the logo, named by their path in it
    return 0
