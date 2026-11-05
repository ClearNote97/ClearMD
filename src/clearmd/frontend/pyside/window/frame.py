"""The arrangement of the window: the rail on the left; on the right the surface with a panel that
holds the four step views, the message and the action bar. A module of its own: it builds the
widgets and nothing else, the window wires them."""

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.presenter import Presenter
from clearmd.frontend.pyside.components.action_bar import ActionBar
from clearmd.frontend.pyside.components.primitives import label
from clearmd.frontend.pyside.components.rail import Rail
from clearmd.frontend.pyside.components.surface import Surface
from clearmd.frontend.pyside.views.choose import ChooseView
from clearmd.frontend.pyside.views.convert import ConvertView
from clearmd.frontend.pyside.views.results import ResultsView
from clearmd.frontend.pyside.views.review import ReviewView
from clearmd.frontend.pyside.window.dialog_host import DialogHost


@dataclass(frozen=True)
class Frame:
    rail: Rail
    surface: Surface
    stack: QStackedWidget
    actions: ActionBar
    message: QLabel
    main: ChooseView
    review: ReviewView
    converting: ConvertView
    results: ResultsView


def build_frame(
    window: QWidget,
    presenter: Presenter,
    dialogs: DialogHost,
    *,
    on_primary: Callable[[], None],
    on_add_files: Callable[[], None],
    on_add_folder: Callable[[], None],
    on_pick_folder: Callable[[], None],
) -> Frame:
    outer = QHBoxLayout(window)
    outer.setContentsMargins(GAP, GAP, 0, GAP)
    outer.setSpacing(0)
    rail = Rail(
        on_step=lambda page: presenter.go_to(page),
        on_settings=dialogs.show_settings,
        on_help=dialogs.show_help,
    )
    outer.addWidget(rail)
    surface = Surface()
    outer.addWidget(surface, 1)

    panel = QFrame()
    panel.setObjectName("panel")
    surface.body.addWidget(panel, 1)
    inside = QVBoxLayout(panel)
    inside.setContentsMargins(GAP, GAP, GAP, GAP)
    inside.setSpacing(SPACE)
    stack = QStackedWidget()
    inside.addWidget(stack, 1)
    message = label("message", wrap=True)
    inside.addWidget(message)
    actions = ActionBar(on_primary=on_primary)
    inside.addWidget(actions)

    main = ChooseView(
        on_add_files=on_add_files,
        on_add_folder=on_add_folder,
        on_remove=lambda paths: presenter.remove_inputs(paths),
        on_clear=lambda: presenter.clear_inputs(),
        on_next_to=lambda: presenter.choose_output_next_to(),
        on_pick_folder=on_pick_folder,
        on_summary=lambda value: presenter.choose_summary_format(value),
        on_images=lambda value: presenter.choose_images(value),
    )
    review = ReviewView()
    converting = ConvertView()
    results = ResultsView()
    for page in (main, review, converting, results):
        stack.addWidget(page)
    return Frame(rail, surface, stack, actions, message, main, review, converting, results)
