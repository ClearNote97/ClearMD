"""The settings' Split group (features 023, 024): the cut (into N parts, every N pages, parts of
about N words, each with its number) and what to keep, as the settings dialog's other rows."""

from dataclasses import replace

import flet as ft

from clearmd.backend.schemas.settings import RANGES, Settings
from clearmd.frontend.design.metrics import GAP
from clearmd.frontend.flet.components.primitives import label
from clearmd.frontend.flet.layout.units import CONTROL_WIDTH
from clearmd.frontend.flet.visuals.look import text_style
from clearmd.frontend.flet.visuals.theme import role
from clearmd.i18n import Catalog

KEEPS = ("pdf", "markdown", "both")
CUTS = ("parts", "pages", "words")  # each with its number: split_parts, split_pages, split_words


def _row(left: ft.Control, right: ft.Control | None = None) -> ft.Row:
    """A row of the dialog: what it is, and its control in the dialog's one column."""
    holder = ft.Container(content=right, width=CONTROL_WIDTH)
    return ft.Row(
        [ft.Container(content=left, expand=True), holder],
        spacing=GAP,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _boxed[Boxed: (ft.TextField, ft.Dropdown)](control: Boxed) -> Boxed:
    control.width = CONTROL_WIDTH
    control.text_style = text_style("onPage")
    control.bgcolor = role("card")
    control.border_color = role("border")
    control.focused_border_color = role("accent")
    return control


class SplitSettings:
    """The cut as three radio buttons, each with its number, and Keep as a list of three."""

    def __init__(self, catalog: Catalog) -> None:
        text = catalog.text
        digits = ft.InputFilter(regex_string=r"^[0-9]*$", allow=True)
        self.radios: dict[str, ft.Radio] = {}
        self.numbers: dict[str, ft.TextField] = {}
        rows: list[ft.Control] = []
        for cut in CUTS:
            words = text(f"gui.settings.split_{cut}")
            radio = ft.Radio(value=cut, label=words, label_style=text_style("onPage"))
            field = _boxed(ft.TextField(input_filter=digits, dense=True))
            field.tooltip = words
            self.radios[cut], self.numbers[cut] = radio, field
            rows.append(_row(radio, field))
        self.parts, self.pages, self.words = (self.numbers[cut] for cut in CUTS)
        self.keep = _boxed(
            ft.Dropdown(
                options=[
                    ft.DropdownOption(key=value, text=text(f"gui.split.keep_{value}"))
                    for value in KEEPS
                ]
            )
        )
        self.keep.tooltip = text("gui.settings.split_keep")
        heading = ft.Column(
            [label("strong", text("gui.settings.split")),
             label("muted", text("gui.settings.split_help"))],
            spacing=0,
        )  # fmt: skip
        cuts = ft.Column(rows, spacing=GAP, tight=True)
        self.cut = ft.RadioGroup(content=cuts, value="parts")
        keep = _row(label("onPage", text("gui.settings.split_keep")), self.keep)
        self.controls: list[ft.Control] = [_row(heading), self.cut, keep]

    def load(self, settings: Settings) -> None:
        self.cut.value = settings.split_cut
        for cut, field in self.numbers.items():
            field.value = str(getattr(settings, f"split_{cut}"))
        self.keep.value = settings.split_keep

    def chosen(self, settings: Settings) -> Settings:
        """``settings`` with the group's choices; a number out of its range keeps the saved one."""
        numbers = {
            f"split_{cut}": _number(str(field.value or ""), f"split_{cut}", settings)
            for cut, field in self.numbers.items()
        }
        return replace(
            settings,
            split_cut=str(self.cut.value or settings.split_cut),
            split_parts=numbers["split_parts"],
            split_pages=numbers["split_pages"],
            split_words=numbers["split_words"],
            split_keep=str(self.keep.value or settings.split_keep),
        )


def _number(text: str, name: str, settings: Settings) -> int:
    saved: int = getattr(settings, name)
    low, high = RANGES[name]
    try:
        number = int(text.strip())
    except ValueError:
        return saved
    return number if low <= number <= high else saved
