"""A list row's tone (features 035, 039): its texts in the tone's colour while unselected, and a
mark at its left edge that the selection never erases, so the row's kind stays visible when it is
selected (audit v3, F3-03: the warning and danger colours fall under 4.5:1 on the selection in
one theme each; the mark, a graphic, keeps above 3:1 in both)."""

from collections.abc import Sequence

import flet as ft

from clearmd.frontend.design.metrics import HALF
from clearmd.frontend.flet.visuals.theme import role


def tint(texts: Sequence[ft.Text], tone: str) -> None:
    """A row's texts in its tone's colour, or the page's text colour."""
    for text in texts:
        text.color = role(tone or "text")


def mark(tone: str) -> ft.Border | None:
    """The tone's mark: a bar at the row's left edge (``None``: a row without a tone)."""
    return ft.Border(left=ft.BorderSide(HALF, role(tone))) if tone else None
