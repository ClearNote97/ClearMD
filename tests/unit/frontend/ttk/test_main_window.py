"""The ttk window and its first step on the presenter (005, T04 and T04b), under a display."""

import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from support.gui_fakes import FakeBackend, MemoryBackend, planned

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.backend.schemas.settings import Settings, SettingsProblem, SettingsWarning
from clearmd.frontend.presenter import Action, AppState
from clearmd.frontend.presenter.state import enabled_actions
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.layout import BODY, on_grid
from clearmd.frontend.ttk.views.dialogs import SettingsDialog, WelcomeDialog


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False, theme="light")))
    window.start()
    pump(window, seconds=0.2)
    yield window
    window.close()


def pump(window: TtkApp, *, until: Any = None, seconds: float = 2.0) -> None:
    """Run the UI loop for a moment (or until ``until()`` holds)."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        window.root.update()
        if until is not None and until():
            return
        time.sleep(0.01)


def widgets(root: Any) -> Iterator[Any]:
    pending = [root]
    while pending:
        widget = pending.pop()
        yield widget
        pending.extend(widget.winfo_children())


def test_the_window_shows_the_first_step_with_convert_disabled(app: TtkApp) -> None:
    assert app.root.title() == "ClearMD"
    assert app.surface.header()["eyebrow"] == "Step 1 of 4"
    assert app.surface.header()["title"] == "Choose what to convert"
    assert app.rail.step_texts() == ["> Choose", "Review", "Convert", "Results"]
    assert app.main.convert.instate(["disabled"])
    assert app.main.remove.instate(["disabled"])


def test_inputs_are_numbered_with_their_icons_and_enable_convert(
    app: TtkApp, tmp_path: Path
) -> None:
    (tmp_path / "a.pdf").write_bytes(b"%PDF")
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path])
    pump(app, seconds=0.2)
    assert app.main.inputs.names() == ["a.pdf", f"{tmp_path.name}/"]
    tree = app.main.inputs.tree
    assert all(tree.item(item, "image") for item in tree.get_children())
    assert not app.main.inputs.empty.winfo_ismapped()
    assert app.main.convert.instate(["!disabled"])


def test_removing_the_selection_and_clearing(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[0])
    app.main.remove.invoke()
    assert app.main.inputs.names() == ["b.pdf"]
    app.main.clear.invoke()
    assert app.main.inputs.names() == []


def test_dropped_files_and_folders_are_added(app: TtkApp, tmp_path: Path) -> None:
    data = app.root.tk.call("list", str(tmp_path / "a b.pdf"), str(tmp_path))  # a space in a name
    app._dropped(SimpleNamespace(data=data))
    shown = app.main.inputs.names()
    assert shown[0] == "a b.pdf" and len(shown) == 2


def test_enter_triggers_convert_and_the_rail_moves_to_review(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    app.root.event_generate("<Return>", when="tail")
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert app.presenter.state is AppState.WAITING_DECISION
    assert app.last_plan is not None
    assert app.rail.step_texts()[1] == "> Review"
    assert app.surface.header()["eyebrow"] == "Step 2 of 4 · Waiting for your decision"


def test_both_clearmd_themes_apply(app: TtkApp) -> None:
    app.apply_theme("dark")
    assert app.style.theme_use() == "clearmd-dark"
    assert app.rail.cget("background") == app.palette.ground == "#18212A"
    app.apply_theme("light")
    assert app.style.theme_use() == "clearmd-light"


def test_the_language_changes_every_label(app: TtkApp) -> None:
    app.presenter.save_settings(Settings(language="es", show_welcome=False))
    pump(app, seconds=0.1)
    assert app.main.convert.cget("text") == "Convertir"
    assert app.main.add_folder.cget("text") == "Agregar carpeta"
    assert app.rail.step_texts()[0] == "> Elegir"
    assert app.surface.header()["eyebrow"] == "Paso 1 de 4"
    assert app.main.drop_zone.text() == "o suelta aquí archivos y carpetas"


def test_the_window_icon_is_the_app_icon_at_every_size(app: TtkApp) -> None:
    assert [icon.width() for icon in app._icons] == [16, 32, 48, 64, 128, 256]


def test_every_gap_is_on_the_8_px_grid_and_text_is_at_least_14_px(app: TtkApp) -> None:
    off_grid = []
    for widget in widgets(app.root):
        manager = widget.winfo_manager()
        if manager not in {"pack", "grid"}:
            continue
        info = widget.pack_info() if manager == "pack" else widget.grid_info()
        for option in ("padx", "pady", "ipadx", "ipady"):
            value = info.get(option, 0)
            for part in value if isinstance(value, tuple) else str(value).split():
                if not on_grid(int(float(part))):
                    off_grid.append((str(widget), option, part))
    assert off_grid == []
    for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont"):
        assert tkfont.nametofont(name, root=app.root).cget("size") <= BODY  # pixels: negative
    assert all(font.cget("size") <= BODY for font in app.fonts.values())


# --- Review, convert, results (T05) --------------------------------------------------------------


def test_review_shows_the_figures_and_each_file_then_converting_ends_in_results(
    display: str, tmp_path: Path
) -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.docx", exists=True)),
        (SkippedItem(Path("/docs/notes.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    fake = FakeBackend(plan=plan, settings=Settings(show_welcome=False, theme="light"))
    app = TtkApp(fake)
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.main.convert.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        assert shown(app) is app.review
        assert app.review.stats.figures() == [
            ("To convert", "2"),
            ("Skipped", "1"),
            ("Already exist", "1"),
        ]
        assert app.review.files.names() == ["notes.md", "a.pdf", "b.docx"]  # attention first
        assert app.review.existing.winfo_ismapped()  # the setting is "ask"
        app.review.decision.set("overwrite")
        app.review.confirm.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.FINISHED)
        assert fake.run_calls[-1]["overwrite"](plan.conversions[1]) is True
        assert shown(app) is app.results
        assert app.rail.step_texts()[3] == "> Results"
        assert ("Converted", "2") in app.results.stats.figures()
        assert app.results.problems.names() == ["notes.md"]  # skipped: said why, with what to do
        assert fake.opened  # the folder opens by itself (open_output_when_done)
        app.results.again.invoke()
        assert shown(app) is app.main and app.main.inputs.names() == [f"{tmp_path.name}/"]
    finally:
        app.close()


def test_progress_shows_the_file_and_cancel_stops(display: str, tmp_path: Path) -> None:
    gate = threading.Event()
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(plan=plan, settings=Settings(show_welcome=False))

    def hold() -> None:  # the first file is converting until the test lets it go
        gate.wait(5)

    fake.before_finish = hold
    app = TtkApp(fake)
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.main.convert.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        app.review.confirm.invoke()
        pump(app, until=lambda: app.converting.counter.cget("text") == "1 of 2")
        assert shown(app) is app.converting
        assert app.converting.file.cget("text").strip() == "a.pdf"
        assert app.converting.cancel.instate(["!disabled"])
        app.converting.cancel.invoke()
        gate.set()
        pump(app, until=lambda: app.presenter.state is AppState.CANCELLED)
        assert app.presenter.state is AppState.CANCELLED and shown(app) is app.results
    finally:
        gate.set()
        app.close()


def test_a_clean_batch_says_every_file_was_converted(display: str, tmp_path: Path) -> None:
    app = TtkApp(FakeBackend(settings=Settings(show_welcome=False)))
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.main.convert.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        app.root.event_generate("<Return>", when="tail")  # Enter confirms on the review
        pump(app, until=lambda: app.presenter.state is AppState.FINISHED)
        pump(app, seconds=0.1)
        assert app.results.all_good.winfo_ismapped()
        assert not app.results.problems.winfo_ismapped()
    finally:
        app.close()


def shown(app: TtkApp) -> object:
    """The page on screen (typed loosely: tests compare it with several views)."""
    return app.page


def test_problems_are_listed_in_the_results(display: str, tmp_path: Path) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(
        plan=plan,
        statuses={"a.pdf": OutcomeStatus.FAILED},
        settings=Settings(show_welcome=False, open_output_when_done=False),
    )
    app = TtkApp(fake)
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.main.convert.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        app.review.confirm.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.FINISHED_WITH_PROBLEMS)
        assert app.results.problems.names() == ["a.pdf"]
        assert app.results.detail.cget("text") == (
            "a.pdf: This file is password-protected. Remove the password and try again."
        )
        assert not app.results.all_good.winfo_ismapped()
        app.results.open.invoke()
        assert fake.opened
    finally:
        app.close()


# --- Help, welcome, settings (T06) ---------------------------------------------------------------


def test_help_opens_from_the_rail_and_esc_closes_it(app: TtkApp) -> None:
    app.rail.help.invoke()
    pump(app, seconds=0.2)
    assert app.dialog is not None
    assert app.dialog.title() == "How to use ClearMD"
    texts = [child.cget("text") for child in app.dialog.body.winfo_children()]
    assert "Your privacy" in texts and "What it converts" in texts
    app.dialog.focus_force()
    pump(app, seconds=0.1)
    app.dialog.event_generate("<Escape>", when="tail")
    pump(app, until=lambda: app.dialog is None, seconds=1.0)
    assert app.dialog is None


def test_the_welcome_appears_once_and_can_be_dismissed_for_good(display: str) -> None:
    fake = FakeBackend(settings=Settings(show_welcome=True))
    app = TtkApp(fake)
    try:
        app.start()
        pump(app, until=lambda: app.dialog is not None)
        assert isinstance(app.dialog, WelcomeDialog)
        app.dialog.dont_show.set(True)
        app.dialog.close()
        assert app.dialog is None
        assert fake.saved[-1].show_welcome is False
    finally:
        app.close()


def test_settings_save_applies_the_language_and_theme(app: TtkApp) -> None:
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    dialog = app.dialog
    assert isinstance(dialog, SettingsDialog)
    assert set(dialog.values) == {
        "language", "theme", "open_output_when_done", "on_existing_output", "recursive",
        "html_strategy", "show_welcome",
    }  # fmt: skip
    dialog.values["language"].set("Español")
    dialog.values["theme"].set("Dark")
    dialog.values["recursive"].set(False)
    dialog.save()
    pump(app, seconds=0.2)
    assert app.dialog is None
    assert app.presenter.settings.language == "es" and not app.presenter.settings.recursive
    assert app.style.theme_use() == "clearmd-dark"
    assert app.main.convert.cget("text") == "Convertir"


def test_restore_defaults_resets_the_controls_until_saved(app: TtkApp) -> None:
    app.presenter.save_settings(Settings(language="es", show_welcome=False, recursive=False))
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    dialog = app.dialog
    assert isinstance(dialog, SettingsDialog)
    dialog.restore()
    assert dialog.chosen() == Settings()
    dialog.close()
    assert app.presenter.settings.language == "es"  # nothing saved without Save


# --- A real batch through the window (AC-20) -----------------------------------------------------

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "documents"


def test_a_real_batch_through_the_window_writes_the_markdown(display: str, tmp_path: Path) -> None:
    folder = tmp_path / "Documentos"
    folder.mkdir()
    for name in ("sample.docx", "sample.csv", "sample.txt", "encrypted.pdf"):
        (folder / name).write_bytes((FIXTURES / name).read_bytes())
    (folder / "notas.md").write_text("# ya es Markdown\n", encoding="utf-8")
    backend = MemoryBackend(Settings(show_welcome=False))
    app = TtkApp(backend)
    try:
        app.start()
        app.presenter.add_paths([folder])
        app.main.convert.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)
        assert app.review.stats.figures()[:2] == [("To convert", "4"), ("Skipped", "1")]
        app.review.confirm.invoke()
        finished = {AppState.FINISHED, AppState.FINISHED_WITH_PROBLEMS}
        pump(app, until=lambda: app.presenter.state in finished, seconds=120)
        assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS  # the encrypted PDF
        assert app.last_result is not None
        (output,) = app.last_result.folders  # ClearMD_Output, next to the chosen folder
        assert output == tmp_path / "ClearMD_Output"
        assert len(list(output.rglob("*.md"))) == 4  # three documents and the summary
        assert set(app.results.problems.names()) == {"encrypted.pdf", "notas.md"}
        assert backend.opened == [output]
    finally:
        app.close()


# --- Keyboard and look (T07; AC-17 – AC-19, AC-22) -----------------------------------------------


def focus_chain(app: TtkApp, start: Any, steps: int = 40) -> list[Any]:
    chain, widget = [], start
    for _ in range(steps):
        chain.append(widget)
        widget = widget.tk_focusNext()
        if widget is None or widget is start:
            break
    return chain


def test_tab_goes_through_the_first_step_in_reading_order(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    pump(app, seconds=0.1)
    main = app.main
    chain = focus_chain(app, main.add_files)
    expected = [
        main.add_files, main.add_folder, main.inputs.tree, main.remove, main.clear,
        main.next_to, main.in_folder, main.pick, main.convert,
    ]  # fmt: skip
    positions = [chain.index(widget) for widget in expected]
    assert positions == sorted(positions)
    assert app.rail.settings in chain and app.rail.help in chain  # the rail is reachable too


def test_enter_saves_the_settings_and_esc_cancels_them(app: TtkApp) -> None:
    app.rail.settings.invoke()
    pump(app, seconds=0.1)
    dialog = app.dialog
    assert isinstance(dialog, SettingsDialog)
    dialog.values["recursive"].set(False)
    dialog.focus_force()
    pump(app, seconds=0.1)
    dialog.event_generate("<Escape>", when="tail")
    pump(app, until=lambda: app.dialog is None, seconds=1.0)
    assert app.presenter.settings.recursive  # Esc: nothing saved
    app.rail.settings.invoke()
    pump(app, seconds=0.1)
    dialog = app.dialog
    assert isinstance(dialog, SettingsDialog)
    dialog.values["recursive"].set(False)
    dialog.focus_force()
    pump(app, seconds=0.1)
    dialog.event_generate("<Return>", when="tail")
    pump(app, until=lambda: app.dialog is None, seconds=1.0)
    assert not app.presenter.settings.recursive  # Enter: saved


def test_settings_and_help_are_never_disabled_together_with_help(app: TtkApp) -> None:
    for state in AppState:
        enabled = enabled_actions(state, has_inputs=True, can_confirm=True, has_results=True)
        assert Action.HELP in enabled  # "?" always works (UX §4)


# --- Review of 005 (code review C-*) -------------------------------------------------------------


def run_until_closed(app: TtkApp, seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            app.root.update()
            if not app.root.winfo_exists():
                return True
        except tk.TclError:
            return True  # destroyed
        time.sleep(0.01)
    return False


def test_c1_closing_while_converting_waits_for_the_summary(display: str, tmp_path: Path) -> None:
    marker = tmp_path / "Resumen_ClearMD.md"

    class Slow(FakeBackend):
        def run_batch(self, plan: BatchPlan, **kwargs: Any) -> Any:
            kwargs["cancel"]._event.wait(5)  # converting until cancelled
            time.sleep(0.3)  # the current file stops, then the summary is written
            marker.write_text("summary", encoding="utf-8")
            return super().run_batch(plan, **kwargs)

    app = TtkApp(Slow(settings=Settings(show_welcome=False)))
    app.start()
    app.presenter.add_paths([tmp_path])
    app.main.convert.invoke()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    app.review.confirm.invoke()
    pump(app, until=lambda: app.presenter.state is AppState.CONVERTING)
    app.close()
    assert run_until_closed(app)
    assert marker.is_file()


def test_c2_an_unexpected_error_stays_on_screen(display: str, tmp_path: Path) -> None:
    app = TtkApp(FakeBackend(settings=Settings(show_welcome=False), plan_error=RuntimeError("x")))
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.main.convert.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.READY and app.last_plan is None)
        pump(app, seconds=0.2)
        assert "Something unexpected went wrong" in app.message.cget("text")
    finally:
        app.close()


def test_c3_settings_warnings_at_start_are_on_screen(display: str) -> None:
    warnings = (SettingsWarning("colour", SettingsProblem.UNKNOWN_KEY),)
    app = TtkApp(FakeBackend(settings=Settings(show_welcome=False), warnings=warnings))
    try:
        app.start()
        pump(app, seconds=0.2)
        assert "colour" in app.message.cget("text")
        assert int(app.message.cget("wraplength")) > 0  # C-12: long messages wrap
    finally:
        app.close()


def test_c5_a_theme_change_keeps_the_selected_row(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[1])
    app.apply_theme("dark")
    assert [tree.index(item) for item in tree.selection()] == [1]


def test_c9_closing_with_the_welcome_open_keeps_its_answer(display: str) -> None:
    fake = FakeBackend(settings=Settings(show_welcome=True))
    app = TtkApp(fake)
    app.start()
    pump(app, until=lambda: app.dialog is not None)
    assert isinstance(app.dialog, WelcomeDialog)
    app.dialog.dont_show.set(True)
    app.close()
    assert fake.saved[-1].show_welcome is False


def test_a3_a_settings_save_keeps_the_selected_problem(display: str, tmp_path: Path) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    statuses = {"a.pdf": OutcomeStatus.FAILED, "b.pdf": OutcomeStatus.FAILED}
    app = TtkApp(FakeBackend(plan=plan, statuses=statuses, settings=Settings(show_welcome=False)))
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.main.convert.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        app.review.confirm.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.FINISHED_WITH_PROBLEMS)
        tree = app.results.problems.tree
        tree.selection_set(tree.get_children()[1])
        pump(app, seconds=0.1)
        app.presenter.save_settings(replace_settings(app.presenter.settings, recursive=False))
        pump(app, seconds=0.1)
        assert [tree.index(item) for item in tree.selection()] == [1]
        assert app.results.detail.cget("text").startswith("b.pdf")
    finally:
        app.close()


def test_a4_a_plan_shown_again_keeps_the_answer_about_existing_results(
    display: str, tmp_path: Path
) -> None:
    plan = BatchPlan((planned("a.pdf", exists=True),), (), ())
    app = TtkApp(FakeBackend(plan=plan, settings=Settings(show_welcome=False)))
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.main.convert.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        app.review.decision.set("overwrite")
        assert app.last_plan is not None
        app.show_plan(app.last_plan)  # the same plan again (a language change)
        assert app.review.decision.get() == "overwrite"
    finally:
        app.close()


def replace_settings(settings: Settings, **changes: Any) -> Settings:
    from dataclasses import replace

    return replace(settings, **changes)
