"""The inputs and the output: add, remove, clear, choose where the results go."""

import os
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from clearmd.backend.schemas.settings import valid_path_setting
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.intents.preferences import save
from clearmd.frontend.presenter.intents.reset import editable
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.presenter.screens.choose import key
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import HOME


class Inputs:
    def __init__(self, session: Session, display: Display, backend: Backend) -> None:
        self._session = session
        self._display = display
        self._backend = backend

    def add_paths(self, paths: Sequence[Path]) -> None:
        s = self._session
        known = {key(path) for path in s.inputs}
        new: list[Path] = []
        for path in paths:
            absolute = Path(os.path.abspath(path))
            if key(absolute) not in known:
                known.add(key(absolute))
                new.append(absolute)
        if not new or not editable(s, self._display):  # nothing new: the plan stays (C7-4)
            return
        s.inputs.extend(new)
        if s.page == HOME:  # dropped on the start screen: they go to step 1 (feature 023)
            s.page = 1
        self._display.show_inputs()
        self._display.set_state(s.state)

    def remove_inputs(self, paths: Sequence[Path]) -> None:
        """Remove several at once: one redraw, whatever their number (code review of 007)."""
        s = self._session
        gone = {key(Path(path)) for path in paths}
        kept = [known for known in s.inputs if key(known) not in gone]
        if len(kept) == len(s.inputs) or not editable(s, self._display):
            return
        s.inputs = kept
        self._display.show_inputs()
        self._display.set_state(s.state)

    def move_input(self, path: Path, offset: int) -> None:
        """Merge's order (feature 032): one place up (-1) or down (+1); a plan made with the
        earlier order is dropped."""
        s = self._session
        where = [key(known) for known in s.inputs]
        if key(Path(path)) not in where:
            return
        index = where.index(key(Path(path)))
        other = index + offset
        if offset not in (-1, 1) or not 0 <= other < len(s.inputs):
            return
        if not editable(s, self._display):
            return
        s.inputs[index], s.inputs[other] = s.inputs[other], s.inputs[index]
        self._display.show_inputs()
        self._display.set_state(s.state)

    def clear_inputs(self) -> None:
        s = self._session
        if not s.inputs or not editable(s, self._display):
            return
        s.inputs.clear()
        self._display.show_inputs()
        self._display.set_state(s.state)

    def choose_output_next_to(self) -> None:
        s = self._session
        if s.output_folder is None or not editable(s, self._display):
            return
        s.output_folder = None
        self._display.show_output()
        self._display.set_state(s.state)

    def choose_output_folder(self, folder: Path) -> None:
        """Results in ``folder``, remembered as the suggestion for next time (ADR-0016) when its
        path can be stored (a name with control characters still receives the results)."""
        s = self._session
        chosen = Path(os.path.abspath(folder))
        if chosen == s.output_folder or not editable(s, self._display):
            return
        s.output_folder = chosen
        self._display.show_output()
        self._display.set_state(s.state)
        if valid_path_setting(str(s.output_folder)):
            save(
                s,
                self._display,
                self._backend,
                replace(s.settings, last_output_folder=str(s.output_folder)),
            )
