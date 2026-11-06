"""A dialog in ClearMD's look (ADR-0027): modal, over the window, a body and a row of actions at
the foot. The window shows it, closes it on Esc (``close_dialog``) and gives Enter to its default
action (``press_default``)."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import MARGIN, SPACE
from clearmd.frontend.flet.components.primitives import label
from clearmd.frontend.flet.layout.units import DIALOG_WIDTH
from clearmd.frontend.flet.visuals.theme import role


class Dialog:
    """A body and a row of actions at the foot; ``on_close`` once, however it is closed."""

    def __init__(
        self,
        *,
        title: str,
        on_close: Callable[[], None],
        width: int = DIALOG_WIDTH,
        scrolls: bool = False,
    ) -> None:
        self._on_close = on_close
        self._finished = False
        self._default: Callable[[], None] = self.close_dialog
        self.dismiss: Callable[[], None] = lambda: None  # the window's: takes it off the screen
        # ``scrolls``: a long dialog (Settings) scrolls when the window is too short for it, its
        # actions staying visible. Only then: a scrolling body takes all the height it is given,
        # so a short question would stand in a tall empty box (v1.0.1).
        self.body = ft.Column(spacing=0, tight=True, scroll=ft.ScrollMode.AUTO if scrolls else None)
        self.foot = ft.Row(spacing=SPACE, alignment=ft.MainAxisAlignment.END)
        self.title = label("dialogTitle", title)
        self.control = ft.AlertDialog(
            modal=True,  # a click beside it does nothing: it closes by its buttons or Esc
            title=self.title,
            content=ft.Container(content=self.body, width=width),
            actions=[self.foot],
            bgcolor=role("ground"),
            title_padding=ft.Padding.only(left=MARGIN, top=MARGIN, right=MARGIN),
            content_padding=ft.Padding.all(MARGIN),
            actions_padding=ft.Padding.only(left=MARGIN, right=MARGIN, bottom=MARGIN),
            on_dismiss=self._finish,  # closed by flet's program itself
        )

    def close_dialog(self) -> None:
        if not self._finished:
            self.dismiss()
            self._finish()

    def default(self, action: Callable[[], None]) -> None:
        """What Enter does while the dialog is open (Qt's default button)."""
        self._default = action

    def press_default(self) -> None:
        self._default()

    def texts(self) -> list[str]:
        """Every text the dialog shows (for tests)."""
        found: list[str] = []
        stack: list[object] = [self.control]
        while stack:
            control = stack.pop()
            if isinstance(control, ft.Text) and control.value:
                found.append(str(control.value))
            for name in ("title", "content", "controls", "actions", "label"):
                value = getattr(control, name, None)
                if isinstance(value, list):
                    stack.extend(reversed(value))
                elif isinstance(value, ft.Control):
                    stack.append(value)
                elif name in {"label", "content"} and isinstance(value, str) and value:
                    found.append(value)  # a box's label, a button's text
        return found

    def _finish(self) -> None:
        if not self._finished:
            self._finished = True
            self._on_close()
