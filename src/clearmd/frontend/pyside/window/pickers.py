"""The native pickers behind Add files, Add folder and the output folder."""

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QRadioButton, QWidget

from clearmd.backend.schemas.formats import EXTENSIONS
from clearmd.frontend.presenter import Action, Presenter
from clearmd.frontend.pyside.window.shown import Shown


class Pickers:
    def __init__(
        self,
        parent: QWidget,
        presenter: Presenter,
        shown: Shown,
        next_to: QRadioButton,
        in_folder: QRadioButton,
    ) -> None:
        self._parent = parent
        self._presenter = presenter
        self._shown = shown
        self._next_to = next_to
        self._in_folder = in_folder

    def add_files(self) -> None:
        if not self._shown.allows(Action.ADD):
            return
        catalog = self._shown.need_catalog()
        patterns = " ".join(f"*{extension}" for extension in sorted(EXTENSIONS))
        chosen, _filter = QFileDialog.getOpenFileNames(
            self._parent,
            catalog.text("gui.main.pick_files_title"),
            "",
            f"{catalog.text('gui.main.documents')} ({patterns});;* (*)",
        )
        if chosen:
            self._presenter.add_paths([Path(path) for path in chosen])

    def add_folder(self) -> None:
        if not self._shown.allows(Action.ADD):
            return
        chosen = QFileDialog.getExistingDirectory(
            self._parent, self._shown.need_catalog().text("gui.main.pick_folder_title")
        )
        if chosen:
            self._presenter.add_paths([Path(chosen)])

    def pick_output_folder(self) -> None:
        if not self._shown.allows(Action.CHOOSE_OUTPUT):
            return
        suggestion = self._presenter.settings.last_output_folder or ""
        chosen = QFileDialog.getExistingDirectory(
            self._parent, self._shown.need_catalog().text("gui.main.pick_output_title"), suggestion
        )
        if chosen:
            self._presenter.choose_output_folder(Path(chosen))
        else:  # cancelled: the radio buttons show the choice as it was
            current = self._presenter.output_folder
            (self._in_folder if current is not None else self._next_to).setChecked(True)
