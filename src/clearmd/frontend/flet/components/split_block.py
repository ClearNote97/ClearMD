"""How to Split (features 023, 024): the cut (into N parts, every N pages, parts of about N words,
each with its number), what to keep of the parts, the line that says nothing inside them changes
and the hint that the words are approximate. Step 1 of Split shows it in the results card, in
place of the images' choice.

flet's controls are taller than Qt's: Keep sits on the title's row (where Convert's card has the
images' choice) and the radio buttons are compact, so one listed file still shows at 1080 x 720."""

from collections.abc import Callable
from functools import partial

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.flet.components.number_field import NumberField
from clearmd.frontend.flet.components.primitives import Choice, Wording, label, stretch
from clearmd.frontend.presenter.models import OutputChoice

CUTS = ("parts", "pages", "words")
KEEPS = ("pdf", "markdown", "both")
# Each box as wide as its largest number: 10 000 parts or pages, 1 000 000 words.
WIDTHS = {"parts": 8 * SPACE, "pages": 8 * SPACE, "words": 11 * SPACE}
# The radio's text and the unit after the box, by cut.
WORDS = {
    "parts": ("gui.split.into", "gui.split.parts"),
    "pages": ("gui.split.every", "gui.split.pages"),
    "words": ("gui.split.words", "gui.split.words_unit"),
}


def _send(on_split: Callable[..., None], cut: str, number: int) -> None:
    """A cut's number to the presenter: ``parts=``, ``pages=`` or ``words=``."""
    on_split(**{cut: number})


def _compact(choice: Choice) -> None:
    for radio in choice.radios.values():
        radio.visual_density = ft.VisualDensity.COMPACT


class SplitBlock:
    """The cut and what to keep: each change goes to ``on_split`` as the presenter takes it
    (``cut=``, ``parts=``, ``pages=``, ``words=`` or ``keep=``)."""

    def __init__(self, wording: Wording, *, on_split: Callable[..., None]) -> None:
        title, keep_title = label("strong"), label("strong")
        wording.add(title, "gui.split.title")
        wording.add(keep_title, "gui.split.keep")
        self.keep = Choice(KEEPS, lambda keep: on_split(keep=keep), spacing=SPACE)
        for value in KEEPS:
            wording.add(self.keep.radios[value], f"gui.split.keep_{value}")
        _compact(self.keep)
        heading = ft.Row(
            [title, stretch(), keep_title, self.keep.control],
            spacing=SPACE,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.cut = Choice(CUTS, lambda cut: on_split(cut=cut))
        _compact(self.cut)
        self.numbers = {
            cut: NumberField(partial(_send, on_split, cut), width=WIDTHS[cut]) for cut in CUTS
        }
        self.parts, self.pages, self.words = (self.numbers[cut] for cut in CUTS)
        pairs: list[ft.Control] = []
        for cut in CUTS:
            radio_key, unit_key = WORDS[cut]
            wording.add(self.cut.radios[cut], radio_key)
            unit = label("onPage")
            wording.add(unit, unit_key)
            pairs.append(self._pair(self.cut.radios[cut], self.numbers[cut], unit))
        # The three cuts on their own row; a narrow window wraps them, each pair whole.
        self.cut.row.controls = pairs
        self.cut.row.spacing, self.cut.row.run_spacing = GAP, HALF
        self.cut.row.wrap = True
        self.note, self.hint = label("muted"), label("muted")
        wording.add(self.note, "gui.split.note")
        wording.add(self.hint, "gui.split.hint")
        self.control = ft.Column(
            [heading, self.cut.control, self.note, self.hint], spacing=HALF, tight=True
        )

    @staticmethod
    def _pair(radio: ft.Radio, number: NumberField, unit: ft.Text) -> ft.Row:
        return ft.Row(
            [radio, number.field, unit],
            spacing=HALF,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def show(self, choice: OutputChoice) -> None:
        self.cut.set(choice.split_cut)
        self.parts.set(choice.split_parts)
        self.pages.set(choice.split_pages)
        self.words.set(choice.split_words)
        self.keep.set(choice.split_keep)

    def set_disabled(self, disabled: bool) -> None:
        self.cut.set_disabled(disabled)
        self.keep.set_disabled(disabled)
        for number in self.numbers.values():
            number.field.disabled = disabled
