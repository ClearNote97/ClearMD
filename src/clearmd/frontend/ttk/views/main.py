"""Step 1, Choose: what to convert, where the results go, and Convert (UX §2, §5; ADR-0027)."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from clearmd.frontend.presenter.models import InputRow, OutputChoice, OutputMode
from clearmd.frontend.ttk.brand import (
    CARD,
    LINK,
    MUTED,
    PAGE,
    SOFT,
    SOFT_ON_CARD,
    Palette,
)
from clearmd.frontend.ttk.components.drop_zone import DropZone
from clearmd.frontend.ttk.components.file_list import Column, FileList, ListRow
from clearmd.frontend.ttk.layout import GAP, HALF, SPACE
from clearmd.i18n import Catalog

TALL_DROP = 11 * SPACE  # the drop zone beside the two buttons, one over the other
SHORT_DROP = 6 * SPACE  # beside them side by side, in a short window (review of 011)


class MainView(ttk.Frame):
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
    ) -> None:
        super().__init__(parent, style=PAGE)
        self._on_remove = on_remove
        self._texts: list[tuple[Any, str]] = []  # a widget with a text, and its catalog key

        entry = ttk.Frame(self, style=PAGE)
        entry.pack(fill="x")
        buttons = ttk.Frame(entry, style=PAGE)
        buttons.pack(side="left", fill="y")
        self.add_files = ttk.Button(buttons, style=SOFT, command=on_add_files)
        self.add_folder = ttk.Button(buttons, style=SOFT, command=on_add_folder)
        self._short = False
        self._stack_buttons()
        self._label(self.add_files, "gui.main.add_files")
        self._label(self.add_folder, "gui.main.add_folder")
        self.drop_zone = DropZone(entry, fonts=fonts, on_click=on_add_files)
        self.drop_zone.pack(side="left", fill="both", expand=True, padx=(GAP, 0))

        self.inputs = FileList(
            self,
            name_heading="gui.main.column_name",
            columns=(Column("location", 320, stretch=True),),
            height=4,
        )
        self.inputs.pack(fill="both", expand=True, pady=(GAP, 0))
        self.inputs.tree.bind("<Delete>", lambda _event: self._remove_selected())

        editing = ttk.Frame(self, style=PAGE)
        # The output card and the editing links stay at the bottom; the list takes what is left,
        # so nothing is cut at the smallest window (code review of 007).
        editing.pack(side="bottom", fill="x", pady=(HALF, 0), before=self.inputs)
        self.remove = ttk.Button(editing, style=LINK, command=self._remove_selected)
        self.remove.pack(side="left")
        self.clear = ttk.Button(editing, style=LINK, command=on_clear)
        self.clear.pack(side="left", padx=(SPACE, 0))
        self.deselect = ttk.Button(editing, style=LINK, command=self.inputs.clear_selection)
        self.deselect.pack(side="left", padx=(SPACE, 0))
        self._label(self.deselect, "gui.main.deselect")
        self._label(self.remove, "gui.main.remove")
        self._label(self.clear, "gui.main.clear")

        bottom = ttk.Frame(self, style=PAGE)
        bottom.pack(side="bottom", fill="x", pady=(SPACE, 0), before=editing)
        output = ttk.Frame(bottom, style=CARD, padding=GAP)
        output.pack(side="left", fill="x", expand=True)
        heading = ttk.Frame(
            output, style="TFrame"
        )  # the title, and the images' choice at its right
        heading.pack(fill="x")
        title = ttk.Label(heading, font=fonts["strong"])
        title.pack(side="left")
        self._label(title, "gui.main.output_title")
        choices = ttk.Frame(output, style="TFrame")
        choices.pack(fill="x", pady=(SPACE, 0))
        self.output_mode = tk.StringVar(value=OutputMode.NEXT_TO.value)
        self.next_to = ttk.Radiobutton(
            choices, variable=self.output_mode, value=OutputMode.NEXT_TO.value, command=on_next_to
        )
        self.next_to.pack(side="left")
        self._label(self.next_to, "gui.output.next_to")
        self.in_folder = ttk.Radiobutton(
            choices,
            variable=self.output_mode,
            value=OutputMode.FOLDER.value,
            command=on_pick_folder,
        )
        self.in_folder.pack(side="left", padx=(GAP, 0))
        self._label(self.in_folder, "gui.main.in_folder")
        self.pick = ttk.Button(choices, style=SOFT_ON_CARD, command=on_pick_folder)
        self.pick.pack(side="left", padx=(SPACE, 0))
        self._label(self.pick, "gui.main.pick_folder")
        self.output_label = ttk.Label(output, style=MUTED, anchor="w")
        self.output_label.pack(fill="x", pady=(SPACE, 0))
        # The summary's format, before starting (ADR-0031): remembered, as in Settings.
        summary = ttk.Frame(output, style="TFrame")
        summary.pack(fill="x", pady=(GAP, 0))
        summary_title = ttk.Label(summary, font=fonts["strong"])
        summary_title.pack(side="left")
        self._label(summary_title, "gui.main.summary_title")
        self.summary_format = tk.StringVar(value="markdown")
        self.summary_buttons = []
        for value, key in (
            ("markdown", "gui.main.summary_md"),
            ("markdown_pdf", "gui.main.summary_pdf"),
        ):
            button = ttk.Radiobutton(
                summary,
                variable=self.summary_format,
                value=value,
                command=lambda: on_summary(self.summary_format.get()),
            )
            button.pack(side="left", padx=(GAP, 0))
            self._label(button, key)
            self.summary_buttons.append(button)
        # Each document's images, left out or in a folder next to it (ADR-0033): remembered. On
        # the title's row, at its right: the list keeps its rows in a short window, and a narrow
        # one cuts nothing (review of 011).
        pictures = ttk.Frame(heading, style="TFrame")
        pictures.pack(side="right")
        images_title = ttk.Label(pictures, font=fonts["strong"])
        images_title.pack(side="left")
        self._label(images_title, "gui.main.images_title")
        self.images = tk.StringVar(value="omit")
        for value, key in (("omit", "gui.main.images_omit"), ("folder", "gui.main.images_folder")):
            button = ttk.Radiobutton(
                pictures,
                variable=self.images,
                value=value,
                command=lambda: on_images(self.images.get()),
            )
            button.pack(side="left", padx=(GAP, 0))
            self._label(button, key)
            self.summary_buttons.append(button)  # enabled and disabled with the output's

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
        if short != self._short:
            self._short = short
            self._stack_buttons()

    def _stack_buttons(self) -> None:
        self.add_files.pack_forget()
        self.add_folder.pack_forget()
        if self._short:
            self.add_files.pack(side="left", fill="y")
            self.add_folder.pack(side="left", fill="y", padx=(SPACE, 0))
            if hasattr(self, "drop_zone"):
                self.drop_zone.configure(height=SHORT_DROP)
        else:
            self.add_files.pack(fill="x")
            self.add_folder.pack(fill="x", pady=(SPACE, 0))
            if hasattr(self, "drop_zone"):
                self.drop_zone.configure(height=TALL_DROP)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self.output_mode.set(choice.mode.value)
        self.output_label.configure(text=choice.label)
        self.summary_format.set(choice.summary_format)
        self.images.set(choice.images)

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

    def _remove_selected(self) -> None:
        chosen = self.inputs.selected()
        if chosen:
            self._on_remove(chosen)
