"""Step 1, Choose: what to convert, where the results go (UX §2, §5; ADR-0027, ADR-0029)."""

from collections.abc import Callable
from pathlib import Path

import flet as ft

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.flet.components.file_list import ListRow
from clearmd.frontend.flet.components.inputs_card import InputsCard
from clearmd.frontend.flet.components.output_card import OutputCard
from clearmd.frontend.flet.components.primitives import Wording
from clearmd.frontend.presenter.models import InputRow, OutputChoice, OutputMode
from clearmd.i18n import Catalog


class ChooseView:
    """Add files / Add folder (two tiles while nothing is listed), the numbered list, the output
    choice."""

    def __init__(
        self,
        *,
        on_add_files: Callable[[], None],
        on_add_folder: Callable[[], None],
        on_remove: Callable[[list[Path]], None],
        on_clear: Callable[[], None],
        on_next_to: Callable[[], None],
        on_pick_folder: Callable[[], None],
        on_summary: Callable[[str], None],
        on_images: Callable[[str], None],
        on_split: Callable[..., None],
    ) -> None:
        self._wording = Wording()
        self._on_next_to = on_next_to
        self._on_pick_folder = on_pick_folder
        inputs = InputsCard(
            self._wording,
            on_add_files=on_add_files,
            on_add_folder=on_add_folder,
            on_remove=on_remove,
            on_clear=on_clear,
        )
        self.add_files, self.add_folder = inputs.add_files, inputs.add_folder
        self.start = inputs.start  # nothing listed yet: two large tiles (feature 021)
        self.entry, self.editing = inputs.entry, inputs.editing
        self._inputs_card = inputs
        self.inputs = inputs.inputs
        self.remove, self.clear, self.deselect = inputs.remove, inputs.clear, inputs.deselect
        self.remove_selected = inputs.remove_selected
        output = OutputCard(
            self._wording,
            on_mode=self._mode_chosen,
            on_pick_folder=on_pick_folder,
            on_summary=on_summary,
            on_images=on_images,
            on_split=on_split,
        )
        self._output = output
        self.mode, self.pick, self.output_label = output.mode, output.pick, output.output_label
        self.summary, self.images, self.split = output.summary, output.images, output.split
        self.choices = output.choices
        # Stretched: every card spans the page's width, as in Qt (flet's column hugs by default).
        self.control = ft.Column(
            [*inputs.controls, output.control],
            spacing=SPACE,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self._inputs_card.show_start(not rows)
        self.inputs.show_rows(
            [
                ListRow(row.icon, f"{row.name}/" if row.is_folder else row.name, (row.location,),
                        payload=row.path)
                for row in rows
            ]
        )  # fmt: skip

    def show_output_choice(self, choice: OutputChoice) -> None:
        self._output.show(choice)

    def output_mode(self) -> str:
        return self.mode.value

    def apply_language(self, catalog: Catalog) -> None:
        self._wording.apply(catalog)
        self.inputs.apply_headings(
            [catalog.text("gui.main.column_name"), catalog.text("gui.main.column_location")],
            "",  # never shown: the start tiles stand in for an empty list
        )

    def _mode_chosen(self, mode: str) -> None:
        """Next to the originals, or a folder: the folder is picked at once (as a click on Qt's
        radio button)."""
        (self._on_next_to if mode == OutputMode.NEXT_TO.value else self._on_pick_folder)()
