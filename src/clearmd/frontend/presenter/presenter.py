"""The presenter: the state, the intents and every text, once for every GUI (ADR-0026).

The view is passive (``ports.View``). Planning and converting run off the UI thread (``spawn``);
their events come back through ``view.after(0, …)``, so the presenter only changes on the UI
thread. Each piece of work carries a generation: what a cancelled analysis returns later is
dropped.
"""

import time
from collections.abc import Callable, Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter.background import Background
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.intents.analysis import Analysis
from clearmd.frontend.presenter.intents.conversion import Conversion
from clearmd.frontend.presenter.intents.inputs import Inputs
from clearmd.frontend.presenter.intents.preferences import Preferences
from clearmd.frontend.presenter.intents.reset import editable
from clearmd.frontend.presenter.intents.results import Results
from clearmd.frontend.presenter.ports import ApiBackend, Backend, View
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import AppState
from clearmd.frontend.presenter.system_theme import detect_system_theme
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

    @property
    def state(self) -> AppState:
        return self._session.state

    @property
    def page(self) -> int:
        return self._session.page

    @property
    def settings(self) -> Settings:
        return self._session.settings

    @property
    def catalog(self) -> Catalog:
        return self._session.catalog

    @property
    def version(self) -> str:
        """ClearMD's version, as shown in the window and the help."""
        try:
            return version("clearmd")
        except PackageNotFoundError:  # running from sources without metadata
            return "dev"

    @property
    def output_folder(self) -> Path | None:
        """The folder chosen for the results; ``None``: next to the originals."""
        return self._session.output_folder

    def start(self) -> None:
        self._preferences.start()

    def add_paths(self, paths: Sequence[Path]) -> None:
        """Files or folders, from the dialogs or dropped on the window; never listed twice."""
        self._inputs.add_paths(paths)

    def remove_input(self, path: Path) -> None:
        self._inputs.remove_inputs([path])

    def remove_inputs(self, paths: Sequence[Path]) -> None:
        self._inputs.remove_inputs(paths)

    def clear_inputs(self) -> None:
        self._inputs.clear_inputs()

    def choose_output_next_to(self) -> None:
        self._inputs.choose_output_next_to()

    def choose_output_folder(self, folder: Path) -> None:
        self._inputs.choose_output_folder(folder)

    def go_to(self, page: int) -> None:
        """Show a step; only what is on screen changes."""
        if 1 <= page <= 4:
            self._session.page = page
            self._display.set_state(self._session.state)

    def press_primary(self, overwrite: bool | None = None) -> None:
        """The page's primary action: Next, Next, Convert, Open results folder."""
        if not self._display.primary().enabled:
            return
        if self.page == 1:
            if self.state is AppState.WAITING_DECISION:
                self.go_to(2)
            else:
                editable(self._session, self._display)  # after a batch: a new plan (007, N-1)
                self.analyze()
        elif self.page == 2:
            self.go_to(3)
        elif self.page == 3:
            self.confirm(overwrite)
        else:
            self.open_results()

    def convert_more(self, *, keep: bool) -> None:
        self._results.convert_more(keep=keep)

    def analyze(self) -> None:
        self._analysis.analyze()

    def confirm(self, overwrite: bool | None = None) -> None:
        self._conversion.confirm(overwrite)

    def cancel(self) -> None:
        """Stop now: an analysis is dropped; a batch stops its current file at once (ADR-0015)."""
        if self.state is AppState.ANALYZING:
            self._analysis.cancel()
        elif self.state is AppState.CONVERTING:
            self._conversion.cancel()

    def shutdown(self) -> None:
        """The window is closing: a batch may still end (its summary is written), but nothing
        opens afterwards (adversarial review of 005)."""
        self._session.shutting_down = True

    def back(self) -> None:
        """From the plan or the result, to the inputs again (they are kept)."""
        self._results.convert_more(keep=True)

    def open_results(self) -> None:
        self._results.open_results()

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
