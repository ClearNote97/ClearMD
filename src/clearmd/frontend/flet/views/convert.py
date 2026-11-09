"""Step 3, Convert: what is ready before the batch, then the progress (AC-09)."""

import flet as ft

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.flet.components.primitives import Wording, card, gap, label
from clearmd.frontend.flet.layout.units import ICON, PROGRESS_HEIGHT
from clearmd.frontend.flet.visuals.images import icon_src
from clearmd.frontend.flet.visuals.look import paint
from clearmd.frontend.flet.visuals.theme import role
from clearmd.frontend.presenter.models import ProgressView
from clearmd.i18n import Catalog


class ConvertView:
    """Before the batch, a card says what is ready and where it goes; then "3 of 37", the
    current file with its icon, the bar, the time left, and for a long file its timer."""

    def __init__(self) -> None:
        self._wording = Wording()
        self._catalog: Catalog | None = None
        self.ready_count = label("bigText")
        # What happens to the results that already exist, when some do (feature 035, AC-08).
        self.ready_existing = label("onPage")
        self.ready_existing.visible = False
        self.ready_where = label("muted")
        self.ready = card(
            [self.ready_count, self.ready_existing, self.ready_where], padding=3 * SPACE
        )
        self.counter = label("bigText")
        now = label("muted")
        self._wording.add(now, "gui.progress.current")
        self.file_icon = ft.Image(src=icon_src("unknown"), width=ICON, height=ICON, visible=False)
        self.file = label("strong", expand=True)
        current = ft.Row([self.file_icon, self.file], spacing=SPACE)
        self.bar = ft.ProgressBar(
            value=0.0,
            bar_height=PROGRESS_HEIGHT,
            color=role("accent"),
            bgcolor=role("border"),
            border_radius=ft.BorderRadius.all(SPACE // 2),
        )
        self.time_left = label("muted")
        self.long_file = label("muted")
        self.progress_card = card(
            [self.counter, gap(SPACE), now, current, gap(SPACE), self.bar, self.time_left,
             self.long_file],
            padding=3 * SPACE,
        )  # fmt: skip
        self.progress_card.visible = False
        # Stretched: the cards span the page's width, as in Qt (flet's column hugs by default).
        self.control = ft.Column(
            [self.ready, self.progress_card],
            spacing=GAP,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self.dimmed = False
        self._fade(True)

    def show_ready(self, count: str, where: str) -> None:
        """``count``: the presenter's ready line; a second line says what happens to the results
        that already exist."""
        self.progress_card.visible = False
        self._fade(False)
        first, _, rest = count.partition("\n")
        self.ready_count.value = first
        self.ready_existing.value = rest
        self.ready_existing.visible = bool(rest)
        self.ready_where.value = where
        self.ready.visible = True

    def forget(self, where: str = "") -> None:
        self.progress_card.visible = False
        self._fade(True)
        catalog = self._catalog
        self.ready_count.value = catalog.text("gui.convert.ready", count="—") if catalog else "—"
        self.ready_existing.value, self.ready_existing.visible = "", False
        self.ready_where.value = where
        self.ready.visible = True

    def clear(self) -> None:
        """The batch starts: the progress replaces the ready card."""
        self.ready.visible = False
        self.progress_card.visible = True
        for text in (self.counter, self.file, self.time_left, self.long_file):
            text.value = ""
        self.file_icon.visible = False
        self.bar.value = 0.0

    def show(self, progress: ProgressView) -> None:
        self.counter.value = progress.counter
        self.file_icon.src = icon_src(progress.icon)
        self.file_icon.visible = True
        self.file.value = progress.name
        self.bar.value = progress.fraction
        self.time_left.value = progress.time_left or ""
        if progress.elapsed and self._catalog is not None:
            elapsed = self._catalog.text("gui.progress.elapsed", clock=progress.elapsed)
            self.long_file.value = f"{elapsed} · {progress.long_file or ''}".strip(" ·")
        else:
            self.long_file.value = ""

    def _fade(self, dimmed: bool) -> None:
        """A faded card waits for a plan (feature 014)."""
        self.dimmed = dimmed
        self.ready.bgcolor = role("dim_card" if dimmed else "card")
        self.ready.border = ft.Border.all(1, role("dim_card" if dimmed else "border"))
        for text, kind in ((self.ready_count, "bigText"), (self.ready_where, "muted")):
            paint(text, kind)
            if dimmed:
                text.color = role("dim_text")

    def apply_language(self, catalog: Catalog) -> None:
        self._wording.apply(catalog)
        self._catalog = catalog
        if self.dimmed:
            self.ready_count.value = catalog.text("gui.convert.ready", count="—")
