"""The welcome dialog: the three steps, "Don't show again", and the language at once (UX §4;
AC-14; audit v3 F4-05: "English" and "Español", each in its own language, redraw it while open)."""

from collections.abc import Callable
from functools import partial

import flet as ft

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.components.primitives import button, gap, label, stretch
from clearmd.frontend.flet.visuals.look import text_style
from clearmd.i18n import Catalog

LANGUAGES = ("en", "es")


class WelcomeDialog(Dialog):
    """The three steps, "Don't show again", the two language buttons (``on_language``)."""

    def __init__(
        self,
        catalog: Catalog,
        steps: tuple[str, ...],
        on_done: Callable[[bool], None],
        on_language: Callable[[str], None] = lambda language: None,
    ) -> None:
        self.dont_show = ft.Checkbox(label_style=text_style("onPage"))
        super().__init__(title="", on_close=lambda: on_done(not self.dont_show.value))
        self.languages = {
            language: button("", partial(on_language, language)) for language in LANGUAGES
        }
        self.start = button("primary", self.close_dialog)
        self.foot.controls.extend([self.dont_show, stretch(), *self.languages.values(), self.start])
        self._show(catalog, steps)

    def apply_language(self, catalog: Catalog) -> None:
        """The language changed while the Welcome is open: every text again, in it."""
        self._show(catalog, tuple(catalog.text(f"gui.welcome.step{n}") for n in (1, 2, 3)))

    def _show(self, catalog: Catalog, steps: tuple[str, ...]) -> None:
        self.title.value = catalog.text("gui.welcome.title")
        self.dont_show.label = catalog.text("gui.welcome.dont_show")
        for language, chosen in self.languages.items():  # each in its own language, always
            chosen.content = catalog.text(f"gui.welcome.language_{language}")
        self.start.content = catalog.text("gui.welcome.start")
        controls: list[ft.Control] = [label("onPage", catalog.text("gui.welcome.intro"))]
        for step in steps:
            controls.extend([gap(SPACE), label("strong", step)])
        controls.extend([gap(GAP), label("muted", catalog.text("gui.help.language"))])
        self.body.controls = controls
