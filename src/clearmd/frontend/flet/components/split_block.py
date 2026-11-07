"""How to Split (feature 023): the cut (into N parts, every N pages, each with its number), what to
keep of the parts, and the line that says nothing inside them changes. Step 1 of Split shows it in
the results card, in place of the images' choice."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.flet.components.primitives import Choice, Wording, label
from clearmd.frontend.flet.visuals.look import text_style
from clearmd.frontend.flet.visuals.theme import role
from clearmd.frontend.presenter.models import OutputChoice

NUMBER_WIDTH = 10 * SPACE  # five digits: the cut's numbers go up to 10 000


class NumberField:
    """A whole number, given to ``on_number`` on Enter or when the field loses the focus (never on
    each keystroke); ``set`` shows the presenter's number (a refused one is put back)."""

    def __init__(self, on_number: Callable[[int], None]) -> None:
        self._on_number = on_number
        self._shown = ""
        self.field = ft.TextField(
            width=NUMBER_WIDTH,
            dense=True,
            text_align=ft.TextAlign.RIGHT,
            text_style=text_style("onPage"),
            bgcolor=role("card"),
            border_color=role("border"),
            focused_border_color=role("accent"),
            input_filter=ft.InputFilter(regex_string=r"^[0-9]*$", allow=True),  # digits only
            on_submit=self.commit,
            on_blur=self.commit,
        )

    def set(self, number: int) -> None:
        self._shown = str(number)
        self.field.value = self._shown

    def type(self, text: str) -> None:
        """The user types ``text`` (tests): nothing is given until it is committed."""
        self.field.value = text

    def commit(self) -> None:
        text = str(self.field.value or "").strip()
        if text == self._shown:
            return
        try:
            number = int(text)
        except ValueError:
            self.field.value = self._shown  # nothing, or not a number: the shown one stays
            return
        self._on_number(number)


class SplitBlock:
    """The cut and what to keep: each change goes to ``on_split`` as the presenter takes it
    (``cut=``, ``parts=``, ``pages=`` or ``keep=``)."""

    def __init__(self, wording: Wording, *, on_split: Callable[..., None]) -> None:
        title = label("strong")
        parts_word, pages_word, keep_title = label("onPage"), label("onPage"), label("onPage")
        wording.add(title, "gui.split.title")
        wording.add(parts_word, "gui.split.parts")
        wording.add(pages_word, "gui.split.pages")
        wording.add(keep_title, "gui.split.keep")
        self.cut = Choice(("parts", "pages"), lambda cut: on_split(cut=cut))
        wording.add(self.cut.radios["parts"], "gui.split.into")
        wording.add(self.cut.radios["pages"], "gui.split.every")
        self.parts = NumberField(lambda number: on_split(parts=number))
        self.pages = NumberField(lambda number: on_split(pages=number))
        self.cut.row.controls = [
            self._pair(self.cut.radios["parts"], self.parts, parts_word),
            self._pair(self.cut.radios["pages"], self.pages, pages_word),
        ]
        self.cut.row.spacing = 3 * SPACE
        self.keep = Choice(("pdf", "markdown", "both"), lambda keep: on_split(keep=keep))
        for value in ("pdf", "markdown", "both"):
            wording.add(self.keep.radios[value], f"gui.split.keep_{value}")
        self.note = label("muted")
        wording.add(self.note, "gui.split.note")
        keep = ft.Row([keep_title, self.keep.control], spacing=GAP)
        self.control = ft.Column([title, self.cut.control, keep, self.note], spacing=SPACE)

    @staticmethod
    def _pair(radio: ft.Radio, number: NumberField, word: ft.Text) -> ft.Row:
        return ft.Row(
            [radio, number.field, word],
            spacing=HALF,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def show(self, choice: OutputChoice) -> None:
        self.cut.set(choice.split_cut)
        self.parts.set(choice.split_parts)
        self.pages.set(choice.split_pages)
        self.keep.set(choice.split_keep)

    def set_disabled(self, disabled: bool) -> None:
        self.cut.set_disabled(disabled)
        self.keep.set_disabled(disabled)
        self.parts.field.disabled = self.pages.field.disabled = disabled
