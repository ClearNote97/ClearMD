"""The ttkbootstrap GUI: one window that draws what the presenter gives it (ADR-0026, ADR-0027).

``TtkApp`` implements the presenter's ``View``: every text and state comes from the presenter; the
window only lays it out and forwards the user's intents (buttons, keys, dropped files).
"""

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

from clearmd.backend.schemas.formats import EXTENSIONS
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
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.components.rail import Rail
from clearmd.frontend.ttk.components.surface import Surface
from clearmd.frontend.ttk.layout import (
    BODY,
    EYEBROW,
    MIN_HEIGHT,
    MIN_WIDTH,
    SPACE,
    START_SIZE,
    STRONG,
    TITLE,
    WORDMARK,
)
from clearmd.frontend.ttk.scheduler import Scheduler
from clearmd.frontend.ttk.views.dialogs import SettingsDialog, WelcomeDialog, help_dialog
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
        # TkinterDnD.Tk: a Tk root with drag and drop (tkinterdnd2 has no types).
        self.root: Any = root or TkinterDnD.Tk()
        self.root.withdraw()  # shown once laid out, in its theme (no flash of the wrong one)
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.geometry(START_SIZE)
        _forget_dead_style()
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
        self._build()
        self.presenter = Presenter(self, backend)
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
            self.root, fonts=self.fonts, on_settings=self.show_settings, on_help=self.show_help
        )
        self.rail.pack(side="left", fill="y")
        self.surface = Surface(self.root, fonts=self.fonts)
        self.surface.pack(side="left", fill="both", expand=True)
        page = self.surface.page

        self.message = ttk.Label(page, style=WARNING, anchor="w", justify="left")
        page.bind("<Configure>", lambda event: self.message.configure(wraplength=event.width))
        self.message.pack(side="bottom", fill="x", pady=(SPACE, 0))
        self.main = MainView(
            page,
            fonts=self.fonts,
            on_add_files=self.add_files,
            on_add_folder=self.add_folder,
            on_remove=lambda path: self.presenter.remove_input(path),
            on_clear=lambda: self.presenter.clear_inputs(),
            on_next_to=lambda: self.presenter.choose_output_next_to(),
            on_pick_folder=self.pick_output_folder,
            on_convert=lambda: self.presenter.analyze(),
        )
        self.review = ReviewView(
            page,
            fonts=self.fonts,
            on_back=lambda: self.presenter.back(),
            on_confirm=lambda overwrite: self.presenter.confirm(overwrite),
        )
        self.converting = ConvertView(
            page, fonts=self.fonts, on_cancel=lambda: self.presenter.cancel()
        )
        self.results = ResultsView(
            page,
            fonts=self.fonts,
            on_again=lambda: self.presenter.back(),
            on_open=lambda: self.presenter.open_results(),
        )
        # One page per step (ADR-0027): Choose (also while analyzing), Review, Convert, Results.
        self.pages: tuple[ttk.Frame, ...] = (self.main, self.review, self.converting, self.results)
        self.page: ttk.Frame | None = None
        self._show_page(self.main)

        # Files and folders dropped anywhere on the window (tkinterdnd2, ADR-0026).
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self._dropped)
        self.root.bind("<Return>", lambda _event: self._primary())

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

    def _primary(self) -> None:
        """Enter triggers the screen's primary action (UX §6)."""
        if self.state is None:
            return
        if Action.CONVERT in self.state.enabled:
            self.presenter.analyze()
        elif Action.CONFIRM in self.state.enabled:
            self.review.confirm.invoke()  # with the answer about existing results
        elif Action.OPEN_RESULTS in self.state.enabled:
            self.presenter.open_results()

    def show_help(self) -> None:
        """The "?" window: always available (UX §4)."""
        if self.dialog is None:
            self._open(
                help_dialog(self.root, self._catalog(), self.palette, self.fonts, self._closed)
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
        if previous is None or previous.step != state.step:
            self.message.configure(text="")  # a message belongs to the step it was given in
        if state.state is AppState.CONVERTING and (previous is None or previous.step != 3):
            self.converting.clear()
        page = self.main if state.state is AppState.ANALYZING else self.pages[state.step - 1]
        self._show_page(page)
        self.rail.show_step(state.step)
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
            (main.convert, Action.CONVERT),
            (self.review.back, Action.BACK),
            (self.review.confirm, Action.CONFIRM),
            (self.converting.cancel, Action.CANCEL),
            (self.results.again, Action.BACK),
            (self.results.open, Action.OPEN_RESULTS),
            (self.rail.settings, Action.SETTINGS),
            (self.rail.help, Action.HELP),
        ):
            button.state(["!disabled"] if action in state.enabled else ["disabled"])

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self.main.show_inputs(rows)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self.main.show_output_choice(choice)

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
        step = STEPS[state.step - 1]
        eyebrow = catalog.text("gui.steps.counter", step=state.step, total=len(STEPS))
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


CLOSE_POLL_MS = 50
CLOSE_WAIT_SECONDS = 60  # closing while converting: at most this long for the batch to stop
SMOKE_SECONDS = 3  # ``--smoke``: the executable's own check in CI (ADR-0028)


def main(argv: Sequence[str] | None = None) -> None:
    """``clearmd-ttk``: the window, until it is closed. ``--smoke`` opens it and closes it after
    a few seconds: CI checks that the executable starts (its data, its toolkit)."""
    import multiprocessing

    multiprocessing.freeze_support()  # a no-op unless running as a packaged executable
    arguments = sys.argv[1:] if argv is None else list(argv)
    app = TtkApp()
    app.start()
    _close_splash()
    if "--smoke" in arguments:
        app.root.after(SMOKE_SECONDS * 1000, app.close)
    app.root.mainloop()


def _close_splash() -> None:
    """The executable shows a splash while it unpacks (PyInstaller); the window replaces it."""
    try:
        import pyi_splash  # type: ignore[import-not-found,import-untyped,unused-ignore]  # frozen only
    except ImportError:
        return
    pyi_splash.close()
