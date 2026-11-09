"""The Choose step's output half: where the results go, the summary's format and the images'
choice, or Split's and Merge's own choices in place of the images' (features 023, 026). It builds
its widgets on the step's own frame, so the layout stays the step's. In a small window the card
scrolls, so the list above keeps its rows (feature 032)."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.presenter.models import OutputChoice, OutputMode
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk.components.merge_choice import MergeChoice
from clearmd.frontend.ttk.components.scroll_area import ScrollArea
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
        card = ttk.Frame(bottom, style=CARD, padding=GAP)
        card.pack(side="left", fill="x", expand=True)
        self.area = ScrollArea(card, ground="#FFFFFF", fixed_width=False)  # 032
        self.area.pack(fill="both", expand=True)
        output = self.area.inner
        output.bind("<Configure>", lambda _event: self._place_summary(), add="+")
        self._narrow: bool | None = None  # the summary under the title (a narrow card)
        heading = ttk.Frame(
            output, style="TFrame"
        )  # the title, and the images' choice at its right
        heading.pack(fill="x")
        self._heading = heading
        # Split's choices: above the output's, shown only while the tool is Split (feature 023).
        self.split = SplitChoice(output, fonts=fonts, on_split=on_split, label=label)
        self.merge = MergeChoice(output, fonts=fonts, on_split=on_split, label=label)  # 026
        self._tool = Tool.CONVERT
        title = ttk.Label(heading, font=fonts["strong"])
        title.pack(side="left")
        label(title, "gui.main.output_title")
        self._title = title
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
        self.area.follow_focus()

    def show(self, choice: OutputChoice) -> None:
        """The choice as the presenter has it; Split's or Merge's block in place of the images."""
        self.output_mode.set(choice.mode.value)
        self.output_label.configure(text=choice.label)
        self.summary_format.set(choice.summary_format)
        self.images.set(choice.images)
        self.split.show(choice)
        self.merge.show(choice)
        if choice.tool is self._tool:
            return
        self._tool = choice.tool
        # The tool's block above; the summary takes the images' place, at the title's right, so
        # the list keeps its rows (features 023, 026).
        for widget in (self.pictures, self._summary, self.split, self.merge):
            widget.pack_forget()
        block = {Tool.SPLIT: self.split, Tool.MERGE: self.merge}.get(choice.tool)
        self._narrow = None
        if block is not None:
            block.pack(fill="x", pady=(0, HALF), before=self._heading)
            self._place_summary()
        else:
            self.pictures.pack(side="right")
            self._summary.pack(in_=self._output, fill="x", pady=(GAP, 0))
            for button in self.summary_buttons[:3]:
                button.pack_configure(padx=(GAP, 0))  # Convert: its own row, as before

    def _place_summary(self) -> None:
        """For Split and Merge, the summary at the title's right, or under it when the card is
        too narrow for both (an 800 px window, feature 032)."""
        if self._tool is Tool.CONVERT:
            return
        width = self._output.winfo_width()
        buttons = self.summary_buttons[:3]  # beside the title, SPACE apart (038: longer words)
        tight = self._summary.winfo_reqwidth() - 3 * (GAP - SPACE) * (self._narrow is not False)
        needed = self._title.winfo_reqwidth() + GAP + tight
        narrow = width > 1 and needed > width
        if narrow == self._narrow:
            return
        self._narrow = narrow
        self._summary.pack_forget()
        for button in buttons:
            button.pack_configure(padx=(GAP if narrow else SPACE, 0))
        if narrow:
            self._summary.pack(in_=self._output, fill="x", pady=(SPACE, 0), after=self._heading)
        else:
            self._summary.pack(in_=self._heading, side="right")
