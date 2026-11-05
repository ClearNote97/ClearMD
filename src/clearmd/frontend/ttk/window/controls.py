"""What the window changes in its controls: the buttons each state enables (the table from the
presenter's actions to the widgets), and the compact and short layouts a small window gets.
A module of its own: the table is data about the window, apart from what the view does."""

from collections.abc import Collection
from typing import Any

from clearmd.frontend.design.metrics import COMPACT_BELOW, SHORT_BELOW
from clearmd.frontend.presenter import Action
from clearmd.frontend.ttk.components.rail import Rail
from clearmd.frontend.ttk.views.choose import MainView


def apply_enabled(enabled: Collection[Action], main: MainView, rail: Rail) -> None:
    for button, action in (
        (main.add_files, Action.ADD),
        (main.add_folder, Action.ADD),
        (main.remove, Action.REMOVE),
        (main.clear, Action.REMOVE),
        (main.next_to, Action.CHOOSE_OUTPUT),
        (main.in_folder, Action.CHOOSE_OUTPUT),
        (main.pick, Action.CHOOSE_OUTPUT),
        *((button, Action.CHOOSE_OUTPUT) for button in main.summary_buttons),
        (rail.settings, Action.SETTINGS),
        (rail.help, Action.HELP),
    ):
        button.state(["!disabled"] if action in enabled else ["disabled"])


def fit_to_size(root: Any, main: MainView, rail: Rail, event: Any) -> None:
    if event.widget is root:
        rail.set_compact(root.winfo_width() < COMPACT_BELOW)
        main.set_short(root.winfo_height() < SHORT_BELOW)
