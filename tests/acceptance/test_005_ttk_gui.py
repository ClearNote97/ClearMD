"""Feature 005 — one test per acceptance criterion (spec/features/005_*/spec.md).

The window runs under a display (a virtual one when there is none). Most criteria drive it with a
fake backend, so the flow is quick and exact; AC-07, AC-15 and AC-20 use the real backend.
"""

import ast
import shutil
import sys
import threading
import time
import tomllib
from collections.abc import Callable, Iterator
from pathlib import Path
from tkinter import filedialog
from types import SimpleNamespace
from typing import Any

import pytest
from support import DOCUMENTS_DIR
from support.gui_fakes import FakeBackend, MemoryBackend, planned

import clearmd.frontend.presenter.presenter as presenter_module
from clearmd.backend.api import load_settings, settings_path
from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.cli import main as cli_main
from clearmd.frontend.presenter import Action, AppState
from clearmd.frontend.presenter.icons import ICONS
from clearmd.frontend.presenter.models import ProgressView, StateView
from clearmd.frontend.presenter.ports import ApiBackend
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.brand import PRIMARY
from clearmd.frontend.ttk.layout import BODY, on_grid
from clearmd.frontend.ttk.views.dialogs import SettingsDialog, WelcomeDialog
from clearmd.i18n import load_catalog

ROOT = Path(__file__).resolve().parents[2]
QUIET = Settings(show_welcome=False, open_output_when_done=False)


@pytest.fixture
def window(display: str) -> Iterator[Callable[..., TtkApp]]:
    opened: list[TtkApp] = []

    def make(backend: Any) -> TtkApp:
        app = TtkApp(backend)
        app.start()
        pump(app, seconds=0.1)
        opened.append(app)
        return app

    yield make
    for app in opened:
        try:
            app.close()
        except Exception:  # noqa: BLE001 -- already closed by the test
            pass


def pump(app: TtkApp, *, until: Callable[[], bool] | None = None, seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.root.update()
        if until is not None and until():
            return
        time.sleep(0.01)


def press_enter(app: TtkApp) -> None:
    """Enter on the window: it needs the keyboard focus first (Windows gives it only on demand)."""
    app.root.focus_force()
    app.root.update()
    app.root.event_generate("<Return>", when="tail")


def to_review(app: TtkApp, *paths: Path) -> None:
    app.presenter.add_paths(list(paths))
    app.main.convert.invoke()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=60)


def converted(app: TtkApp) -> bool:
    return app.presenter.state in {
        AppState.FINISHED,
        AppState.FINISHED_WITH_PROBLEMS,
        AppState.CANCELLED,
    }


def copy_documents(folder: Path, *names: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copyfile(DOCUMENTS_DIR / name, folder / name)
    return folder


def widgets(root: Any) -> Iterator[Any]:
    pending = [root]
    while pending:
        widget = pending.pop()
        yield widget
        pending.extend(widget.winfo_children())


# --- The presenter ---------------------------------------------------------------------------


def test_ac_01_one_state_at_a_time_and_each_enables_its_actions(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    app = window(FakeBackend(settings=QUIET))
    seen: list[tuple[AppState, frozenset[Action]]] = []
    real = app.show_state

    def recorded(state: StateView) -> None:
        seen.append((state.state, state.enabled))
        real(state)

    app.show_state = recorded  # type: ignore[method-assign]
    assert Action.CONVERT not in (app.state.enabled if app.state else frozenset())
    to_review(app, tmp_path)
    app.review.confirm.invoke()
    pump(app, until=lambda: converted(app))
    states = [state for state, _ in seen]
    assert states[:3] == [AppState.READY, AppState.ANALYZING, AppState.WAITING_DECISION]
    assert AppState.CONVERTING in states and states[-1] is AppState.FINISHED
    for state, enabled in seen:
        working = state in {AppState.ANALYZING, AppState.CONVERTING}
        assert (Action.CANCEL in enabled) is working
        assert Action.CONVERT not in enabled or state is AppState.READY


def test_ac_02_the_work_never_runs_on_the_ui_thread(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    ui = threading.get_ident()
    planned_on: list[int] = []
    fake = FakeBackend(settings=QUIET)
    real_plan = fake.plan_batch

    def slow_plan(inputs: Any, **options: Any) -> BatchPlan:
        planned_on.append(threading.get_ident())
        time.sleep(0.5)  # meanwhile the window must keep handling events
        return real_plan(inputs, **options)

    fake.plan_batch = slow_plan  # type: ignore[method-assign]
    app = window(fake)
    ticks: list[float] = []
    app.presenter.add_paths([tmp_path])
    app.main.convert.invoke()
    for _ in range(10):
        app.root.after(20, lambda: ticks.append(time.monotonic()))
        pump(app, seconds=0.03)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert planned_on and planned_on[0] != ui
    assert len(ticks) >= 5  # the UI loop ran while the plan was being made


def test_ac_03_every_text_comes_from_the_catalogs_in_the_chosen_language(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    plan = BatchPlan(
        (planned("a.pdf"),),
        (SkippedItem(Path("/docs/notas.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    app = window(FakeBackend(plan=plan, settings=replace_settings(QUIET, language="es")))
    es = load_catalog("es")
    assert app.main.convert.cget("text") == es.text("gui.main.convert")
    assert app.surface.header()["title"] == es.text("gui.page.choose_title")
    to_review(app, tmp_path)
    (skipped,) = [row for row in app.last_plan.rows if row.name == "notas.md"]  # type: ignore[union-attr]
    assert skipped.detail.startswith(es.text("skip.already_markdown"))


def test_ac_04_the_presenter_imports_only_the_api_schemas_i18n_and_the_standard_library() -> None:
    allowed = (
        "clearmd.backend.api",
        "clearmd.backend.schemas",
        "clearmd.i18n",
        "clearmd.frontend.presenter",
    )
    for path in (ROOT / "src" / "clearmd" / "frontend" / "presenter").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom) and node.level == 0
                else []
            )
            for name in names:
                top = name.split(".")[0]
                assert top not in {"tkinter", "turtle"}, (path.name, name)
                assert name.startswith(allowed) or top in sys.stdlib_module_names, (path.name, name)


# --- Choosing what to convert ----------------------------------------------------------------


def test_ac_05_add_files_add_folder_drop_remove_and_no_duplicates(
    window: Callable[..., TtkApp], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second = tmp_path / "a.pdf", tmp_path / "b.docx"
    monkeypatch.setattr(filedialog, "askopenfilenames", lambda **_: (str(first), str(second)))
    monkeypatch.setattr(filedialog, "askdirectory", lambda **_: str(tmp_path))
    app = window(FakeBackend(settings=QUIET))
    app.main.add_files.invoke()
    app.main.add_folder.invoke()
    app.main.add_files.invoke()  # the same files again: never listed twice
    data = app.root.tk.call("list", str(tmp_path / "c d.odt"), str(first))
    app._dropped(SimpleNamespace(data=data))
    assert app.main.inputs.names() == ["a.pdf", "b.docx", f"{tmp_path.name}/", "c d.odt"]
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[0])
    app.main.remove.invoke()
    assert app.main.inputs.names()[0] == "b.docx"


def test_ac_06_the_picked_output_folder_is_remembered(
    window: Callable[..., TtkApp], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "Resultados"
    out.mkdir()
    monkeypatch.setattr(filedialog, "askdirectory", lambda **_: str(out))
    backend = MemoryBackend(QUIET)
    app = window(backend)
    assert app.main.output_mode.get() == "next_to"  # the default
    app.main.in_folder.invoke()
    assert app.presenter.output_folder == out
    assert backend.settings.last_output_folder == str(out)
    again = window(backend)
    assert again.presenter.settings.last_output_folder == str(out)  # the suggestion next time


# --- Before converting -----------------------------------------------------------------------


def test_ac_07_convert_first_shows_the_plan_and_writes_nothing(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    folder = copy_documents(tmp_path / "docs", "sample.docx", "sample.csv")
    (folder / "notes.md").write_text("# notes\n", encoding="utf-8")
    app = window(MemoryBackend(QUIET))
    to_review(app, folder)
    assert app.review.stats.figures() == [
        ("To convert", "2"), ("Skipped", "1"), ("Already exist", "0")
    ]  # fmt: skip
    assert app.review.files.names()[0] == "notes.md"  # what will not be converted, first
    assert not (tmp_path / "ClearMD_Output").exists()


@pytest.mark.parametrize(
    ("setting", "asked"), [("ask", True), ("overwrite", False), ("skip", False)]
)
def test_ac_08_existing_outputs_are_asked_about_only_with_ask(
    window: Callable[..., TtkApp], tmp_path: Path, setting: str, asked: bool
) -> None:
    plan = BatchPlan((planned("a.pdf", exists=True),), (), ())
    settings = replace_settings(QUIET, on_existing_output=setting)
    fake = FakeBackend(plan=plan, settings=settings)
    app = window(fake)
    to_review(app, tmp_path)
    assert bool(app.review.existing.winfo_ismapped()) is asked
    if asked:
        app.review.decision.set("overwrite")
    app.review.confirm.invoke()
    pump(app, until=lambda: converted(app))
    assert fake.run_calls[-1]["overwrite"](plan.conversions[0]) is (setting != "skip")


# --- Converting ------------------------------------------------------------------------------


class Held:
    """Holds the batch on its first file until released."""

    def __init__(self) -> None:
        self.gate, self.started = threading.Event(), threading.Event()

    def __call__(self) -> None:
        self.started.set()
        self.gate.wait(10)


def test_ac_09_the_progress_says_where_it_is_and_reassures_on_a_long_file(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    held = Held()
    plan = BatchPlan((planned("Informe.pdf"), planned("b.pdf")), (), ())
    app = window(FakeBackend(plan=plan, settings=QUIET, before_finish=held))
    try:
        to_review(app, tmp_path)
        app.review.confirm.invoke()
        pump(app, until=lambda: app.converting.counter.cget("text") == "1 of 2")
        assert app.converting.file.cget("text").strip() == "Informe.pdf"
        assert app.converting.time_left.cget("text") == "about 2 min left"
        long_file = ProgressView(
            "1 of 2", "Informe.pdf", 0.0, None, "0:25", "Large files can take a few minutes.", "pdf"
        )
        app.show_progress(long_file)  # what the presenter sends after 15 s on one file
        assert app.converting.long_file.cget("text") == (
            "This file: 0:25 · Large files can take a few minutes."
        )
    finally:
        held.gate.set()
    pump(app, until=lambda: converted(app))


def test_ac_10_cancel_is_always_there_and_stops_at_once(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    held = Held()
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(plan=plan, settings=QUIET, before_finish=held)
    app = window(fake)
    to_review(app, tmp_path)
    app.review.confirm.invoke()
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert app.converting.cancel.instate(["!disabled"])
    app.converting.cancel.invoke()
    held.gate.set()
    pump(app, until=lambda: converted(app))
    assert app.presenter.state is AppState.CANCELLED
    assert fake.run_calls[-1]["cancel"].is_set()


# --- After converting ------------------------------------------------------------------------


def test_ac_11_the_result_tells_counts_problems_and_opens_the_folder(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(
        plan=plan,
        statuses={"a.pdf": OutcomeStatus.FAILED},
        settings=replace_settings(QUIET, open_output_when_done=True),
    )
    app = window(fake)
    to_review(app, tmp_path)
    app.review.confirm.invoke()
    pump(app, until=lambda: converted(app))
    assert app.results.stats.figures()[:3] == [
        ("Converted", "1"),
        ("Skipped", "0"),
        ("Failed", "1"),
    ]
    assert "password" in app.results.detail.cget("text")
    assert fake.opened == [Path("/docs/ClearMD_Output")]  # opened by itself
    app.results.open.invoke()
    assert len(fake.opened) == 2


def test_ac_12_one_failed_file_never_stops_the_batch(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf"), planned("c.pdf")), (), ())
    app = window(FakeBackend(plan=plan, statuses={"a.pdf": OutcomeStatus.FAILED}, settings=QUIET))
    to_review(app, tmp_path)
    app.review.confirm.invoke()
    pump(app, until=lambda: converted(app))
    assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
    assert ("Converted", "2") in app.results.stats.figures()


# --- Help, welcome, settings -----------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_13_help_is_always_one_click_away(
    window: Callable[..., TtkApp], tmp_path: Path, language: str
) -> None:
    held = Held()
    fake = FakeBackend(settings=replace_settings(QUIET, language=language), before_finish=held)
    app = window(fake)
    to_review(app, tmp_path)
    app.review.confirm.invoke()
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert app.rail.help.instate(["!disabled"])  # even while converting
    app.rail.help.invoke()
    assert app.dialog is not None
    shown = " ".join(str(child.cget("text")) for child in app.dialog.body.winfo_children())
    catalog = load_catalog(language)
    for section in ("how", "formats", "where", "privacy", "language"):
        assert catalog.text(f"gui.help.{section}") in shown
    assert "Settings" in shown and "Ajustes" in shown  # where to switch, in both languages
    app.dialog.close()
    held.gate.set()
    pump(app, until=lambda: converted(app))


def test_ac_14_the_welcome_appears_until_dont_show_again(
    window: Callable[..., TtkApp],
) -> None:
    backend = MemoryBackend(Settings())  # first run: show_welcome is on
    app = window(backend)
    pump(app, until=lambda: app.dialog is not None)
    dialog = app.dialog
    assert isinstance(dialog, WelcomeDialog)
    texts = [str(child.cget("text")) for child in dialog.body.winfo_children()]
    assert [text for text in texts if text[:2] in {"1.", "2.", "3."}] == [
        "1. Choose files or a folder",
        "2. Review what will be converted",
        "3. Done, your folder opens",
    ]
    dialog.dont_show.set(True)
    dialog.close()
    assert backend.settings.show_welcome is False
    again = window(backend)
    pump(again, seconds=0.3)
    assert again.dialog is None


def test_ac_15_the_settings_window_saves_settings_toml_and_applies_it(
    window: Callable[..., TtkApp],
) -> None:
    app = window(ApiBackend())
    if app.dialog is not None:  # the welcome of a first run
        app.dialog.close()
    app.rail.settings.invoke()
    dialog = app.dialog
    assert isinstance(dialog, SettingsDialog)
    assert set(dialog.values) == {
        "language", "theme", "open_output_when_done", "on_existing_output", "recursive",
        "html_strategy", "show_welcome",
    }  # fmt: skip
    dialog.values["language"].set("Español")
    dialog.values["html_strategy"].set("Only the article")
    dialog.save()
    written = tomllib.loads(settings_path().read_text(encoding="utf-8"))
    assert written["language"] == "es" and written["html_strategy"] == "article"
    assert load_settings()[0].language == "es"
    assert app.main.convert.cget("text") == "Convertir"  # applied at once
    app.rail.settings.invoke()
    restored = app.dialog
    assert isinstance(restored, SettingsDialog)
    restored.restore()
    assert restored.chosen().language == "en"


# --- Look and keyboard -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("system", "theme"), [("dark", "clearmd-dark"), ("light", "clearmd-light")]
)
def test_ac_16_the_theme_follows_the_system_by_default(
    window: Callable[..., TtkApp], monkeypatch: pytest.MonkeyPatch, system: str, theme: str
) -> None:
    monkeypatch.setattr(presenter_module, "detect_system_theme", lambda: system)
    app = window(FakeBackend(settings=QUIET))  # theme: "system"
    assert app.style.theme_use() == theme


def test_ac_17_the_8_px_grid_14_px_text_and_one_primary_action_per_screen(
    window: Callable[..., TtkApp],
) -> None:
    app = window(FakeBackend(settings=QUIET))
    for widget in widgets(app.root):
        manager = widget.winfo_manager()
        if manager not in {"pack", "grid"}:
            continue
        info = widget.pack_info() if manager == "pack" else widget.grid_info()
        for option in ("padx", "pady", "ipadx", "ipady"):
            value = info.get(option, 0)
            for part in value if isinstance(value, tuple) else str(value).split():
                assert on_grid(int(float(part))), (str(widget), option, part)
    assert all(font.cget("size") <= BODY for font in app.fonts.values())  # pixels: negative
    for page in app.pages:  # one primary action per screen; the progress has only Cancel
        primaries = [w for w in widgets(page) if styled(w) == PRIMARY]
        assert len(primaries) == (0 if page is app.converting else 1), page


def styled(widget: Any) -> str:
    try:
        return str(widget.cget("style"))
    except Exception:  # noqa: BLE001 -- a classic Tk widget has no style
        return ""


def test_ac_18_everything_works_with_the_keyboard(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    app = window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path])
    pump(app, seconds=0.1)
    chain: list[Any] = []
    widget: Any = app.main.add_files
    for _ in range(40):
        chain.append(widget)
        widget = widget.tk_focusNext()
        if widget is None or widget is app.main.add_files:
            break
    assert {app.main.add_folder, app.main.inputs.tree, app.main.convert} <= set(chain)
    press_enter(app)  # Enter: the primary action
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    app.rail.help.invoke()
    assert app.dialog is not None
    app.dialog.focus_force()
    pump(app, seconds=0.1)
    app.dialog.event_generate("<Escape>", when="tail")  # Esc closes a dialog
    pump(app, until=lambda: app.dialog is None, seconds=1.0)
    assert app.dialog is None


def test_ac_19_nothing_is_reachable_only_by_hover(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(settings=QUIET))
    hovering = [
        str(widget) for widget in widgets(app.root) if "<Enter>" in widget.bind()
    ]  # no tooltip, no hover-only control
    assert hovering == []


# --- Delivered -------------------------------------------------------------------------------


def test_ac_20_clearmd_ttk_starts_the_gui_and_converts_like_the_cli(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert scripts["project"]["gui-scripts"]["clearmd-ttk"] == "clearmd.frontend.ttk:main"
    names = ("sample.docx", "sample.csv", "sample.txt", "encrypted.pdf")
    by_gui = copy_documents(tmp_path / "gui" / "Docs", *names)
    by_cli = copy_documents(tmp_path / "cli" / "Docs", *names)
    app = window(MemoryBackend(QUIET))
    to_review(app, by_gui)
    app.review.confirm.invoke()
    pump(app, until=lambda: converted(app), seconds=120)
    cli_main([str(by_cli), "--quiet"])

    def outputs(root: Path) -> dict[str, str]:
        out = root / "ClearMD_Output" / "OutputMD"
        return {str(p.relative_to(out)): p.read_text(encoding="utf-8") for p in out.rglob("*.md")}

    assert outputs(tmp_path / "gui") == outputs(tmp_path / "cli") != {}
    summaries = [
        (root / "ClearMD_Output" / "Resumen_ClearMD.md").read_text(encoding="utf-8")
        for root in (tmp_path / "gui", tmp_path / "cli")
    ]
    tables = [[line for line in text.splitlines() if line.startswith("| `")] for text in summaries]
    assert tables[0] == tables[1] != []


def test_ac_21_screenshots_of_every_screen_light_and_dark_english_and_spanish() -> None:
    shots = ROOT / "docs" / "screenshots" / "005"
    screens = (
        "0-welcome",
        "1-choose",
        "2-review",
        "3-convert",
        "4-results",
        "5-help",
        "6-settings",
    )
    for screen in screens:
        for theme in ("light", "dark"):
            for language in ("en", "es"):
                assert (shots / f"{screen}-{theme}-{language}.png").is_file()


def test_ac_22_the_window_wears_clearmds_identity(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(settings=replace_settings(QUIET, theme="dark")))
    assert app.style.theme_use() == "clearmd-dark"
    assert app.rail.step_texts() == ["> Choose", "Review", "Convert", "Results"]
    assert {"Primary.ClearMD.TButton.face", "Card.ClearMD.face"} <= set(app.style.element_names())
    assert [icon.width() for icon in app._icons] == [16, 32, 48, 64, 128, 256]


def test_ac_23_every_list_shows_number_icon_and_name(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.docx")),
        (SkippedItem(Path("/docs/n.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    app = window(FakeBackend(plan=plan, statuses={"a.pdf": OutcomeStatus.FAILED}, settings=QUIET))
    app.presenter.add_paths([tmp_path])
    lists = [app.main.inputs]
    to_review(app, tmp_path)
    lists.append(app.review.files)
    assert [row.icon for row in app.last_plan.rows] == ["pdf", "docx", "markdown"]  # type: ignore[union-attr]
    app.review.confirm.invoke()
    pump(app, until=lambda: converted(app))
    lists.append(app.results.problems)
    for file_list in lists:
        tree = file_list.tree
        assert tree.get_children() and all(tree.item(i, "image") for i in tree.get_children())
    icons = ROOT / "src" / "clearmd" / "frontend" / "assets" / "icons"
    assert all((icons / f"{name}.png").is_file() for name in ICONS)


def replace_settings(settings: Settings, **changes: Any) -> Settings:
    from dataclasses import replace

    return replace(settings, **changes)
