"""The help dialog (UX §4): the presenter's sections, the same in the three windows (feature 035,
AC-04): what Markdown is, the real flow, the tools, what is converted, where results go, the
keys, privacy, the language. flet cannot receive dropped files, so dropping is never told."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.components.primitives import button, gap, label, stretch
from clearmd.frontend.flet.layout.units import HELP_HEIGHT, HELP_WIDTH
from clearmd.frontend.presenter.screens.help import help_sections
from clearmd.i18n import Catalog

DROPS = False  # flet 1.0 cannot receive files dropped from the system (feature 018)


class HelpDialog(Dialog):
    """``help_sections`` in order, each title strong and its text wrapped; the version."""

    def __init__(
        self, catalog: Catalog, on_close: Callable[[], None], *, version: str = ""
    ) -> None:
        super().__init__(title=catalog.text("gui.help.title"), on_close=on_close, width=HELP_WIDTH)
        self.sections = help_sections(catalog, drops=DROPS)
        sections: list[ft.Control] = []
        for index, (title, text) in enumerate(self.sections):
            if index:
                sections.append(gap(GAP - HALF))
            sections.append(label("strong", title))
            sections.append(label("onPage", text))
        scroll = ft.Column(sections, spacing=HALF, scroll=ft.ScrollMode.AUTO)
        self.body.controls.append(
            ft.Container(content=scroll, height=HELP_HEIGHT, padding=ft.Padding.only(right=SPACE))
        )
        self.texts_shown = [text for _title, text in self.sections]
        if version:
            self.foot.controls.append(
                label("hint", catalog.text("gui.help.version", version=version))
            )
        self.foot.controls.append(stretch())
        close = button("primary", self.close_dialog, catalog.text("gui.help.close"))
        self.foot.controls.append(close)
