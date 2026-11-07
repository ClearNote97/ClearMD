"""The arrangement of the window: the rail on the left; on the right the surface with a panel that
holds Home (feature 023) and the four step views, the message and the action bar. A module of its
own: it builds the controls and nothing else, the window wires them."""

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from clearmd.frontend.design.metrics import GAP, RADIUS, SPACE
from clearmd.frontend.flet.components.action_bar import ActionBar
from clearmd.frontend.flet.components.primitives import label
from clearmd.frontend.flet.components.rail import Rail
from clearmd.frontend.flet.components.surface import Surface
from clearmd.frontend.flet.views.choose import ChooseView
from clearmd.frontend.flet.views.convert import ConvertView
from clearmd.frontend.flet.views.home import HomeView
from clearmd.frontend.flet.views.results import ResultsView
from clearmd.frontend.flet.views.review import ReviewView
from clearmd.frontend.flet.visuals.theme import role
from clearmd.frontend.flet.window.dialog_host import DialogHost
from clearmd.frontend.presenter import Presenter
from clearmd.frontend.presenter.state import HOME


@dataclass(frozen=True)
class Frame:
    root: ft.Container
    rail: Rail
    surface: Surface
    panel: ft.Container
    pages: tuple[ft.Control, ...]  # the four steps' columns, one visible at a time
    home: HomeView  # the start screen, the page before them (feature 023)
    actions: ActionBar
    message: ft.Text
    main: ChooseView
    review: ReviewView
    converting: ConvertView
    results: ResultsView


def build_frame(
    presenter: Presenter,
    dialogs: DialogHost,
    *,
    on_primary: Callable[[], None],
    on_add_files: Callable[[], None],
    on_add_folder: Callable[[], None],
    on_pick_folder: Callable[[], None],
) -> Frame:
    rail = Rail(
        on_step=lambda page: presenter.go_to(page),
        on_home=lambda: presenter.go_to(HOME),
        on_settings=dialogs.show_settings,
        on_help=dialogs.show_help,
    )
    main = ChooseView(
        on_add_files=on_add_files,
        on_add_folder=on_add_folder,
        on_remove=lambda paths: presenter.remove_inputs(paths),
        on_clear=lambda: presenter.clear_inputs(),
        on_next_to=lambda: presenter.choose_output_next_to(),
        on_pick_folder=on_pick_folder,
        on_summary=lambda value: presenter.choose_summary_format(value),
        on_images=lambda value: presenter.choose_images(value),
        on_split=lambda **choice: presenter.choose_split(**choice),
    )
    home = HomeView(on_tool=lambda tool: presenter.choose_tool(tool))
    home.control.visible = False
    review, converting, results = ReviewView(), ConvertView(), ResultsView()
    pages = tuple(view.control for view in (main, review, converting, results))
    message = label("message")
    message.visible = False  # until there is one
    actions = ActionBar(on_primary=on_primary, on_offer=lambda: presenter.split_large())
    panel = ft.Container(
        content=ft.Column(
            [ft.Column([home.control, *pages], spacing=0, expand=True), message, actions.control],
            spacing=SPACE,
            expand=True,
        ),
        padding=ft.Padding.all(GAP),
        bgcolor=role("ground"),
        border=ft.Border.all(1, role("border")),
        border_radius=ft.BorderRadius.all(RADIUS),
        expand=True,
    )
    surface = Surface(panel)
    root = ft.Container(
        content=ft.Row(
            [rail.control, surface.control],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        padding=ft.Padding.only(left=GAP, top=GAP, right=0, bottom=GAP),
        bgcolor=role("ground"),
        expand=True,
    )
    return Frame(
        root, rail, surface, panel, pages, home, actions, message, main, review, converting, results
    )
