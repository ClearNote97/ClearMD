"""Closing a test window for sure: a window closed while converting waits for the batch, and
only an event loop gets it there. Left open, its root keeps ttkbootstrap's Style alive and every
later window fails with it (seen on the slower CI runners in 007)."""

import time
from typing import Any

CLOSE_SECONDS = 30.0


def shut(app: Any) -> None:
    app.close()
    deadline = time.monotonic() + CLOSE_SECONDS
    while time.monotonic() < deadline:
        try:
            if not app.root.winfo_exists():
                return
            app.root.update()
        except Exception:  # noqa: BLE001 -- destroyed while updating: closed
            return
        time.sleep(0.01)
    app._destroy()  # still converting after the wait: the test is over, the window goes
