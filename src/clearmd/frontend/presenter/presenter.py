"""The presenter: the state, the intents and every text, once for every GUI (ADR-0026).

The view is passive (``ports.View``). Planning and converting run off the UI thread (``spawn``);
their events come back through ``view.after(0, …)``, so the presenter only changes on the UI
thread. Each piece of work carries a generation: what a cancelled analysis returns later is
dropped.
"""

import time
from collections.abc import Callable, Sequence
from pathlib import Path

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter.background import Background
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.intents.analysis import Analysis
from clearmd.frontend.presenter.intents.conversion import Conversion
from clearmd.frontend.presenter.intents.inputs import Inputs
from clearmd.frontend.presenter.intents.navigation import Navigation
from clearmd.frontend.presenter.intents.preferences import Preferences
from clearmd.frontend.presenter.intents.reset import copy_details
from clearmd.frontend.presenter.intents.results import Results
from clearmd.frontend.presenter.intents.tools import Tools
from clearmd.frontend.presenter.models import NextChoice
from clearmd.frontend.presenter.ports import ApiBackend, Backend, View
from clearmd.frontend.presenter.screens.next import next_choices
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import AppState, Tool
from clearmd.frontend.presenter.system_theme import detect_system_theme
from clearmd.frontend.presenter.version import app_version
from clearmd.i18n import Catalog


class Presenter:
    def __init__(
        self,
        view: View,
        backend: Backend | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
        detect_theme: Callable[[], str] | None = None,
        spawn: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self._backend = backend or ApiBackend()
        self._session = session = Session()
        self._display = display = Display(view, session, clock)
        background = Background(view, session, spawn)
        self._inputs = Inputs(session, display, self._backend)
        self._analysis = Analysis(session, display, self._backend, background)
        self._results = Results(session, display, self._backend)
        self._conversion = Conversion(
            session, display, self._backend, background, clock, self._results.open_results
        )
        self._preferences = Preferences(
            session, display, self._backend, detect_theme or detect_system_theme
        )
        self._tools = Tools(session, display, self._backend)
        self._navigation = Navigation(
            session, display, self._tools, self._analysis, self._conversion, self._results
        )

    @property
    def state(self) -> AppState:
        return self._session.state

    @property
    def page(self) -> int:
        return self._session.page

    @property
    def tool(self) -> Tool:
        return self._session.tool

    @property
    def settings(self) -> Settings:
        return self._session.settings

    @property
    def catalog(self) -> Catalog:
        return self._session.catalog

    @property
    def version(self) -> str:  # as shown in the window and the help
        return app_version()

    @property
    def output_folder(self) -> Path | None:  # the results' folder; None: next to the originals
        return self._session.output_folder

    def start(self) -> None:
        self._preferences.start()

    def add_paths(self, paths: Sequence[Path]) -> None:  # from dialogs or dropped; never twice
        self._inputs.add_paths(paths)

    def remove_input(self, path: Path) -> None:
        self._inputs.remove_inputs([path])

    def remove_inputs(self, paths: Sequence[Path]) -> None:
        self._inputs.remove_inputs(paths)

    def clear_inputs(self) -> None:
        self._inputs.clear_inputs()

    def move_input(self, path: Path, offset: int) -> None:  # Merge's order (feature 032)
        self._inputs.move_input(path, offset)

    def choose_output_next_to(self) -> None:
        self._inputs.choose_output_next_to()

    def choose_output_folder(self, folder: Path) -> None:
        self._inputs.choose_output_folder(folder)

    def choose_tool(self, tool: Tool) -> None:  # a tile of the start screen (feature 023)
        self._tools.choose_tool(tool)

    def split_large(self) -> None:  # Review's and Results' offer (feature 025)
        self._tools.split_large()

    def choose_split(
        self,
        *,
        cut: str | None = None,
        parts: int | None = None,
        pages: int | None = None,
        keep: str | None = None,
        words: int | None = None,
        into: str | None = None,
    ) -> None:
        self._tools.choose_split(
            cut=cut, parts=parts, pages=pages, keep=keep, words=words, into=into
        )

    def go_to(self, page: int) -> None:  # a step, or 0: Home; only what is on screen changes
        self._navigation.go_to(page)

    def press_primary(self, overwrite: bool | str | None = None) -> None:  # Next, Convert, Open
        self._navigation.press_primary(overwrite)

    def next_choices(self) -> tuple[NextChoice, ...]:  # Results' "What Next?" (feature 033)
        return next_choices(self._session.catalog, self._session.tool)

    def continue_with(self, tool: Tool, *, keep: bool) -> None:
        self._navigation.continue_with(tool, keep=keep)

    def analyze(self) -> None:
        self._analysis.analyze()

    def confirm(self, overwrite: bool | str | None = None) -> None:
        self._conversion.confirm(overwrite)

    def cancel(self) -> None:  # an analysis is dropped; a batch stops its file at once (0015)
        if self.state is AppState.ANALYZING:
            self._analysis.cancel()
        elif self.state is AppState.CONVERTING:
            self._conversion.cancel()

    def shutdown(self) -> None:  # a batch may still end, but nothing opens afterwards (005)
        self._session.shutting_down = True

    def back(self) -> None:  # from the plan or the result, to the inputs again (kept)
        self._results.convert_more(keep=True)

    def open_results(self) -> None:
        self._results.open_results()

    def copy_details(self) -> None:  # "Copy Details" after an unexpected error (D3)
        copy_details(self._session, self._display)

    def save_settings(self, settings: Settings) -> None:
        self._preferences.save_settings(settings)

    def choose_summary_format(self, summary_format: str) -> None:
        self._preferences.choose_summary_format(summary_format)

    def choose_images(self, images: str) -> None:
        self._preferences.choose_images(images)

    def restore_defaults(self) -> None:
        self._preferences.restore_defaults()

    def dismiss_welcome(self, *, show_again: bool) -> None:
        self._preferences.dismiss_welcome(show_again=show_again)
