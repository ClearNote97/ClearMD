"""The tools (feature 023, ADR-0043): the start screen, the tool chosen there, and Split's
choices on step 1."""

from dataclasses import replace

from clearmd.backend.schemas.settings import CHOICES, RANGES
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.intents.preferences import save
from clearmd.frontend.presenter.intents.reset import editable
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import HOME, WORKING, Tool
from clearmd.i18n import load_catalog


class Tools:
    def __init__(self, session: Session, display: Display, backend: Backend) -> None:
        self._session = session
        self._display = display
        self._backend = backend

    def choose_tool(self, tool: Tool) -> None:
        """Open step 1 of ``tool``. Another tool drops the plan or the result, and the window
        speaks as the tool does (Split's words in place of Convert's)."""
        s = self._session
        if s.state in WORKING:
            return
        if tool is not s.tool:
            editable(s, self._display)
            s.tool = tool
            s.catalog = load_catalog(s.catalog.language).for_tool(tool)
            self._display.view.apply_language(s.catalog)
            self._display.show_inputs()
            self._display.show_output()
        s.page = 1
        self._display.set_state(s.state)

    def go_home(self) -> None:
        """Back to the start screen, outside the work; the inputs and a plan are kept."""
        s = self._session
        if s.state in WORKING:
            return
        s.page = HOME
        self._display.set_state(s.state)

    def choose_split(
        self,
        *,
        cut: str | None = None,
        parts: int | None = None,
        pages: int | None = None,
        keep: str | None = None,
    ) -> None:
        """Split's cut, its sizes and what to keep: remembered (AC-10). A change drops the plan,
        which was made with the earlier cut."""
        s = self._session
        changes: dict[str, object] = {}
        for name, value in (("split_cut", cut), ("split_keep", keep)):
            if value is not None and value in CHOICES[name] and value != getattr(s.settings, name):
                changes[name] = value
        for name, number in (("split_parts", parts), ("split_pages", pages)):
            low, high = RANGES[name]
            if number is not None and low <= number <= high:
                if number != getattr(s.settings, name):
                    changes[name] = number
        if not changes or not editable(s, self._display):
            self._display.show_output()  # the controls show the choice as it is
            return
        save(s, self._display, self._backend, replace(s.settings, **changes))  # type: ignore[arg-type]
        self._display.show_output()
        self._display.set_state(s.state)
