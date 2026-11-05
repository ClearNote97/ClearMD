"""The ttkbootstrap GUI: one window that draws what the presenter gives it (ADR-0026, ADR-0027).

``TtkApp`` implements the presenter's ``View``: every text and state comes from the presenter; the
window only lays it out and forwards the user's intents (buttons, keys, dropped files).
"""

import contextlib
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Any, Literal

import ttkbootstrap as tb
from PIL import ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

import clearmd.frontend.launch as launch
from clearmd.backend.schemas.formats import EXTENSIONS
from clearmd.frontend.design.metrics import COMPACT_BELOW, MIN_HEIGHT, MIN_WIDTH, SHORT_BELOW, SPACE
from clearmd.frontend.presenter import Action, AppState, Presenter
from clearmd.frontend.presenter.models import (
    InputRow,
    OutputChoice,
    PlanView,
    ProgressView,
    ResultView,
    StateView,
)
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.presenter.state import STEPS
from clearmd.frontend.ttk import art
from clearmd.frontend.ttk.brand import LIGHT, PALETTES, WARNING, Look, Palette, register_themes
from clearmd.frontend.ttk.components.action_bar import ActionBar
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.components.rail import Rail
from clearmd.frontend.ttk.components.surface import Surface
from clearmd.frontend.ttk.layout import BODY, EYEBROW, START_SIZE, STRONG, TITLE, WORDMARK
from clearmd.frontend.ttk.presses import Presses
from clearmd.frontend.ttk.scheduler import Scheduler
from clearmd.frontend.ttk.views.dialogs import (
    KeepInputsDialog,
    SettingsDialog,
    WelcomeDialog,
    help_dialog,
)
from clearmd.frontend.ttk.views.main import MainView
from clearmd.frontend.ttk.views.plan import ReviewView
from clearmd.frontend.ttk.views.progress import ConvertView
from clearmd.frontend.ttk.views.result import ResultsView
from clearmd.i18n import Catalog

_NAMED_FONTS = ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont")
_APP_ICON_SIZES = (16, 32, 48, 64, 128, 256)


class TtkApp:
    """The window, and the presenter's view."""

    def __init__(self, backend: Backend | None = None, *, root: tk.Tk | None = None) -> None:
        # TkinterDnD.Tk: a Tk root with drag and drop (tkinterdnd2 has no types). Without its
        # library (a Tk it was not built for), the window works with Add files / Add folder only.
        self.root: Any = root or _root_with_drop()
        self.drops = bool(getattr(self.root, "TkdndVersion", None))
        self.root.withdraw()  # shown once laid out, in its theme (no flash of the wrong one)
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.geometry(START_SIZE)
        _forget_dead_style()
        # ttkbootstrap speaks to tkinter's default root, not to the one it is given: this window
        # is it, so its styles and messages (Tcl's msgcat) are made in this interpreter, never in
        # one left by an earlier window (CI on Windows, Python 3.12).
        tk._default_root = self.root  # type: ignore[attr-defined]
        # ttkbootstrap calls Tcl's msgcat without loading it: it works only when Tk happened to
        # load it first, which a new interpreter on Windows does not always do (CI, 014).
        with contextlib.suppress(tk.TclError):
            self.root.tk.call("package", "require", "msgcat")
        self.style = tb.Style()
        register_themes(self.style)
        self.fonts = self._fonts()
        self.look = Look(self.style, self.root, self.fonts)
        self.palette: Palette = LIGHT
        self.look.use(self.palette)  # the styles exist before the widgets that use them
        self.scheduler = Scheduler(self.root)
        self.catalog: Catalog | None = None
        self.state: StateView | None = None
        self.last_plan: PlanView | None = None
        self.last_progress: ProgressView | None = None
        self.last_result: ResultView | None = None
        self._scan: str | None = None
        self.dialog: Dialog | None = None  # the open dialog: one at a time
        self._closing_since: float | None = None  # closed while converting: waiting for the end
        self._page_shown_at = 0.0  # when the page on screen changed (F-1)
        self._unpause: str | None = None  # the end of that pause
        self.presses = Presses()
        self._build()
        self.presenter = Presenter(self, backend)
        self.rail.show_version(self.presenter.version)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # --- Building ------------------------------------------------------------------------------

    def _fonts(self) -> dict[str, tkfont.Font]:
        for name in _NAMED_FONTS:
            tkfont.nametofont(name, root=self.root).configure(size=BODY)
        family = tkfont.nametofont("TkDefaultFont", root=self.root).actual("family")

        def font(size: int, weight: Literal["normal", "bold"] = "normal") -> tkfont.Font:
            return tkfont.Font(root=self.root, family=family, size=size, weight=weight)

        return {
            "body": tkfont.nametofont("TkDefaultFont", root=self.root),
            "strong": font(STRONG, "bold"),
            "eyebrow": font(EYEBROW, "bold"),
            "title": font(TITLE, "bold"),
            "wordmark": font(WORDMARK, "bold"),
        }

    def _build(self) -> None:
        icons = [
            ImageTk.PhotoImage(art.logo(f"clearmd-app-{size}"), master=self.root)
            for size in _APP_ICON_SIZES
        ]
        self._icons = icons  # Tk forgets an image Python does not hold
        self.root.iconphoto(True, *icons)

        self.rail = Rail(
            self.root,
            fonts=self.fonts,
            on_settings=self.show_settings,
            on_help=self.show_help,
            on_step=lambda page: self.presenter.go_to(page),
        )
        self.rail.pack(side="left", fill="y")
        self.surface = Surface(self.root, fonts=self.fonts)
        self.surface.pack(side="left", fill="both", expand=True)
        page = self.surface.page

        # One action bar for every page (ADR-0029), the message above it.
        self.actions = ActionBar(page, on_primary=self._primary)
        self.actions.pack(side="bottom", fill="x", pady=(SPACE, 0))
        self.message = ttk.Label(page, style=WARNING, anchor="w", justify="left")
        page.bind("<Configure>", lambda event: self.message.configure(wraplength=event.width))
        self.message.pack(side="bottom", fill="x", pady=(SPACE, 0))
        self.main = MainView(
            page,
            fonts=self.fonts,
            on_add_files=self.add_files,
            on_add_folder=self.add_folder,
            on_remove=lambda paths: self.presenter.remove_inputs(paths),
            on_clear=lambda: self.presenter.clear_inputs(),
            on_next_to=lambda: self.presenter.choose_output_next_to(),
            on_pick_folder=self.pick_output_folder,
            on_summary=lambda value: self.presenter.choose_summary_format(value),
            on_images=lambda value: self.presenter.choose_images(value),
        )
        self.review = ReviewView(page, fonts=self.fonts)
        self.converting = ConvertView(page, fonts=self.fonts)
        self.results = ResultsView(page, fonts=self.fonts)
        # One page per step (ADR-0027): Choose (also while analyzing), Review, Convert, Results.
        self.pages: tuple[ttk.Frame, ...] = (self.main, self.review, self.converting, self.results)
        self.page: ttk.Frame | None = None
        self._show_page(self.main)

        # Files and folders dropped anywhere on the window (tkinterdnd2, ADR-0026).
        if self.drops:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._dropped)
        self.root.bind("<KeyPress-Return>", self._enter)
        self.root.bind("<KeyRelease-Return>", self.presses.released)
        # Space on the focused primary button: held, it is one press too (F-1).
        self.actions.primary.bind("<KeyPress-space>", self._space)
        self.actions.primary.bind("<KeyRelease-space>", self.presses.released)
        for number in range(1, 5):  # the rail by keyboard (AC-01)
            self.root.bind(
                f"<Control-Key-{number}>", lambda _event, n=number: self.presenter.go_to(n)
            )
        self.root.bind("<Configure>", self._window_resized, add="+")

    # --- Intents ---------------------------------------------------------------------------------

    def add_files(self) -> None:
        if self.state is not None and Action.ADD not in self.state.enabled:
            return
        catalog = self._catalog()
        patterns = " ".join(f"*{extension}" for extension in sorted(EXTENSIONS))
        chosen = filedialog.askopenfilenames(
            parent=self.root,
            title=catalog.text("gui.main.pick_files_title"),
            filetypes=[(catalog.text("gui.main.documents"), patterns), ("*", "*")],
        )
        if chosen:
            self.presenter.add_paths([Path(path) for path in chosen])

    def add_folder(self) -> None:
        if self.state is not None and Action.ADD not in self.state.enabled:
            return
        chosen = filedialog.askdirectory(
            parent=self.root, title=self._catalog().text("gui.main.pick_folder_title")
        )
        if chosen:
            self.presenter.add_paths([Path(chosen)])

    def pick_output_folder(self) -> None:
        if self.state is not None and Action.CHOOSE_OUTPUT not in self.state.enabled:
            return
        suggestion = self.presenter.settings.last_output_folder or None
        chosen = filedialog.askdirectory(
            parent=self.root,
            title=self._catalog().text("gui.main.pick_output_title"),
            initialdir=suggestion,
        )
        if chosen:
            self.presenter.choose_output_folder(Path(chosen))
        else:  # cancelled: the radio buttons show the choice as it was
            current = self.presenter.output_folder
            self.main.output_mode.set("folder" if current is not None else "next_to")

    def _dropped(self, event: Any) -> None:  # tkinterdnd2's event: ``data`` holds the paths
        paths = [Path(item) for item in self.root.tk.splitlist(event.data)]
        if self.state is not None and Action.ADD in self.state.enabled:
            self.presenter.add_paths(paths)

    def _enter(self, event: Any) -> None:
        if self.presses.pressed(event):  # held down: one press, whatever the page (F-1)
            self._primary()

    def _space(self, event: Any) -> str | None:
        return None if self.presses.pressed(event) else "break"  # "break": the button stays

    def _primary(self) -> None:
        """The page's primary action, from its button or Enter (UX §6, ADR-0029). Right after the
        page changes it waits a moment, shown disabled: a double click must not run Next and
        Convert past a page the user did not see (security audit of 007, F-1)."""
        if self.dialog is not None:
            return
        if time.monotonic() - self._page_shown_at < PRIMARY_PAUSE_SECONDS:
            return
        self.presenter.press_primary(self.review.overwrite_answer())

    def _pause_primary(self) -> None:
        """The primary button is disabled for the pause after a page change, so it is seen."""
        if self._unpause is not None:
            self.root.after_cancel(self._unpause)
            self._unpause = None
        if PRIMARY_PAUSE_SECONDS <= 0 or self.actions.primary.instate(["disabled"]):
            return
        self.actions.primary.state(["disabled"])
        self._unpause = self.root.after(int(PRIMARY_PAUSE_SECONDS * 1000), self._end_pause)

    def _end_pause(self) -> None:
        self._unpause = None
        if self.state is not None:
            self.actions.show(self.state.primary)

    def convert_more(self) -> None:
        """Asked every time: keep the chosen files, or start empty (feature 007)."""
        if self.dialog is not None:
            return
        dialog = KeepInputsDialog(
            self.root,
            self._catalog(),
            self.palette,
            self.fonts,
            on_answer=lambda keep: self.presenter.convert_more(keep=keep),
            on_close=self._closed,
        )
        self._open(dialog)

    def _window_resized(self, event: Any) -> None:
        if event.widget is self.root:
            self.rail.set_compact(self.root.winfo_width() < COMPACT_BELOW)
            self.main.set_short(self.root.winfo_height() < SHORT_BELOW)

    def show_help(self) -> None:
        """The "?" window: always available (UX §4)."""
        if self.dialog is None:
            self._open(
                help_dialog(
                    self.root,
                    self._catalog(),
                    self.palette,
                    self.fonts,
                    self._closed,
                    version=self.presenter.version,
                )  # fmt: skip
            )

    def show_settings(self) -> None:
        if self.dialog is not None or self.state is None:
            return
        if Action.SETTINGS not in self.state.enabled:
            return
        dialog = SettingsDialog(
            self.root,
            self._catalog(),
            self.palette,
            self.fonts,
            self.presenter.settings,
            on_save=self.presenter.save_settings,
            on_close=self._closed,
        )
        self._open(dialog)

    def _welcome(self, steps: tuple[str, ...]) -> None:
        if self.dialog is not None:
            return

        def done(show_again: bool) -> None:
            self._closed()
            self.presenter.dismiss_welcome(show_again=show_again)

        dialog = WelcomeDialog(self.root, self._catalog(), self.palette, self.fonts, steps, done)
        self._open(dialog)

    def _open(self, dialog: Dialog) -> None:
        self.dialog = dialog
        dialog.open()

    def _closed(self) -> None:
        self.dialog = None

    def close(self) -> None:
        """Closing while converting cancels, hides the window and waits for the batch to end, so
        the summary of what was done is still written (AC-10); then the window closes."""
        if self._closing_since is not None:
            return
        if self.dialog is not None:
            self.dialog.close()  # its answer counts ("Don't show again")
        self.presenter.shutdown()
        if self.state is not None and self.state.state is AppState.CONVERTING:
            self._closing_since = time.monotonic()
            self.presenter.cancel()
            self.root.withdraw()
            self.root.after(CLOSE_POLL_MS, self._close_when_done)
            return
        if self.state is not None and self.state.state is AppState.ANALYZING:
            self.presenter.cancel()
        self._destroy()

    def _close_when_done(self) -> None:
        converting = self.state is not None and self.state.state is AppState.CONVERTING
        waited = time.monotonic() - (self._closing_since or 0.0)
        if converting and waited < CLOSE_WAIT_SECONDS:
            self.root.after(CLOSE_POLL_MS, self._close_when_done)
            return
        self._destroy()

    def _destroy(self) -> None:
        if self._unpause is not None:
            self.root.after_cancel(self._unpause)
            self._unpause = None
        self.scheduler.close()
        self.root.update_idletasks()  # Tk's own idle work (a theme change) runs before the end
        self.root.destroy()

    # --- The View the presenter draws on ---------------------------------------------------------

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self.scheduler.after(milliseconds, callback)

    def show_state(self, state: StateView) -> None:
        previous = self.state
        self.state = state
        if state.state is not AppState.ANALYZING:
            self._scan = None
        if previous is not None and previous.page != state.page:
            self.message.configure(text="")  # a message belongs to the page it was given on
            self._page_shown_at = time.monotonic()
        converting = state.state is AppState.CONVERTING
        if converting and (previous is None or previous.state is not AppState.CONVERTING):
            self.converting.clear()
        elif state.state is AppState.WAITING_DECISION:
            self._show_ready()
        self._show_page(self.pages[state.page - 1])
        self.rail.show_page(state.page)
        self.actions.show(state.primary)
        if previous is not None and previous.page != state.page:
            self._pause_primary()
        self._show_secondary(state)
        self._header()
        main = self.main
        for button, action in (
            (main.add_files, Action.ADD),
            (main.add_folder, Action.ADD),
            (main.remove, Action.REMOVE),
            (main.clear, Action.REMOVE),
            (main.next_to, Action.CHOOSE_OUTPUT),
            (main.in_folder, Action.CHOOSE_OUTPUT),
            (main.pick, Action.CHOOSE_OUTPUT),
            *((button, Action.CHOOSE_OUTPUT) for button in main.summary_buttons),
            (self.rail.settings, Action.SETTINGS),
            (self.rail.help, Action.HELP),
        ):
            button.state(["!disabled"] if action in state.enabled else ["disabled"])

    def _show_secondary(self, state: StateView) -> None:
        """Back on Review and Convert, Cancel while working, Convert more on Results."""
        catalog, bar = self._catalog(), self.actions
        if state.state in {AppState.ANALYZING, AppState.CONVERTING}:
            bar.show_secondary(catalog.text("gui.progress.cancel"), self.presenter.cancel)
        elif state.page in {2, 3}:
            back = state.page - 1
            bar.show_secondary(catalog.text("gui.plan.back"), lambda: self.presenter.go_to(back))
        elif state.page == 4 and Action.BACK in state.enabled and self.last_result is not None:
            bar.show_secondary(catalog.text("gui.result.again"), self.convert_more, strong=True)
        else:
            bar.show_secondary(None)

    def _show_ready(self) -> None:
        """Convert's card before the batch: how many are ready, and where they go."""
        plan = self.last_plan
        if plan is None or self.catalog is None or not plan.stats:
            return
        count = self.catalog.text("gui.convert.ready", count=plan.stats[0].value)
        self.converting.show_ready(count, str(self.main.output_label.cget("text")))

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self.main.show_inputs(rows)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self.main.show_output_choice(choice)
        if self.converting.dimmed:  # the waiting card says where results will go (014)
            self.converting.ready_where.configure(text=str(self.main.output_label.cget("text")))

    def show_scan(self, text: str) -> None:
        self._scan = text
        self._header()

    def show_plan(self, plan: PlanView) -> None:
        self.last_plan = plan
        self.review.show(plan)

    def show_progress(self, progress: ProgressView) -> None:
        self.last_progress = progress
        self.converting.show(progress)

    def show_result(self, result: ResultView) -> None:
        self.last_result = result
        self.results.show(result)

    def _show_page(self, page: ttk.Frame) -> None:
        if page is self.page:
            return
        if self.page is not None:
            self.page.pack_forget()
        page.pack(fill="both", expand=True)
        self.page = page

    def forget_work(self) -> None:
        self.last_plan = None
        self.last_result = None
        self.review.forget()
        self.converting.forget(str(self.main.output_label.cget("text")))
        self.results.forget()

    def show_message(self, text: str) -> None:
        self.message.configure(text=text)

    def show_welcome(self, steps: tuple[str, ...]) -> None:
        # Once the window is on screen: the presenter asks for it while starting.
        self.scheduler.after(0, lambda: self._welcome(steps))

    def apply_theme(self, theme: str) -> None:
        self.palette = PALETTES.get(theme, LIGHT)
        self.look.use(self.palette)
        self.root.configure(background=self.palette.ground)
        self.rail.apply_palette(self.palette)
        self.surface.apply_palette(self.palette)
        for view in (self.main, self.review, self.results):
            view.apply_palette(self.palette)

    def apply_language(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.root.title(catalog.text("gui.app.title"))
        self.rail.apply_language(catalog)
        for view in (self.main, self.review, self.converting, self.results):
            view.apply_language(catalog)
        self._header()

    def _header(self) -> None:
        if self.catalog is None or self.state is None:
            return
        catalog, state = self.catalog, self.state
        step = STEPS[state.page - 1]
        eyebrow = catalog.text("gui.steps.counter", step=state.page, total=len(STEPS))
        if state.state is not AppState.READY:
            eyebrow = f"{eyebrow} · {state.label}"
        self.surface.show_header(
            eyebrow=eyebrow,
            title=catalog.text(f"gui.page.{step}_title"),
            subtitle=self._scan or catalog.text(f"gui.page.{step}_subtitle"),
        )

    def _catalog(self) -> Catalog:
        if self.catalog is None:
            raise RuntimeError("the presenter has not started")
        return self.catalog

    # --- Running ---------------------------------------------------------------------------------

    def start(self) -> None:
        self.presenter.start()
        self.root.deiconify()


def _root_with_drop() -> Any:
    """A Tk root that accepts dropped files, or a plain one if tkdnd cannot be loaded."""
    try:
        return TkinterDnD.Tk()
    except (RuntimeError, tk.TclError):
        # Its Tk interpreter was created before tkdnd failed, and it is now tkinter's default
        # root: images made without a master would go there. It is closed first.
        stale = getattr(tk, "_default_root", None)
        if stale is not None:
            stale.destroy()
        root: Any = tk.Tk()
        root.TkdndVersion = None
        return root


def _forget_dead_style() -> None:
    """ttkbootstrap keeps one Style per process, tied to the first root: a new root (a reopened
    window, a test) needs a new one once that root is gone."""
    existing = tb.Style.instance
    if existing is None:
        return
    try:
        alive = bool(existing.master.winfo_exists())
    except tk.TclError:
        alive = False
    if not alive:
        tb.Style.instance = None


PRIMARY_PAUSE_SECONDS = 0.5  # after a page change, before its primary action counts (F-1)
CLOSE_POLL_MS = 50
CLOSE_WAIT_SECONDS = 60  # closing while converting: at most this long for the batch to stop


def main(argv: Sequence[str] | None = None) -> None:
    """``clearmd-ttk``: the window, until it is closed. ``--smoke`` opens it and closes it after
    a few seconds: CI checks that the executable starts (its data, its toolkit)."""
    import multiprocessing

    multiprocessing.freeze_support()  # a no-op unless running as a packaged executable
    arguments = sys.argv[1:] if argv is None else list(argv)
    launch.splash_text(launch.BUILDING_TEXT)
    app = TtkApp()
    launch.splash_text(launch.LOADED_TEXT)
    app.start()
    launch.close_splash()
    if launch.is_smoke(arguments):
        app.root.after(launch.SMOKE_SECONDS * 1000, app.close)
    app.root.mainloop()
