"""Step 1, Choose: what to convert, where the results go, and Convert (UX §2, §5; ADR-0027)."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.models import InputRow, OutputChoice
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk.components.file_list import ListRow
from clearmd.frontend.ttk.components.inputs_card import InputsCard
from clearmd.frontend.ttk.components.output_card import OutputCard
from clearmd.frontend.ttk.components.split_choice import OnSplit
from clearmd.frontend.ttk.visuals.style_names import PAGE
from clearmd.i18n import Catalog


class ChooseView(ttk.Frame):
    """Add files / Add folder and the drop zone, the numbered list, the output choice, Convert."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
        on_add_files: Callable[[], None],
        on_add_folder: Callable[[], None],
        on_remove: Callable[[list[Path]], None],
        on_clear: Callable[[], None],
        on_next_to: Callable[[], None],
        on_pick_folder: Callable[[], None],
        on_summary: Callable[[str], None] = lambda _format: None,
        on_images: Callable[[str], None] = lambda _images: None,
        on_split: OnSplit = lambda **_choice: None,
    ) -> None:
        super().__init__(parent, style=PAGE)
        self._texts: list[tuple[Any, str]] = []  # a widget with a text, and its catalog key
        self._short = False  # a short window (review of 011)
        self._splitting = False  # Split's choices shown (feature 023)

        inputs = InputsCard(
            self,
            fonts=fonts,
            on_add_files=on_add_files,
            on_add_folder=on_add_folder,
            on_remove=on_remove,
            on_clear=on_clear,
            label=self._label,
        )
        self._inputs_card = inputs
        self.add_files = inputs.add_files
        self.add_folder = inputs.add_folder
        self.drop_zone = inputs.drop_zone
        self.inputs = inputs.inputs
        self.remove = inputs.remove
        self.clear = inputs.clear
        self.deselect = inputs.deselect

        output = OutputCard(
            self,
            before=inputs.editing,
            fonts=fonts,
            on_next_to=on_next_to,
            on_pick_folder=on_pick_folder,
            on_summary=on_summary,
            on_images=on_images,
            on_split=on_split,
            label=self._label,
        )
        self.output_mode = output.output_mode
        self.next_to = output.next_to
        self.in_folder = output.in_folder
        self.pick = output.pick
        self.output_label = output.output_label
        self.summary_format = output.summary_format
        self.summary_buttons = output.summary_buttons
        self.images = output.images
        self._output = output
        self.split = output.split
        self.pictures = output.pictures

    # --- What the presenter shows ------------------------------------------------------------

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self.inputs.show(
            [
                ListRow(row.icon, f"{row.name}/" if row.is_folder else row.name, (row.location,),
                        payload=row.path)
                for row in rows
            ]
        )  # fmt: skip

    def set_short(self, short: bool) -> None:
        """A short window: the add buttons side by side and a lower drop zone, so the list keeps
        its rows (review of 011: at 800 x 560 it had none)."""
        self._short = short
        self._inputs_card.set_short(short or self._splitting)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self._output.show(choice)
        splitting = choice.tool is Tool.SPLIT
        if splitting != self._splitting:  # Split's taller card: the short entry keeps the list
            self._splitting = splitting
            self._inputs_card.set_short(self._short or splitting)

    def apply_language(self, catalog: Catalog) -> None:
        for widget, key in self._texts:
            widget.configure(text=catalog.text(key))
        self.drop_zone.show_text(catalog.text("gui.main.drop"))
        self.inputs.apply_headings(
            catalog.text("gui.main.column_name"),
            [catalog.text("gui.main.column_location")],
            catalog.text("gui.main.empty"),
        )

    def apply_palette(self, palette: Palette) -> None:
        self.drop_zone.apply_palette(palette)
        self.inputs.apply_palette(palette)

    def _label(self, widget: Any, key: str) -> None:
        self._texts.append((widget, key))
