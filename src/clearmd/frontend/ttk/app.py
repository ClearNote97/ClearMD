"""The ttkbootstrap GUI: one window that draws what the presenter gives it (ADR-0026).

``TtkApp`` implements the presenter's ``View``: every text and state comes from the presenter; the
window only lays it out and forwards the user's intents (buttons, keys, dropped files).
"""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog
from typing import Any

import ttkbootstrap as tb
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
from clearmd.frontend.ttk.layout import (
    BODY,
    GAP,
    MARGIN,
    MIN_HEIGHT,
    MIN_WIDTH,
    SPACE,
    SUBTITLE,
    THEMES,
    TITLE,
)
from clearmd.frontend.ttk.scheduler import Scheduler
from clearmd.frontend.ttk.views.main import MainView
from clearmd.i18n import Catalog

_NAMED_FONTS = ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont")


class TtkApp:
    """The window, and the presenter's view."""

    def __init__(self, backend: Backend | None = None, *, root: tk.Tk | None = None) -> None:
        # TkinterDnD.Tk: a Tk root with drag and drop (tkinterdnd2 has no types).
        self.root: Any = root or TkinterDnD.Tk()
        self.root.withdraw()  # shown once laid out, in its theme (no flash of the wrong one)
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        _forget_dead_style()
        self.style = tb.Style()
        self._fonts()
        self.scheduler = Scheduler(self.root)
        self.catalog: Catalog | None = None
        self.state: StateView | None = None
        self.last_plan: PlanView | None = None
        self.last_progress: ProgressView | None = None
        self.last_result: ResultView | None = None
        self._build()
        self.presenter = Presenter(self, backend)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # --- Building ------------------------------------------------------------------------------

    def _fonts(self) -> None:
        for name in _NAMED_FONTS:
            tkfont.nametofont(name, root=self.root).configure(size=BODY)
        family = tkfont.nametofont("TkDefaultFont", root=self.root).actual("family")
        self.title_font = tkfont.Font(root=self.root, family=family, size=TITLE, weight="bold")
        self.subtitle_font = tkfont.Font(root=self.root, family=family, size=SUBTITLE)
        self.state_font = tkfont.Font(root=self.root, family=family, size=BODY, weight="bold")

    def _build(self) -> None:
        self.frame = tb.Frame(self.root, padding=MARGIN)
        self.frame.pack(fill="both", expand=True)

        header = tb.Frame(self.frame)
        header.pack(fill="x")
        titles = tb.Frame(header)
        titles.pack(side="left", fill="x", expand=True)
        self.title = tb.Label(titles, font=self.title_font)
        self.title.pack(anchor="w")
        self.subtitle = tb.Label(titles, font=self.subtitle_font, bootstyle="secondary")
        self.subtitle.pack(anchor="w")
        self.help_button = tb.Button(header, command=self.show_help, bootstyle="secondary-outline")
        self.help_button.pack(side="right")
        self.settings_button = tb.Button(
            header, command=self.show_settings, bootstyle="secondary-outline"
        )
        self.settings_button.pack(side="right", padx=(0, SPACE))
        self.state_label = tb.Label(self.frame, font=self.state_font)
        self.state_label.pack(anchor="w", pady=(GAP, 0))

        self.pages = tb.Frame(self.frame)
        self.pages.pack(fill="both", expand=True, pady=(GAP, 0))
        self.main = MainView(
            self.pages,
            on_add_files=self.add_files,
            on_add_folder=self.add_folder,
            on_remove=lambda path: self.presenter.remove_input(path),
            on_clear=lambda: self.presenter.clear_inputs(),
            on_next_to=lambda: self.presenter.choose_output_next_to(),
            on_pick_folder=self.pick_output_folder,
            on_convert=lambda: self.presenter.analyze(),
        )
        self.main.pack(fill="both", expand=True)

        self.message = tb.Label(self.frame, anchor="w", bootstyle="warning", wraplength=MIN_WIDTH)
        self.message.pack(fill="x", pady=(SPACE, 0))

        # Files and folders dropped anywhere on the window (tkinterdnd2, ADR-0026).
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self._dropped)
        self.root.bind("<Return>", lambda _event: self._primary())

    # --- Intents ---------------------------------------------------------------------------------

    def add_files(self) -> None:
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
        chosen = filedialog.askdirectory(
            parent=self.root, title=self._catalog().text("gui.main.pick_folder_title")
        )
        if chosen:
            self.presenter.add_paths([Path(chosen)])

    def pick_output_folder(self) -> None:
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
            self.presenter.confirm()

    def show_help(self) -> None:
        """The help window (T06)."""

    def show_settings(self) -> None:
        """The settings window (T06)."""

    def close(self) -> None:
        """Closing while working cancels first (the summary is still written), then closes."""
        if self.state is not None and self.state.state in {AppState.ANALYZING, AppState.CONVERTING}:
            self.presenter.cancel()
        self.scheduler.close()
        self.root.update_idletasks()  # Tk's own idle work (a theme change) runs before the end
        self.root.destroy()

    # --- The View the presenter draws on ---------------------------------------------------------

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self.scheduler.after(milliseconds, callback)

    def show_state(self, state: StateView) -> None:
        self.state = state
        self.state_label.configure(text=state.label)
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
            (self.settings_button, Action.SETTINGS),
            (self.help_button, Action.HELP),
        ):
            button.configure(state="normal" if action in state.enabled else "disabled")

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self.main.show_inputs(rows)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self.main.show_output_choice(choice)

    def show_scan(self, text: str) -> None:
        self.state_label.configure(text=text)

    def show_plan(self, plan: PlanView) -> None:
        self.last_plan = plan  # drawn by the plan view (T05)

    def show_progress(self, progress: ProgressView) -> None:
        self.last_progress = progress  # drawn by the progress view (T05)

    def show_result(self, result: ResultView) -> None:
        self.last_result = result  # drawn by the result view (T05)

    def show_message(self, text: str) -> None:
        self.message.configure(text=text)

    def show_welcome(self, steps: tuple[str, ...]) -> None:
        """The welcome dialog (T06)."""

    def apply_theme(self, theme: str) -> None:
        self.style.theme_use(THEMES.get(theme, THEMES["light"]))

    def apply_language(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.root.title(catalog.text("gui.app.title"))
        self.title.configure(text=catalog.text("gui.app.title"))
        self.subtitle.configure(text=catalog.text("gui.app.subtitle"))
        self.help_button.configure(text=catalog.text("gui.main.help"))
        self.settings_button.configure(text=catalog.text("gui.main.settings"))
        self.main.apply_language(catalog)

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


def main() -> None:
    """``clearmd-ttk``: the window, until it is closed."""
    import multiprocessing

    multiprocessing.freeze_support()  # a no-op unless running as a packaged executable
    app = TtkApp()
    app.start()
    app.root.mainloop()
