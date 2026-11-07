"""The dark rail (ADR-0027, ADR-0029): the logo, Home (feature 023), the steps, Settings, Help, the
promise and the version."""

from collections.abc import Callable
from functools import partial

import flet as ft

from clearmd.frontend.design.metrics import COMPACT_RAIL_WIDTH, GAP, HALF, RADIUS, RAIL_WIDTH, SPACE
from clearmd.frontend.flet.components.primitives import gap, label
from clearmd.frontend.flet.components.rail_art import badge, paint_badge, rail_style
from clearmd.frontend.flet.components.rail_home import RailHome
from clearmd.frontend.flet.layout.units import STEP_HEIGHT
from clearmd.frontend.flet.visuals.images import logo_src
from clearmd.frontend.flet.visuals.look import paint
from clearmd.frontend.flet.visuals.theme import role
from clearmd.frontend.presenter.state import HOME, STEPS
from clearmd.i18n import Catalog

COMPACT_VERSION_CHARS = 6  # what fits the compact rail at 14 px
LOGO = 40  # the mark's size on the rail


class Rail:
    """The dark rail: the logo, Clear·MD, Home and the four steps — each one can be opened, the one
    on screen highlighted — Settings, Help, the promise and the version. Below 1000 px of window
    width it is compact: the mark and the numbers only."""

    def __init__(
        self,
        *,
        on_step: Callable[[int], None],
        on_home: Callable[[], None],
        on_settings: Callable[[], None],
        on_help: Callable[[], None],
    ) -> None:
        self._compact = False
        self._page = HOME
        self._labels = [""] * len(STEPS)
        self._words = {"settings": "", "help": "", "home": ""}
        self._version = ""
        self._local = ""
        self.mark = ft.Image(src=logo_src("clearmd-mark-dark-40"), width=LOGO, height=LOGO)
        self.wordmark = label("wordmark")
        self.wordmark.spans = [
            ft.TextSpan("Clear"),
            ft.TextSpan("·", style=ft.TextStyle(color=role("clear"))),  # the "Clear" tone
            ft.TextSpan("MD"),
        ]
        top = ft.Container(
            content=ft.Row([self.mark, self.wordmark], spacing=SPACE),
            padding=ft.Padding.only(left=SPACE),
        )
        self._home = RailHome(on_home)
        self.home = self._home.button
        self.steps: list[ft.Button] = []
        self._badges: list[tuple[ft.Container, ft.Text]] = []
        self._names: list[ft.Text] = []
        for index in range(1, len(STEPS) + 1):
            circle, digit = badge(index)
            name = label("rail")
            step = ft.Button(
                content=ft.Row([circle, name], spacing=SPACE),
                height=STEP_HEIGHT,
                on_click=partial(on_step, index),
            )
            self.steps.append(step)
            self._badges.append((circle, digit))
            self._names.append(name)
        self._settings_text, self._help_text = label("railButton"), label("railButton")
        self.settings = ft.Button(
            content=self._settings_text, height=STEP_HEIGHT, on_click=on_settings
        )
        self.help = ft.Button(content=self._help_text, height=STEP_HEIGHT, on_click=on_help)
        self.foot = label("local")
        foot = ft.Container(
            content=self.foot, padding=ft.Padding.only(left=SPACE, top=SPACE, right=SPACE)
        )
        self._foot_frame = foot
        self.control = ft.Container(
            content=ft.Column(
                [top, gap(4 * SPACE), self.home, *self.steps, ft.Container(expand=True),
                 self.settings, self.help, foot],
                spacing=HALF,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            width=RAIL_WIDTH,
            bgcolor=role("rail"),
            border_radius=ft.BorderRadius.all(2 * RADIUS),
            padding=ft.Padding.only(left=SPACE, top=3 * SPACE, right=SPACE, bottom=GAP),
        )  # fmt: skip
        self._draw()

    def apply_language(self, catalog: Catalog) -> None:
        self._labels = [catalog.text(f"gui.steps.{name}") for name in STEPS]
        self._words = {
            "settings": catalog.text("gui.main.settings"),
            "help": catalog.text("gui.main.help_word"),
            "home": catalog.text("gui.home.step"),
        }
        self._local = catalog.text("gui.app.local")
        self._draw()

    def show_page(self, page: int) -> None:
        if page != self._page:
            self._page = page
            self._draw()

    def show_version(self, version: str) -> None:
        self._version = f"v{version}" if version[:1].isdigit() else version
        self._draw()

    def set_compact(self, compact: bool) -> None:
        if compact != self._compact:
            self._compact = compact
            self.control.width = COMPACT_RAIL_WIDTH if compact else RAIL_WIDTH
            self.wordmark.visible = not compact
            side = 0 if compact else SPACE  # the compact rail's 56 px hold the version whole
            self._foot_frame.padding = ft.Padding.only(left=side, top=SPACE, right=side)
            self.foot.text_align = ft.TextAlign.CENTER if compact else ft.TextAlign.LEFT
            self._draw()

    @property
    def compact(self) -> bool:
        return self._compact

    def step_texts(self) -> list[str]:
        """The steps as shown, the one on screen marked with ``>`` (for tests)."""
        return [
            ("> " if index + 1 == self._page else "") + text
            for index, text in enumerate(self._labels)
        ]

    def home_text(self) -> str:
        """Home as shown, marked with ``>`` while on screen (for tests)."""
        return ("> " if self._page == HOME else "") + self._words["home"]

    def _draw(self) -> None:
        self._home.draw(self._words["home"], current=self._page == HOME, compact=self._compact)
        for index, step in enumerate(self.steps, start=1):
            current = index == self._page
            text = self._labels[index - 1]
            name = self._names[index - 1]
            name.value = text
            name.visible = not self._compact
            paint(name, "railCurrent" if current else "rail")
            paint_badge(*self._badges[index - 1], current=current)
            step.tooltip = text
            step.style = rail_style(current=current, compact=self._compact)
        for widget, shown, word, short in (
            (self.settings, self._settings_text, "settings", "⚙"),
            (self.help, self._help_text, "help", "?"),
        ):
            shown.value = short if self._compact else self._words[word]
            widget.tooltip = self._words[word]
            widget.style = rail_style(compact=self._compact, inset=5 * SPACE)
        self.foot.value = (
            self._compact_version()
            if self._compact
            else "\n".join(filter(None, (self._local, self._version)))
        )

    def _compact_version(self) -> str:
        """The version in the narrow rail: without its "v" when it would not fit (0.10.1)."""
        return self._version if len(self._version) <= COMPACT_VERSION_CHARS else self._version[1:]
