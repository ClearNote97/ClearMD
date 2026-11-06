"""The welcome dialog: the three steps and "Don't show again" (UX §4; AC-14)."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.components.primitives import button, gap, label, stretch
from clearmd.frontend.flet.visuals.look import text_style
from clearmd.i18n import Catalog


class WelcomeDialog(Dialog):
    """The three steps and "Don't show again" (UX §4)."""

    def __init__(
        self, catalog: Catalog, steps: tuple[str, ...], on_done: Callable[[bool], None]
    ) -> None:
        self.dont_show = ft.Checkbox(
            label=catalog.text("gui.welcome.dont_show"), label_style=text_style("onPage")
        )
        super().__init__(
            title=catalog.text("gui.welcome.title"),
            on_close=lambda: on_done(not self.dont_show.value),
        )
        self.body.controls.append(label("onPage", catalog.text("gui.welcome.intro")))
        for step in steps:
            self.body.controls.extend([gap(SPACE), label("strong", step)])
        self.body.controls.extend([gap(GAP), label("muted", catalog.text("gui.help.language"))])
        start = button("primary", self.close_dialog, catalog.text("gui.welcome.start"))
        self.foot.controls.extend([self.dont_show, stretch(), start])
