"""The native pickers behind Add files, Add folder and the output folder."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Any

from clearmd.backend.schemas.formats import EXTENSIONS
from clearmd.frontend.presenter import Action, Presenter
from clearmd.frontend.ttk.window.shown import Shown


class Pickers:
    def __init__(
        self, root: Any, presenter: Presenter, shown: Shown, output_mode: tk.StringVar
    ) -> None:
        self._root = root
        self._presenter = presenter
        self._shown = shown
        self._output_mode = output_mode

    def add_files(self) -> None:
        state = self._shown.state
        if state is not None and Action.ADD not in state.enabled:
            return
        catalog = self._shown.need_catalog()
        patterns = " ".join(f"*{extension}" for extension in sorted(EXTENSIONS))
        chosen = filedialog.askopenfilenames(
            parent=self._root,
            title=catalog.text("gui.main.pick_files_title"),
            filetypes=[(catalog.text("gui.main.documents"), patterns), ("*", "*")],
        )
        if chosen:
            self._presenter.add_paths([Path(path) for path in chosen])

    def add_folder(self) -> None:
        state = self._shown.state
        if state is not None and Action.ADD not in state.enabled:
            return
        chosen = filedialog.askdirectory(
            parent=self._root, title=self._shown.need_catalog().text("gui.main.pick_folder_title")
        )
        if chosen:
            self._presenter.add_paths([Path(chosen)])

    def pick_output_folder(self) -> None:
        state = self._shown.state
        if state is not None and Action.CHOOSE_OUTPUT not in state.enabled:
            return
        suggestion = self._presenter.settings.last_output_folder or None
        chosen = filedialog.askdirectory(
            parent=self._root,
            title=self._shown.need_catalog().text("gui.main.pick_output_title"),
            initialdir=suggestion,
        )
        if chosen:
            self._presenter.choose_output_folder(Path(chosen))
        else:  # cancelled: the radio buttons show the choice as it was
            current = self._presenter.output_folder
            self._output_mode.set("folder" if current is not None else "next_to")
