"""The system's pickers behind Add files, Add folder and the output folder."""

from pathlib import Path

from clearmd.backend.schemas.formats import EXTENSIONS
from clearmd.frontend.flet.components.primitives import Choice
from clearmd.frontend.flet.window.page_port import PagePort
from clearmd.frontend.flet.window.shown import Shown
from clearmd.frontend.presenter import Action, OutputMode, Presenter


class Pickers:
    """The pickers answer later, on the page's loop: each answer is handed to the presenter."""

    def __init__(self, page: PagePort, presenter: Presenter, shown: Shown, mode: Choice) -> None:
        self._page = page
        self._presenter = presenter
        self._shown = shown
        self._mode = mode

    def add_files(self) -> None:
        if not self._shown.allows(Action.ADD):
            return
        extensions = sorted(extension.lstrip(".") for extension in EXTENSIONS)
        title = self._shown.need_catalog().text("gui.main.pick_files_title")
        self._page.pick_files(title, extensions, self._files_chosen)

    def add_folder(self) -> None:
        if not self._shown.allows(Action.ADD):
            return
        title = self._shown.need_catalog().text("gui.main.pick_folder_title")
        self._page.pick_folder(title, None, self._folder_chosen)

    def pick_output_folder(self) -> None:
        if not self._shown.allows(Action.CHOOSE_OUTPUT):
            return
        suggestion = self._presenter.settings.last_output_folder or None
        title = self._shown.need_catalog().text("gui.main.pick_output_title")
        self._page.pick_folder(title, suggestion, self._output_chosen)

    def _files_chosen(self, chosen: list[str]) -> None:
        if chosen:
            self._presenter.add_paths([Path(path) for path in chosen])

    def _folder_chosen(self, chosen: str | None) -> None:
        if chosen:
            self._presenter.add_paths([Path(chosen)])

    def _output_chosen(self, chosen: str | None) -> None:
        if chosen:
            self._presenter.choose_output_folder(Path(chosen))
        else:  # cancelled: the radio buttons show the choice as it was
            current = self._presenter.output_folder
            self._mode.set((OutputMode.FOLDER if current is not None else OutputMode.NEXT_TO).value)
