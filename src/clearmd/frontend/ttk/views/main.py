"""The main screen: what to convert, where the results go, and Convert (UX §2, §5)."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from typing import Any

import ttkbootstrap as tb

from clearmd.frontend.presenter.models import InputRow, OutputChoice, OutputMode
from clearmd.frontend.ttk.layout import GAP, HALF, SPACE
from clearmd.i18n import Catalog


class MainView(tb.Frame):
    """Add files / Add folder / drop zone, the inputs, the output choice and Convert."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        on_add_files: Callable[[], None],
        on_add_folder: Callable[[], None],
        on_remove: Callable[[Path], None],
        on_clear: Callable[[], None],
        on_next_to: Callable[[], None],
        on_pick_folder: Callable[[], None],
        on_convert: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self._on_remove = on_remove
        self._rows: dict[str, Path] = {}
        self._texts: list[tuple[Any, str]] = []  # a widget with a text, and its catalog key

        entry = tb.Frame(self)
        entry.pack(fill="x")
        self.add_files = tb.Button(entry, command=on_add_files, bootstyle="secondary")
        self.add_files.pack(side="left")
        self.add_folder = tb.Button(entry, command=on_add_folder, bootstyle="secondary")
        self.add_folder.pack(side="left", padx=(SPACE, 0))
        self._label(self.add_files, "gui.main.add_files")
        self._label(self.add_folder, "gui.main.add_folder")

        zone = tb.Frame(self, bootstyle="secondary", padding=1)  # a 1 px border around the zone
        zone.pack(fill="x", pady=(SPACE, 0))
        self.drop_zone = tb.Label(zone, anchor="center", padding=GAP, bootstyle="secondary")
        self.drop_zone.pack(fill="x")
        self._label(self.drop_zone, "gui.main.drop")

        listing = tb.Frame(self)
        listing.pack(fill="both", expand=True, pady=(GAP, 0))
        self.inputs = tb.Treeview(listing, columns=("location",), height=6, selectmode="extended")
        self.inputs.pack(side="left", fill="both", expand=True)
        scroll = tb.Scrollbar(listing, orient="vertical", command=self.inputs.yview)
        scroll.pack(side="left", fill="y")
        self.inputs.configure(yscrollcommand=scroll.set)
        self.inputs.bind("<Delete>", lambda _event: self._remove_selected())
        self.empty = tb.Label(self, anchor="w", bootstyle="secondary")
        self.empty.pack(fill="x", pady=(HALF, 0))
        self._label(self.empty, "gui.main.empty")

        editing = tb.Frame(self)
        editing.pack(fill="x", pady=(SPACE, 0))
        self.remove = tb.Button(editing, command=self._remove_selected, bootstyle="link")
        self.remove.pack(side="left")
        self.clear = tb.Button(editing, command=on_clear, bootstyle="link")
        self.clear.pack(side="left", padx=(SPACE, 0))
        self._label(self.remove, "gui.main.remove")
        self._label(self.clear, "gui.main.clear")

        output = tb.Labelframe(self, padding=GAP)
        output.pack(fill="x", pady=(GAP, 0))
        self._label(output, "gui.main.output_title")
        self.output_mode = tk.StringVar(value=OutputMode.NEXT_TO.value)
        self.next_to = tb.Radiobutton(
            output, variable=self.output_mode, value=OutputMode.NEXT_TO.value, command=on_next_to
        )
        self.next_to.pack(anchor="w")
        self._label(self.next_to, "gui.output.next_to")
        chosen = tb.Frame(output)
        chosen.pack(fill="x", pady=(SPACE, 0))
        self.in_folder = tb.Radiobutton(
            chosen, variable=self.output_mode, value=OutputMode.FOLDER.value, command=on_pick_folder
        )
        self.in_folder.pack(side="left")
        self._label(self.in_folder, "gui.main.in_folder")
        self.pick = tb.Button(chosen, command=on_pick_folder, bootstyle="link")
        self.pick.pack(side="left", padx=(SPACE, 0))
        self._label(self.pick, "gui.main.pick_folder")
        self.output_label = tb.Label(output, anchor="w", bootstyle="secondary")
        self.output_label.pack(fill="x", pady=(SPACE, 0))

        self.convert = tb.Button(self, command=on_convert, bootstyle="primary")
        self.convert.pack(anchor="e", pady=(GAP, 0), ipadx=GAP, ipady=SPACE)
        self._label(self.convert, "gui.main.convert")

    # --- What the presenter shows ------------------------------------------------------------

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self.inputs.delete(*self.inputs.get_children())
        self._rows.clear()
        for row in rows:
            shown = f"{row.name}/" if row.is_folder else row.name
            item = self.inputs.insert("", "end", text=shown, values=(row.location,))
            self._rows[item] = row.path
        if rows:
            self.empty.pack_forget()
        elif not self.empty.winfo_ismapped():
            self.empty.pack(fill="x", pady=(HALF, 0), after=self.inputs.master)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self.output_mode.set(choice.mode.value)
        self.output_label.configure(text=choice.label)

    def apply_language(self, catalog: Catalog) -> None:
        for widget, key in self._texts:
            widget.configure(text=catalog.text(key))
        self.inputs.heading("#0", text=catalog.text("gui.main.column_name"), anchor="w")
        self.inputs.heading("location", text=catalog.text("gui.main.column_location"), anchor="w")

    def _label(self, widget: Any, key: str) -> None:
        self._texts.append((widget, key))

    def _remove_selected(self) -> None:
        for item in self.inputs.selection():
            path = self._rows.get(item)
            if path is not None:
                self._on_remove(path)
