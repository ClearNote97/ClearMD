"""What the window changes in its controls: the controls each state enables (the table from the
presenter's actions to the controls), and the compact rail a narrow window gets. A module of its
own: the table is data about the window, apart from what the view does."""

from collections.abc import Collection

import flet as ft

from clearmd.frontend.design.metrics import COMPACT_BELOW
from clearmd.frontend.flet.components.rail import Rail
from clearmd.frontend.flet.views.choose import ChooseView
from clearmd.frontend.presenter import Action


def apply_enabled(enabled: Collection[Action], main: ChooseView, rail: Rail) -> None:
    controls: tuple[tuple[ft.Control, Action], ...] = (
        (main.add_files, Action.ADD),
        (main.add_folder, Action.ADD),
        (main.start.files.control, Action.ADD),
        (main.start.folder.control, Action.ADD),
        (main.remove, Action.REMOVE),
        (main.clear, Action.REMOVE),
        (main.pick, Action.CHOOSE_OUTPUT),
        (rail.settings, Action.SETTINGS),
        (rail.help, Action.HELP),
    )
    for control, action in controls:
        control.disabled = action not in enabled
    for choice in (*main.choices, main.split, main.merge):
        choice.set_disabled(Action.CHOOSE_OUTPUT not in enabled)


def fit_to_size(rail: Rail, width: float) -> None:
    rail.set_compact(width < COMPACT_BELOW)
