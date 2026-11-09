"""How far a long conversion has got, told from inside the worker (audit 2026-11-08, decision 3B).

A converter that walks pages calls ``report(done, total)``; the worker sends it on to the
supervisor, at most once a second, as ``Progress``. The supervisor then counts the time limit
from the last progress, not from the start: a long file that keeps moving finishes, a stuck one
stops. Outside the worker nothing listens and ``report`` costs nothing.
"""

import time
from collections.abc import Callable

INTERVAL = 1.0  # seconds between two reports sent on

_listener: Callable[[int, int], None] | None = None
_last = 0.0


def listen(listener: Callable[[int, int], None] | None) -> None:
    global _listener, _last
    _listener, _last = listener, 0.0


def report(done: int, total: int) -> None:
    global _last
    if _listener is None:
        return
    now = time.monotonic()
    if now - _last >= INTERVAL or done >= total:
        _last = now
        _listener(done, total)
