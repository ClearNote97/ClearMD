"""What the window changes in its controls: the widgets each state enables (the table from the
presenter's actions to the widgets), and the compact and short layouts a small window gets.
A module of its own: the table is data about the window, apart from what the view does."""

from collections.abc import Collection

from clearmd.frontend.design.metrics import COMPACT_BELOW, SHORT_BELOW
from clearmd.frontend.presenter import Action
from clearmd.frontend.pyside.components.rail import Rail
from clearmd.frontend.pyside.views.choose import ChooseView


def apply_enabled(
    enabled: Collection[Action], main: ChooseView, rail: Rail, *, working: bool
) -> None:
    rail.home.setEnabled(not working)  # the start screen, outside the work (feature 023)
    for widget, action in (
        (main.add_files, Action.ADD),
        (main.add_folder, Action.ADD),
        (main.drop_zone, Action.ADD),
        (main.remove, Action.REMOVE),
        (main.clear, Action.REMOVE),
        *((choice, Action.CHOOSE_OUTPUT) for choice in main.choice_buttons),
        (rail.settings, Action.SETTINGS),
        (rail.help, Action.HELP),
    ):
        widget.setEnabled(action in enabled)


def fit_to_size(main: ChooseView, rail: Rail, width: int, height: int) -> None:
    rail.set_compact(width < COMPACT_BELOW)
    main.set_short(height < SHORT_BELOW)
