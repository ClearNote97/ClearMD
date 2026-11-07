"""The Choose step's output half: where the results go, the summary's format and the images'
choice, or for Split its own choices in place of the images' (feature 023). It builds its widgets
on the step's own frame, so the layout stays the step's."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.presenter.models import OutputChoice, OutputMode
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk.components.split_choice import OnSplit, SplitChoice
from clearmd.frontend.ttk.visuals.style_names import CARD, MUTED, PAGE, SOFT_ON_CARD


class OutputCard:
    """The output choice (next to the originals, in a folder), the summary's format, the images."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        before: tk.Misc,
        fonts: dict[str, tkfont.Font],
        on_next_to: Callable[[], None],
        on_pick_folder: Callable[[], None],
        on_summary: Callable[[str], None],
        on_images: Callable[[str], None],
        on_split: OnSplit,
        label: Callable[[Any, str], None],
    ) -> None:
        bottom = ttk.Frame(parent, style=PAGE)
        bottom.pack(side="bottom", fill="x", pady=(SPACE, 0), before=before)
        output = ttk.Frame(bottom, style=CARD, padding=GAP)
        output.pack(side="left", fill="x", expand=True)
        heading = ttk.Frame(
            output, style="TFrame"
        )  # the title, and the images' choice at its right
        heading.pack(fill="x")
        self._heading = heading
        # Split's choices: above the output's, shown only while the tool is Split (feature 023).
        self.split = SplitChoice(output, fonts=fonts, on_split=on_split, label=label)
        title = ttk.Label(heading, font=fonts["strong"])
        title.pack(side="left")
        label(title, "gui.main.output_title")
        choices = ttk.Frame(output, style="TFrame")
        choices.pack(fill="x", pady=(SPACE, 0))
        self.output_mode = tk.StringVar(value=OutputMode.NEXT_TO.value)
        self.next_to = ttk.Radiobutton(
            choices, variable=self.output_mode, value=OutputMode.NEXT_TO.value, command=on_next_to
        )
        self.next_to.pack(side="left")
        label(self.next_to, "gui.output.next_to")
        self.in_folder = ttk.Radiobutton(
            choices,
            variable=self.output_mode,
            value=OutputMode.FOLDER.value,
            command=on_pick_folder,
        )
        self.in_folder.pack(side="left", padx=(GAP, 0))
        label(self.in_folder, "gui.main.in_folder")
        self.pick = ttk.Button(choices, style=SOFT_ON_CARD, command=on_pick_folder)
        self.pick.pack(side="left", padx=(SPACE, 0))
        label(self.pick, "gui.main.pick_folder")
        self.output_label = ttk.Label(output, style=MUTED, anchor="w")
        self.output_label.pack(fill="x", pady=(SPACE, 0))
        # The summary's format, before starting (ADR-0031): remembered, as in Settings.
        summary = ttk.Frame(output, style="TFrame")
        summary.pack(fill="x", pady=(GAP, 0))
        self._output, self._summary = output, summary
        summary_title = ttk.Label(summary, font=fonts["strong"])
        summary_title.pack(side="left")
        label(summary_title, "gui.main.summary_title")
        self.summary_format = tk.StringVar(value="markdown")
        self.summary_buttons: list[ttk.Radiobutton] = []
        for value, key in (
            ("markdown", "gui.main.summary_md"),
            ("markdown_pdf", "gui.main.summary_pdf"),
            ("pdf", "gui.main.summary_pdf_only"),
        ):
            button = ttk.Radiobutton(
                summary,
                variable=self.summary_format,
                value=value,
                command=lambda: on_summary(self.summary_format.get()),
            )
            button.pack(side="left", padx=(GAP, 0))
            label(button, key)
            self.summary_buttons.append(button)
        # Each document's images, left out or in a folder next to it (ADR-0033): remembered. On
        # the title's row, at its right: the list keeps its rows in a short window, and a narrow
        # one cuts nothing (review of 011).
        pictures = ttk.Frame(heading, style="TFrame")
        pictures.pack(side="right")
        self.pictures = pictures
        images_title = ttk.Label(pictures, font=fonts["strong"])
        images_title.pack(side="left")
        label(images_title, "gui.main.images_title")
        self.images = tk.StringVar(value="omit")
        for value, key in (("omit", "gui.main.images_omit"), ("folder", "gui.main.images_folder")):
            button = ttk.Radiobutton(
                pictures,
                variable=self.images,
                value=value,
                command=lambda: on_images(self.images.get()),
            )
            button.pack(side="left", padx=(GAP, 0))
            label(button, key)
            self.summary_buttons.append(button)  # enabled and disabled with the output's

    def show(self, choice: OutputChoice) -> None:
        """The choice as the presenter has it; Split's block in place of the images for Split."""
        self.output_mode.set(choice.mode.value)
        self.output_label.configure(text=choice.label)
        self.summary_format.set(choice.summary_format)
        self.images.set(choice.images)
        self.split.show(choice)
        splitting = choice.tool is Tool.SPLIT
        if splitting == bool(self.split.winfo_manager()):
            return
        # Split's block above; the summary takes the images' place, at the title's right, so the
        # list keeps its rows (feature 023).
        self.pictures.pack_forget()
        self._summary.pack_forget()
        if splitting:
            self.split.pack(fill="x", pady=(0, GAP), before=self._heading)
            self._summary.pack(in_=self._heading, side="right")
        else:
            self.split.pack_forget()
            self.pictures.pack(side="right")
            self._summary.pack(in_=self._output, fill="x", pady=(GAP, 0))
