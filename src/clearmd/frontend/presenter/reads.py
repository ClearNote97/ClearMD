"""What the windows read from the presenter: the state, the step, the tool, the settings, the
texts, the version and the results' folder. Kept apart so the presenter's class stays its size."""

from pathlib import Path

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import AppState, Tool
from clearmd.frontend.presenter.version import app_version
from clearmd.i18n import Catalog


class Reads:
    _session: Session

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
