"""The arrangement of the window: the rail on the left; on the right the surface with the four
step views, the message and the action bar. A module of its own: it builds the widgets and nothing
else, the window wires them."""

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.presenter import Presenter
from clearmd.frontend.ttk.components.action_bar import ActionBar
from clearmd.frontend.ttk.components.rail import Rail
from clearmd.frontend.ttk.components.surface import Surface
from clearmd.frontend.ttk.views.choose import ChooseView
from clearmd.frontend.ttk.views.convert import ConvertView
from clearmd.frontend.ttk.views.results import ResultsView
from clearmd.frontend.ttk.views.review import ReviewView
from clearmd.frontend.ttk.visuals.style_names import WARNING
from clearmd.frontend.ttk.window.dialog_host import DialogHost


@dataclass(frozen=True)
class Frame:
    rail: Rail
    surface: Surface
    actions: ActionBar
    message: ttk.Label
    main: ChooseView
    review: ReviewView
    converting: ConvertView
    results: ResultsView


def build_frame(
    root: tk.Misc,
    fonts: dict[str, Any],
    presenter: Presenter,
    dialogs: DialogHost,
    *,
    on_primary: Callable[[], None],
    on_add_files: Callable[[], None],
    on_add_folder: Callable[[], None],
    on_pick_folder: Callable[[], None],
) -> Frame:
    rail = Rail(
        root,
        fonts=fonts,
        on_settings=dialogs.show_settings,
        on_help=dialogs.show_help,
        on_step=lambda page: presenter.go_to(page),
    )
    rail.pack(side="left", fill="y")
    surface = Surface(root, fonts=fonts)
    surface.pack(side="left", fill="both", expand=True)
    page = surface.page

    # One action bar for every page (ADR-0029), the message above it.
    actions = ActionBar(page, on_primary=on_primary)
    actions.pack(side="bottom", fill="x", pady=(SPACE, 0))
    message = ttk.Label(page, style=WARNING, anchor="w", justify="left")
    page.bind("<Configure>", lambda event: message.configure(wraplength=event.width))
    message.pack(side="bottom", fill="x", pady=(SPACE, 0))
    main = ChooseView(
        page,
        fonts=fonts,
        on_add_files=on_add_files,
        on_add_folder=on_add_folder,
        on_remove=lambda paths: presenter.remove_inputs(paths),
        on_clear=lambda: presenter.clear_inputs(),
        on_next_to=lambda: presenter.choose_output_next_to(),
        on_pick_folder=on_pick_folder,
        on_summary=lambda value: presenter.choose_summary_format(value),
        on_images=lambda value: presenter.choose_images(value),
    )
    review = ReviewView(page, fonts=fonts)
    converting = ConvertView(page, fonts=fonts)
    results = ResultsView(page, fonts=fonts)
    return Frame(rail, surface, actions, message, main, review, converting, results)
