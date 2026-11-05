"""A key held down is one press (adversarial check of 007, F-1).

Windows repeats a held key as more presses; X11 as a release and a press with the same time.
Either way a held Enter or Space must not run Next, Next and Convert past pages the user did not
see: only a press after a real release counts. A module of its own: Enter and space both use it.
"""

from typing import Any


class Presses:
    def __init__(self) -> None:
        self._down: set[str] = set()
        self._released_at: dict[str, int] = {}

    def pressed(self, event: Any) -> bool:
        """True for a new press of the key; False while it is held."""
        key = str(event.keysym)
        time = int(getattr(event, "time", 0) or 0)
        repeated = key in self._down or (time and self._released_at.get(key) == time)
        self._down.add(key)
        return not repeated

    def released(self, event: Any) -> None:
        key = str(event.keysym)
        self._down.discard(key)
        self._released_at[key] = int(getattr(event, "time", 0) or 0)
