"""The help dialog: how to use it, what it converts, where results go, privacy, the language
(UX §4)."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.components.primitives import button, gap, label, stretch
from clearmd.frontend.flet.layout.units import HELP_HEIGHT, HELP_WIDTH
from clearmd.i18n import Catalog

# "how_buttons", not "how": flet cannot receive dropped files, so its help names the buttons only.
_HELP_SECTIONS = ("how_buttons", "formats", "where", "keyboard", "privacy", "language")


class HelpDialog(Dialog):
    """How to use it, what it converts, where results go, privacy, the language; the version."""

    def __init__(
        self, catalog: Catalog, on_close: Callable[[], None], *, version: str = ""
    ) -> None:
        super().__init__(title=catalog.text("gui.help.title"), on_close=on_close, width=HELP_WIDTH)
        sections: list[ft.Control] = []
        for index, section in enumerate(_HELP_SECTIONS):
            if index:
                sections.append(gap(GAP - HALF))
            sections.append(label("strong", catalog.text(f"gui.help.{_title(section)}_title")))
            sections.append(label("onPage", catalog.text(f"gui.help.{section}")))
        scroll = ft.Column(sections, spacing=HALF, scroll=ft.ScrollMode.AUTO)
        self.body.controls.append(
            ft.Container(content=scroll, height=HELP_HEIGHT, padding=ft.Padding.only(right=SPACE))
        )
        self.texts_shown = [catalog.text(f"gui.help.{section}") for section in _HELP_SECTIONS]
        if version:
            self.foot.controls.append(
                label("hint", catalog.text("gui.help.version", version=version))
            )
        self.foot.controls.append(stretch())
        close = button("primary", self.close_dialog, catalog.text("gui.help.close"))
        self.foot.controls.append(close)


def _title(section: str) -> str:
    """The buttons-only way of use keeps the same heading as the shared one."""
    return "how" if section == "how_buttons" else section
