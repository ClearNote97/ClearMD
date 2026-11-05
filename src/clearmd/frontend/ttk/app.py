"""The ttkbootstrap GUI's entry: build the window and run it (ADR-0026, ADR-0027)."""

import sys
from collections.abc import Sequence

import clearmd.frontend.launch as launch
from clearmd.frontend.ttk.window import toolkit
from clearmd.frontend.ttk.window.window import TtkApp


def main(argv: Sequence[str] | None = None) -> None:
    """``clearmd-ttk``: the window, until it is closed. ``--smoke`` opens it and closes it after
    a few seconds: CI checks that the executable starts (its data, its toolkit)."""
    import multiprocessing

    multiprocessing.freeze_support()  # a no-op unless running as a packaged executable
    arguments = sys.argv[1:] if argv is None else list(argv)
    launch.splash_text(launch.BUILDING_TEXT)
    app = TtkApp(root=toolkit.root_with_drop())
    launch.splash_text(launch.LOADED_TEXT)
    app.start()
    launch.close_splash()
    if launch.is_smoke(arguments):
        app.root.after(launch.SMOKE_SECONDS * 1000, app.close)
    app.root.mainloop()
