"""Choose before anything is chosen (feature 021): two large tiles, Add files and Add folder, in
the room the list will take. flet 1.0 cannot receive files dropped from the system, so the empty
list is not a drop zone: it is the two ways in, each with what it takes."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF, RADIUS, SPACE
from clearmd.frontend.flet.components.primitives import Wording, label
from clearmd.frontend.flet.visuals.look import tile_style
from clearmd.frontend.flet.visuals.theme import role

TILE_HEIGHT = 17 * SPACE  # 136: the icon, the title and two lines of text, with room around
ICON_SIZE = 5 * SPACE  # 40


class Tile:
    """A large button: an icon, a title and what it takes."""

    def __init__(
        self,
        wording: Wording,
        icon: ft.IconData,
        title: str,
        body: str,
        on_click: Callable[[], None],
    ) -> None:
        self.icon = ft.Icon(icon, size=ICON_SIZE, color=role("accent_text"))
        self.title = label("strong")
        self.body = label("muted")
        self.body.text_align = ft.TextAlign.CENTER
        wording.add(self.title, title)
        wording.add(self.body, body)
        column = ft.Column(
            [self.icon, self.title, self.body],
            spacing=HALF,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.control = ft.Button(
            content=column,
            style=tile_style(),
            height=TILE_HEIGHT,
            expand=True,
            on_click=on_click,
        )


class StartPanel:
    """The two tiles side by side, a hint under them, in the list's own frame."""

    def __init__(
        self,
        wording: Wording,
        *,
        on_add_files: Callable[[], None],
        on_add_folder: Callable[[], None],
    ) -> None:
        self.files = Tile(
            wording,
            ft.Icons.NOTE_ADD_OUTLINED,
            "gui.main.add_files",
            "gui.main.start_files",
            on_add_files,
        )
        self.folder = Tile(
            wording,
            ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
            "gui.main.add_folder",
            "gui.main.start_folder",
            on_add_folder,
        )
        self.hint = label("hint")
        self.hint.text_align = ft.TextAlign.CENTER
        wording.add(self.hint, "gui.main.start_hint")
        tiles = ft.Row([self.files.control, self.folder.control], spacing=GAP)
        self.control = ft.Container(
            content=ft.Column(
                [tiles, self.hint],
                spacing=GAP,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=ft.Padding.all(2 * GAP),
            bgcolor=role("card"),
            border=ft.Border.all(1, role("border")),
            border_radius=ft.BorderRadius.all(RADIUS),
        )
