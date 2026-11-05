"""The four steps' pages (ADR-0027, ADR-0029): Choose, Review, Convert, Results. Each lays out
what the presenter gives it and forwards the user's choices; the actions are in the window's bar."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.models import (
    InputRow,
    OutputChoice,
    OutputMode,
    PlanView,
    ProgressView,
    ResultView,
    RowKind,
)
from clearmd.frontend.pyside.layout.units import ICON
from clearmd.frontend.pyside.visuals.images import icon
from clearmd.frontend.pyside.widgets import (
    DropZone,
    FileList,
    ListRow,
    Stats,
    button,
    card,
    label,
    restyle,
)
from clearmd.i18n import Catalog

_ATTENTION = frozenset({RowKind.SKIPPED, RowKind.MISSING})


class _Page(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._texts: list[tuple[QLabel | QPushButton | QRadioButton, str]] = []
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(GAP)

    def _text(self, widget: QLabel | QPushButton | QRadioButton, key: str) -> None:
        self._texts.append((widget, key))

    def apply_language(self, catalog: Catalog) -> None:
        for widget, key in self._texts:
            widget.setText(catalog.text(key))

    def apply_palette(self, palette: Palette) -> None:
        """What the style sheet cannot draw (the lists' warning rows)."""


def _radio(group: QButtonGroup, on_click: Callable[[], None] | None = None) -> QRadioButton:
    radio = QRadioButton()
    group.addButton(radio)
    if on_click is not None:
        radio.clicked.connect(lambda _checked=False: on_click())
    return radio


# --- Step 1: Choose --------------------------------------------------------------------------


class ChoosePage(_Page):
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
    ) -> None:
        super().__init__()
        self._on_remove = on_remove
        entry = QHBoxLayout()
        entry.setSpacing(GAP)
        self._buttons = QVBoxLayout()
        self._buttons.setSpacing(SPACE)
        self.add_files = button("", on_add_files)
        self.add_folder = button("", on_add_folder)
        self._text(self.add_files, "gui.main.add_files")
        self._text(self.add_folder, "gui.main.add_folder")
        self._buttons.addWidget(self.add_files)
        self._buttons.addWidget(self.add_folder)
        entry.addLayout(self._buttons)
        self.drop_zone = DropZone(on_click=on_add_files)
        entry.addWidget(self.drop_zone, 1)
        self.layout_.addLayout(entry)
        self._short = False

        self.inputs = FileList(1, checks=True, widths=(320,))
        self.inputs.tree.setAccessibleName("inputs")
        self.layout_.addWidget(self.inputs, 1)

        editing = QHBoxLayout()
        editing.setSpacing(SPACE)
        self.remove = button("link", self._remove_selected)
        self.clear = button("link", on_clear)
        self.deselect = button("link", self.inputs.clear_selection)
        for widget, key in (
            (self.remove, "gui.main.remove"),
            (self.clear, "gui.main.clear"),
            (self.deselect, "gui.main.deselect"),
        ):
            self._text(widget, key)
            editing.addWidget(widget)
        editing.addStretch(1)
        self.layout_.addLayout(editing)
        self.layout_.setSpacing(SPACE)

        output, output_layout = card()
        heading = QHBoxLayout()
        title = label("strong")
        self._text(title, "gui.main.output_title")
        heading.addWidget(title)
        heading.addStretch(1)
        images_title = label("strong")
        self._text(images_title, "gui.main.images_title")
        heading.addWidget(images_title)
        self._images = QButtonGroup(self)
        self.images_omit = _radio(self._images, lambda: on_images("omit"))
        self.images_folder = _radio(self._images, lambda: on_images("folder"))
        self._text(self.images_omit, "gui.main.images_omit")
        self._text(self.images_folder, "gui.main.images_folder")
        heading.addSpacing(SPACE)
        heading.addWidget(self.images_omit)
        heading.addSpacing(SPACE)
        heading.addWidget(self.images_folder)
        output_layout.addLayout(heading)

        choices = QHBoxLayout()
        self._mode = QButtonGroup(self)
        self.next_to = _radio(self._mode, on_next_to)
        self.in_folder = _radio(self._mode, on_pick_folder)
        self._text(self.next_to, "gui.output.next_to")
        self._text(self.in_folder, "gui.main.in_folder")
        self.pick = button("", on_pick_folder)
        self._text(self.pick, "gui.main.pick_folder")
        choices.addWidget(self.next_to)
        choices.addSpacing(GAP)
        choices.addWidget(self.in_folder)
        choices.addSpacing(SPACE)
        choices.addWidget(self.pick)
        choices.addStretch(1)
        output_layout.addLayout(choices)
        self.output_label = label("muted", wrap=True)
        output_layout.addWidget(self.output_label)

        summary = QHBoxLayout()
        summary_title = label("strong")
        self._text(summary_title, "gui.main.summary_title")
        summary.addWidget(summary_title)
        self._summary = QButtonGroup(self)
        self.summary_md = _radio(self._summary, lambda: on_summary("markdown"))
        self.summary_pdf = _radio(self._summary, lambda: on_summary("markdown_pdf"))
        self._text(self.summary_md, "gui.main.summary_md")
        self._text(self.summary_pdf, "gui.main.summary_pdf")
        for radio in (self.summary_md, self.summary_pdf):
            summary.addSpacing(GAP)
            summary.addWidget(radio)
        summary.addStretch(1)
        output_layout.addLayout(summary)
        self.layout_.addWidget(output)
        self.choice_buttons = (
            self.next_to,
            self.in_folder,
            self.pick,
            self.summary_md,
            self.summary_pdf,
            self.images_omit,
            self.images_folder,
        )

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
        md = choice.summary_format == "markdown"
        (self.summary_md if md else self.summary_pdf).setChecked(True)
        (self.images_omit if choice.images == "omit" else self.images_folder).setChecked(True)

    def output_mode(self) -> str:
        return OutputMode.FOLDER.value if self.in_folder.isChecked() else OutputMode.NEXT_TO.value

    def set_short(self, short: bool) -> None:
        """A short window: the add buttons side by side, so the list keeps its rows (011)."""
        if short == self._short:
            return
        self._short = short
        self._buttons.setDirection(
            QVBoxLayout.Direction.LeftToRight if short else QVBoxLayout.Direction.TopToBottom
        )

    def apply_language(self, catalog: Catalog) -> None:
        super().apply_language(catalog)
        self.drop_zone.show_text(catalog.text("gui.main.drop"))
        self.inputs.apply_headings(
            [catalog.text("gui.main.column_name"), catalog.text("gui.main.column_location")],
            catalog.text("gui.main.empty"),
        )

    def apply_palette(self, palette: Palette) -> None:
        self.inputs.apply_palette(palette)

    def _remove_selected(self) -> None:
        chosen = self.inputs.selected()
        if chosen:
            self._on_remove(chosen)


# --- Step 2: Review --------------------------------------------------------------------------


class ReviewPage(_Page):
    """The figures, the list (what will not be converted first, in the warning colour, with what
    to do), and the question about existing results when the setting is "ask"."""

    def __init__(self) -> None:
        super().__init__()
        self._catalog: Catalog | None = None
        self._asks = False
        self._plan_id = -1
        self.stats = Stats()
        self.layout_.addWidget(self.stats)
        self.files = FileList(2, widths=(240, 220))
        self.layout_.addWidget(self.files, 1)
        self.existing, existing_layout = card()
        question = label("strong")
        self._text(question, "gui.plan.existing_question")
        existing_layout.addWidget(question)
        answers = QHBoxLayout()
        self._answers = QButtonGroup(self)
        self.keep = _radio(self._answers)
        self.overwrite = _radio(self._answers)
        self._text(self.keep, "gui.plan.keep")
        self._text(self.overwrite, "gui.plan.overwrite")
        answers.addWidget(self.keep)
        answers.addSpacing(GAP)
        answers.addWidget(self.overwrite)
        answers.addStretch(1)
        existing_layout.addLayout(answers)
        self.keep.setChecked(True)
        self.layout_.addWidget(self.existing)
        self.existing.hide()

    def show(self, plan: PlanView) -> None:  # type: ignore[override]  # the presenter's, not QWidget's
        self.stats.show_stats(plan.stats)
        rows = sorted(plan.rows, key=lambda row: row.kind not in _ATTENTION)
        self.files.show_rows(
            [
                ListRow(row.icon, row.name, (row.location, row.detail),
                        warning=row.kind in _ATTENTION)
                for row in rows
            ]
        )  # fmt: skip
        if plan.plan_id != self._plan_id:  # another plan: the answer starts over
            self.keep.setChecked(True)
        self._plan_id = plan.plan_id
        self._asks = plan.asks_about_existing
        self.existing.setVisible(self._asks)

    def forget(self) -> None:
        self._wait()
        self.files.show_rows([])
        self.existing.hide()
        self._asks = False
        self._plan_id = -1

    def overwrite_answer(self) -> bool | None:
        return self.overwrite.isChecked() if self._asks else None

    def _wait(self) -> None:
        names = ("gui.plan.stat_convert", "gui.plan.stat_skipped", "gui.plan.stat_existing")
        catalog = self._catalog
        self.stats.waiting([catalog.text(name) for name in names] if catalog else [])

    def apply_language(self, catalog: Catalog) -> None:
        super().apply_language(catalog)
        self._catalog = catalog
        if self.stats.dimmed or not self.stats.figures():
            self._wait()
        self.files.apply_headings(
            [
                catalog.text("gui.main.column_name"),
                catalog.text("gui.main.column_location"),
                catalog.text("gui.plan.column_what"),
            ],
            catalog.text("gui.plan.nothing"),
        )

    def apply_palette(self, palette: Palette) -> None:
        self.files.apply_palette(palette)


# --- Step 3: Convert -------------------------------------------------------------------------


class ConvertPage(_Page):
    """Before the batch, a card says what is ready and where it goes; then "3 of 37", the
    current file with its icon, the bar, the time left, and for a long file its timer."""

    def __init__(self) -> None:
        super().__init__()
        self._catalog: Catalog | None = None
        self.ready, ready_layout = card(padding=3 * SPACE)
        self.ready_count = label("bigText")
        self.ready_where = label("muted", wrap=True)
        ready_layout.addWidget(self.ready_count)
        ready_layout.addWidget(self.ready_where)
        self.layout_.addWidget(self.ready)
        self.progress_card, progress = card(padding=3 * SPACE)
        self.counter = label("bigText")
        progress.addWidget(self.counter)
        progress.addSpacing(SPACE)
        now = label("muted")
        self._text(now, "gui.progress.current")
        progress.addWidget(now)
        current = QHBoxLayout()
        current.setSpacing(SPACE)
        self.file_icon = QLabel()
        self.file = label("strong")
        current.addWidget(self.file_icon)
        current.addWidget(self.file, 1)
        progress.addLayout(current)
        progress.addSpacing(SPACE)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        progress.addWidget(self.bar)
        self.time_left = label("muted")
        self.long_file = label("muted", wrap=True)
        progress.addWidget(self.time_left)
        progress.addWidget(self.long_file)
        self.layout_.addWidget(self.progress_card)
        self.progress_card.hide()
        self.layout_.addStretch(1)
        self.dimmed = False
        self._fade(True)

    def show_ready(self, count: str, where: str) -> None:
        self.progress_card.hide()
        self._fade(False)
        self.ready_count.setText(count)
        self.ready_where.setText(where)
        self.ready.show()

    def forget(self, where: str = "") -> None:
        self.progress_card.hide()
        self._fade(True)
        catalog = self._catalog
        self.ready_count.setText(catalog.text("gui.convert.ready", count="—") if catalog else "—")
        self.ready_where.setText(where)
        self.ready.show()

    def clear(self) -> None:
        """The batch starts: the progress replaces the ready card."""
        self.ready.hide()
        self.progress_card.show()
        for widget in (self.counter, self.file, self.time_left, self.long_file):
            widget.setText("")
        self.file_icon.clear()
        self.bar.setValue(0)

    def show(self, progress: ProgressView) -> None:  # type: ignore[override]  # the presenter's
        self.counter.setText(progress.counter)
        self.file_icon.setPixmap(icon(progress.icon).pixmap(ICON, ICON))
        self.file.setText(progress.name)
        self.bar.setValue(round(progress.fraction * 1000))
        self.time_left.setText(progress.time_left or "")
        if progress.elapsed and self._catalog is not None:
            elapsed = self._catalog.text("gui.progress.elapsed", clock=progress.elapsed)
            self.long_file.setText(f"{elapsed} · {progress.long_file or ''}".strip(" ·"))
        else:
            self.long_file.setText("")

    def _fade(self, dimmed: bool) -> None:
        self.dimmed = dimmed
        restyle(self.ready, "dim", "true" if dimmed else "false")

    def apply_language(self, catalog: Catalog) -> None:
        super().apply_language(catalog)
        self._catalog = catalog
        if self.dimmed:
            self.ready_count.setText(catalog.text("gui.convert.ready", count="—"))


# --- Step 4: Results -------------------------------------------------------------------------


class ResultsPage(_Page):
    """The figures; then "every file was converted", or what needs attention with the selected
    problem in full below the list."""

    def __init__(self) -> None:
        super().__init__()
        self._catalog: Catalog | None = None
        self.stats = Stats()
        self.layout_.addWidget(self.stats)
        self.all_good, good_layout = card(padding=3 * SPACE)
        message = label("strong", wrap=True)
        self._text(message, "gui.result.all_good")
        good_layout.addWidget(message)
        self.layout_.addWidget(self.all_good)
        self.problems_title = label("strong")
        self._text(self.problems_title, "gui.result.problems")
        self.layout_.addWidget(self.problems_title)
        self.problems = FileList(1, widths=(240,))
        self.layout_.addWidget(self.problems, 1)
        self.detail = label("onPage", wrap=True)
        self.layout_.addWidget(self.detail)
        self.problems.selection_changed.connect(self._show_detail)
        self._filler = QWidget()
        self.layout_.addWidget(self._filler, 1)
        self._showing(None)

    def show(self, result: ResultView) -> None:  # type: ignore[override]  # the presenter's
        current = self.problems.current()
        rows = self.problems.rows()
        selected = rows.index(current) if current in rows else 0
        keep = len(rows) == len(result.rows)  # the same result again (settings)
        self.stats.show_stats(result.stats)
        if result.rows:
            self.problems.show_rows(
                [ListRow(row.icon, row.name, (row.detail,), warning=True) for row in result.rows]
            )
            self._showing(True)
            self.problems.select(selected if keep and selected < len(result.rows) else 0)
            self._show_detail()
        else:
            self._showing(False)

    def forget(self) -> None:
        self._wait()
        self.problems.show_rows([])
        self._showing(None)

    def _showing(self, problems: bool | None) -> None:
        """``None``: nothing yet; ``False``: all good; ``True``: the problems."""
        self.all_good.setVisible(problems is False)
        for widget in (self.problems_title, self.problems, self.detail):
            widget.setVisible(problems is True)
        self._filler.setVisible(problems is not True)

    def _show_detail(self) -> None:
        row = self.problems.current()
        self.detail.setText(f"{row.name}: {row.values[0]}" if row else "")

    def _wait(self) -> None:
        names = ("gui.result.stat_converted", "gui.result.stat_skipped", "gui.result.stat_failed")
        catalog = self._catalog
        self.stats.waiting([catalog.text(name) for name in names] if catalog else [])

    def apply_language(self, catalog: Catalog) -> None:
        super().apply_language(catalog)
        self._catalog = catalog
        if self.stats.dimmed or not self.stats.figures():
            self._wait()
        self.problems.apply_headings(
            [catalog.text("gui.main.column_name"), catalog.text("gui.result.column_what")], ""
        )

    def apply_palette(self, palette: Palette) -> None:
        self.problems.apply_palette(palette)
