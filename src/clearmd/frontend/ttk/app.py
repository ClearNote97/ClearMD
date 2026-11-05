"""The ttkbootstrap GUI: one window that draws what the presenter gives it (ADR-0026, ADR-0027).

``TtkApp`` implements the presenter's ``View``: every text and state comes from the presenter; the
window only lays it out and forwards the user's intents (buttons, keys, dropped files).
"""

import sys
import time
import tkinter as tk
from collections.abc import Callable, Sequence
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Any

from tkinterdnd2 import DND_FILES

import clearmd.frontend.launch as launch
from clearmd.backend.schemas.formats import EXTENSIONS
from clearmd.frontend.design.metrics import COMPACT_BELOW, SHORT_BELOW, SPACE
from clearmd.frontend.design.palette import LIGHT, PALETTES, Palette
from clearmd.frontend.presenter import Action, AppState, Presenter
from clearmd.frontend.presenter.chrome import close_policy
from clearmd.frontend.presenter.chrome.header import header_of
from clearmd.frontend.presenter.chrome.secondary import SecondaryKind, ready_line, secondary_of
from clearmd.frontend.presenter.models import (
    InputRow,
    OutputChoice,
    PlanView,
    ProgressView,
    ResultView,
    StateView,
)
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.ttk.components.action_bar import ActionBar
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.components.rail import Rail
from clearmd.frontend.ttk.components.surface import Surface
from clearmd.frontend.ttk.layout.fonts import make_fonts
from clearmd.frontend.ttk.views.choose import MainView
from clearmd.frontend.ttk.views.convert import ConvertView
from clearmd.frontend.ttk.views.results import ResultsView
from clearmd.frontend.ttk.views.review import ReviewView
from clearmd.frontend.ttk.visuals.look import Look
from clearmd.frontend.ttk.visuals.style_names import WARNING
from clearmd.frontend.ttk.window import toolkit
from clearmd.frontend.ttk.window.dialog_host import DialogHost
from clearmd.frontend.ttk.window.presses import Presses
from clearmd.frontend.ttk.window.primary_button import PrimaryButton
from clearmd.frontend.ttk.window.scheduler import Scheduler
from clearmd.frontend.ttk.window.shown import Shown
from clearmd.i18n import Catalog


class TtkApp:
    """The window, and the presenter's view."""

    def __init__(self, backend: Backend | None = None, *, root: tk.Tk | None = None) -> None:
        # TkinterDnD.Tk: a Tk root with drag and drop (tkinterdnd2 has no types). Without its
        # library (a Tk it was not built for), the window works with Add files / Add folder only.
        self.root: Any = root or toolkit.root_with_drop()
        self.drops = bool(getattr(self.root, "TkdndVersion", None))
        self.style = toolkit.prepare(self.root)
        self.fonts = make_fonts(self.root)
        self.look = Look(self.style, self.root, self.fonts)
        self.shown = Shown()
        self.look.use(self.shown.palette)  # the styles exist before the widgets that use them
        self.scheduler = Scheduler(self.root)
        self.presenter = Presenter(self, backend)
        self.dialogs = DialogHost(self.root, self.fonts, self.presenter, self.shown)
        self._closing_since: float | None = None  # closed while converting: waiting for the end
        self.presses = Presses()
        self._build()
        self.rail.show_version(self.presenter.version)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    @property
    def dialog(self) -> Dialog | None:
        return self.dialogs.current

    @property
    def state(self) -> StateView | None:
        return self.shown.state

    @property
    def palette(self) -> Palette:
        return self.shown.palette

    @property
    def last_plan(self) -> PlanView | None:
        return self.shown.last_plan

    @property
    def last_result(self) -> ResultView | None:
        return self.shown.last_result

    @property
    def page(self) -> ttk.Frame | None:
        return self.shown.page

    # --- Building ------------------------------------------------------------------------------

    def _build(self) -> None:
        self._icons = toolkit.set_icons(self.root)

        self.rail = Rail(
            self.root,
            fonts=self.fonts,
            on_settings=self.dialogs.show_settings,
            on_help=self.dialogs.show_help,
            on_step=lambda page: self.presenter.go_to(page),
        )
        self.rail.pack(side="left", fill="y")
        self.surface = Surface(self.root, fonts=self.fonts)
        self.surface.pack(side="left", fill="both", expand=True)
        page = self.surface.page

        # One action bar for every page (ADR-0029), the message above it.
        self.actions = ActionBar(page, on_primary=lambda: self.primary_button.press())
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
        self.primary_button = PrimaryButton(
            self.root, self.actions, self.review, self.presenter, self.dialogs, self.shown
        )
        self.pages: tuple[ttk.Frame, ...] = (self.main, self.review, self.converting, self.results)
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
        if self.shown.state is not None and Action.ADD not in self.shown.state.enabled:
            return
        catalog = self.shown.need_catalog()
        patterns = " ".join(f"*{extension}" for extension in sorted(EXTENSIONS))
        chosen = filedialog.askopenfilenames(
            parent=self.root,
            title=catalog.text("gui.main.pick_files_title"),
            filetypes=[(catalog.text("gui.main.documents"), patterns), ("*", "*")],
        )
        if chosen:
            self.presenter.add_paths([Path(path) for path in chosen])

    def add_folder(self) -> None:
        if self.shown.state is not None and Action.ADD not in self.shown.state.enabled:
            return
        chosen = filedialog.askdirectory(
            parent=self.root, title=self.shown.need_catalog().text("gui.main.pick_folder_title")
        )
        if chosen:
            self.presenter.add_paths([Path(chosen)])

    def pick_output_folder(self) -> None:
        if self.shown.state is not None and Action.CHOOSE_OUTPUT not in self.shown.state.enabled:
            return
        suggestion = self.presenter.settings.last_output_folder or None
        chosen = filedialog.askdirectory(
            parent=self.root,
            title=self.shown.need_catalog().text("gui.main.pick_output_title"),
            initialdir=suggestion,
        )
        if chosen:
            self.presenter.choose_output_folder(Path(chosen))
        else:  # cancelled: the radio buttons show the choice as it was
            current = self.presenter.output_folder
            self.main.output_mode.set("folder" if current is not None else "next_to")

    def _dropped(self, event: Any) -> None:  # tkinterdnd2's event: ``data`` holds the paths
        paths = [Path(item) for item in self.root.tk.splitlist(event.data)]
        if self.shown.state is not None and Action.ADD in self.shown.state.enabled:
            self.presenter.add_paths(paths)

    def _enter(self, event: Any) -> None:
        if self.presses.pressed(event):  # held down: one press, whatever the page (F-1)
            self.primary_button.press()

    def _space(self, event: Any) -> str | None:
        return None if self.presses.pressed(event) else "break"  # "break": the button stays

    def _window_resized(self, event: Any) -> None:
        if event.widget is self.root:
            self.rail.set_compact(self.root.winfo_width() < COMPACT_BELOW)
            self.main.set_short(self.root.winfo_height() < SHORT_BELOW)

    def close(self) -> None:
        """Closing while converting cancels, hides the window and waits for the batch to end, so
        the summary of what was done is still written (AC-10); then the window closes."""
        if self._closing_since is not None:
            return
        if self.dialogs.current is not None:
            self.dialogs.current.close()  # its answer counts ("Don't show again")
        self.presenter.shutdown()
        step = close_policy.on_close(
            self.shown.state.state if self.shown.state is not None else None
        )
        if step is close_policy.CloseStep.CANCEL_AND_WAIT:
            self._closing_since = time.monotonic()
            self.presenter.cancel()
            self.root.withdraw()
            self.root.after(close_policy.CLOSE_POLL_MS, self._close_when_done)
            return
        if step is close_policy.CloseStep.CANCEL_THEN_NOW:
            self.presenter.cancel()
        self._destroy()

    def _close_when_done(self) -> None:
        waited = time.monotonic() - (self._closing_since or 0.0)
        if close_policy.keep_waiting(
            self.shown.state.state if self.shown.state is not None else None, waited
        ):
            self.root.after(close_policy.CLOSE_POLL_MS, self._close_when_done)
            return
        self._destroy()

    def _destroy(self) -> None:
        self.primary_button.cancel_pause()
        self.scheduler.close()
        self.root.update_idletasks()  # Tk's own idle work (a theme change) runs before the end
        self.root.destroy()

    # --- The View the presenter draws on ---------------------------------------------------------

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self.scheduler.after(milliseconds, callback)

    def show_state(self, state: StateView) -> None:
        previous = self.shown.state
        self.shown.state = state
        if state.state is not AppState.ANALYZING:
            self.shown.scan = None
        if previous is not None and previous.page != state.page:
            self.message.configure(text="")  # a message belongs to the page it was given on
            self.primary_button.page_shown()
        converting = state.state is AppState.CONVERTING
        if converting and (previous is None or previous.state is not AppState.CONVERTING):
            self.converting.clear()
        elif state.state is AppState.WAITING_DECISION:
            self._show_ready()
        self._show_page(self.pages[state.page - 1])
        self.rail.show_page(state.page)
        self.actions.show(state.primary)
        if previous is not None and previous.page != state.page:
            self.primary_button.pause()
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
        second = secondary_of(
            self.shown.need_catalog(), state, has_result=self.shown.last_result is not None
        )
        commands = {
            SecondaryKind.CANCEL: self.presenter.cancel,
            SecondaryKind.BACK: lambda: self.presenter.go_to(second.back_to),
            SecondaryKind.AGAIN: self.dialogs.convert_more,
        }
        command = commands.get(second.kind)
        self.actions.show_secondary(second.text or None, command, strong=second.strong)

    def _show_ready(self) -> None:
        """Convert's card before the batch: how many are ready, and where they go."""
        count = ready_line(self.shown.catalog, self.shown.last_plan)
        if count is not None:
            self.converting.show_ready(count, str(self.main.output_label.cget("text")))

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self.main.show_inputs(rows)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self.main.show_output_choice(choice)
        if self.converting.dimmed:  # the waiting card says where results will go (014)
            self.converting.ready_where.configure(text=str(self.main.output_label.cget("text")))

    def show_scan(self, text: str) -> None:
        self.shown.scan = text
        self._header()

    def show_plan(self, plan: PlanView) -> None:
        self.shown.last_plan = plan
        self.review.show(plan)

    def show_progress(self, progress: ProgressView) -> None:
        self.shown.last_progress = progress
        self.converting.show(progress)

    def show_result(self, result: ResultView) -> None:
        self.shown.last_result = result
        self.results.show(result)

    def _show_page(self, page: ttk.Frame) -> None:
        if page is self.shown.page:
            return
        if self.shown.page is not None:
            self.shown.page.pack_forget()
        page.pack(fill="both", expand=True)
        self.shown.page = page

    def forget_work(self) -> None:
        self.shown.last_plan = None
        self.shown.last_result = None
        self.review.forget()
        self.converting.forget(str(self.main.output_label.cget("text")))
        self.results.forget()

    def show_message(self, text: str) -> None:
        self.message.configure(text=text)

    def show_welcome(self, steps: tuple[str, ...]) -> None:
        # Once the window is on screen: the presenter asks for it while starting.
        self.scheduler.after(0, lambda: self.dialogs.welcome(steps))

    def apply_theme(self, theme: str) -> None:
        self.shown.palette = PALETTES.get(theme, LIGHT)
        self.look.use(self.shown.palette)
        self.root.configure(background=self.shown.palette.ground)
        self.rail.apply_palette(self.shown.palette)
        self.surface.apply_palette(self.shown.palette)
        for view in (self.main, self.review, self.results):
            view.apply_palette(self.shown.palette)

    def apply_language(self, catalog: Catalog) -> None:
        self.shown.catalog = catalog
        self.root.title(catalog.text("gui.app.title"))
        self.rail.apply_language(catalog)
        for view in (self.main, self.review, self.converting, self.results):
            view.apply_language(catalog)
        self._header()

    def _header(self) -> None:
        if self.shown.catalog is None or self.shown.state is None:
            return
        header = header_of(self.shown.catalog, self.shown.state, self.shown.scan)
        self.surface.show_header(
            eyebrow=header.eyebrow, title=header.title, subtitle=header.subtitle
        )

    # --- Running ---------------------------------------------------------------------------------

    def start(self) -> None:
        self.presenter.start()
        self.root.deiconify()


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
