"""Step 1, Choose: what to convert, where the results go (UX §2, §5; ADR-0027, ADR-0029)."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QLabel, QPushButton, QRadioButton, QVBoxLayout, QWidget

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.models import InputRow, OutputChoice, OutputMode
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside.components.file_list import ListRow
from clearmd.frontend.pyside.components.inputs_card import InputsCard
from clearmd.frontend.pyside.components.output_card import OutputCard
from clearmd.i18n import Catalog


class ChooseView(QWidget):
    """Add files / Add folder and the drop zone, the numbered list, the output choice."""

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
        super().__init__()
        self._texts: list[tuple[QLabel | QPushButton | QRadioButton, str]] = []
        self._short = self._split = False
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(GAP)
        inputs = InputsCard(
            self.layout_,
            text=self._text,
            on_add_files=on_add_files,
            on_add_folder=on_add_folder,
            on_remove=on_remove,
            on_clear=on_clear,
        )
        self._inputs_card = inputs
        self.add_files = inputs.add_files
        self.add_folder = inputs.add_folder
        self.drop_zone = inputs.drop_zone
        self.inputs = inputs.inputs
        self.remove = inputs.remove
        self.clear = inputs.clear
        self.deselect = inputs.deselect
        self.layout_.setSpacing(SPACE)

        output = OutputCard(
            self,
            self.layout_,
            text=self._text,
            on_next_to=on_next_to,
            on_pick_folder=on_pick_folder,
            on_summary=on_summary,
            on_images=on_images,
            on_split=on_split,
        )
        self._output_card = output
        self.split = output.split
        self.merge = output.merge
        self.next_to = output.next_to
        self.in_folder = output.in_folder
        self.pick = output.pick
        self.output_label = output.output_label
        self.summary_md = output.summary_md
        self.summary_pdf = output.summary_pdf
        self.summary_pdf_only = output.summary_pdf_only
        self.images_omit = output.images_omit
        self.images_folder = output.images_folder
        self.choice_buttons = output.choice_buttons

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self.inputs.show_rows(
            [
                ListRow(row.icon, f"{row.name}/" if row.is_folder else row.name, (row.location,),
                        payload=row.path)
                for row in rows
            ]
        )  # fmt: skip

    def show_output_choice(self, choice: OutputChoice) -> None:
        (self.next_to if choice.mode is OutputMode.NEXT_TO else self.in_folder).setChecked(True)
        self.output_label.setText(choice.label)
        radios = {"markdown_pdf": self.summary_pdf, "pdf": self.summary_pdf_only}
        radios.get(choice.summary_format, self.summary_md).setChecked(True)
        (self.images_omit if choice.images == "omit" else self.images_folder).setChecked(True)
        self._output_card.show_tool(choice)
        self._split = choice.tool is not Tool.CONVERT  # Split's or Merge's block
        self._fit()

    def output_mode(self) -> str:
        return OutputMode.FOLDER.value if self.in_folder.isChecked() else OutputMode.NEXT_TO.value

    def set_short(self, short: bool) -> None:
        """A short window: the add buttons side by side, so the list keeps its rows (011)."""
        self._short = short
        self._fit()

    def _fit(self) -> None:
        """Split's and Merge's blocks are taller than the images' choice: with them, the add
        buttons go side by side at any height, so the list keeps a row (024, 026; as ttk)."""
        self._inputs_card.set_short(self._short or self._split)

    def apply_language(self, catalog: Catalog) -> None:
        for widget, key in self._texts:
            widget.setText(catalog.text(key))
        self.drop_zone.show_text(catalog.text("gui.main.drop"))
        self.inputs.apply_headings(
            [catalog.text("gui.main.column_name"), catalog.text("gui.main.column_location")],
            catalog.text("gui.main.empty"),
        )

    def apply_palette(self, palette: Palette) -> None:
        self.inputs.apply_palette(palette)

    def _text(self, widget: QLabel | QPushButton | QRadioButton, key: str) -> None:
        self._texts.append((widget, key))
