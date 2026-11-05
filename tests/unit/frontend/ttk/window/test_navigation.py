"""Navigation (feature 007, ADR-0029)."""

from functools import partial
from pathlib import Path

from support.gui_close import shut
from support.gui_fakes import FakeBackend
from support.ttk_unit import confirm, convert_more, pump, shown

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.ttk import TtkApp

# --- Navigation (feature 007, ADR-0029) ----------------------------------------------------------


def click_step(app: TtkApp, step: int) -> None:
    rail = app.rail
    x1, y1, x2, y2 = rail.bbox(f"step{step}")
    rail.event_generate("<Button-1>", x=(x1 + x2) // 2, y=(y1 + y2) // 2)
    pump(app, seconds=0.05)


def test_every_step_opens_from_the_rail_and_the_keyboard(app: TtkApp) -> None:
    click_step(app, 4)
    assert shown(app) is app.results and app.rail.step_texts()[3] == "> Results"
    click_step(app, 2)
    assert shown(app) is app.review
    app.root.focus_force()
    app.root.update()
    app.root.event_generate("<Control-Key-3>", when="tail")
    pump(app, until=lambda: app.presenter.page == 3, seconds=1)
    assert shown(app) is app.converting


def test_a_disabled_primary_says_why(app: TtkApp) -> None:
    assert app.actions.primary.instate(["disabled"])
    assert app.actions.primary.cget("text") == "Next"
    assert app.actions.hint.cget("text") == "Add at least one file or folder."
    app.presenter.go_to(4)
    assert app.actions.primary.cget("text") == "Open results folder"
    assert "Nothing chosen yet" in app.actions.hint.cget("text")  # what is missing first (011)
    app.presenter.add_paths([Path("/docs/a.pdf")])
    assert "Convert something first" in app.actions.hint.cget("text")


def test_convert_shows_what_is_ready_before_it_starts(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    app.actions.primary.invoke()
    pump(app, until=lambda: app.presenter.page == 2)
    app.actions.primary.invoke()  # Next on Review
    assert shown(app) is app.converting
    assert app.converting.ready_count.cget("text") == "Ready to convert: 1"
    assert app.actions.primary.cget("text") == "Convert"
    assert app.actions.secondary.cget("text") == "Back"


def on_page(app: TtkApp, page: int) -> bool:
    return app.presenter.page == page


def test_convert_more_asks_whether_to_keep_the_files(display: str, tmp_path: Path) -> None:
    for keep, expected in ((True, [f"{tmp_path.name}/"]), (False, [])):
        app = TtkApp(FakeBackend(settings=Settings(show_welcome=False)))
        try:
            app.start()
            app.presenter.add_paths([tmp_path])
            app.actions.primary.invoke()
            pump(app, until=partial(on_page, app, 2))
            confirm(app)
            pump(app, until=partial(on_page, app, 4))
            assert app.actions.secondary.cget("text") == "Convert more"
            assert str(app.actions.secondary.cget("style")).startswith("Strong")
            convert_more(app, keep=keep)
            assert shown(app) is app.main and app.main.inputs.names() == expected
        finally:
            shut(app)


def test_a_narrow_window_gets_the_compact_rail_and_the_version_is_shown(app: TtkApp) -> None:
    assert app.rail._version.startswith(("v", "dev"))
    app.root.geometry("820x600")
    pump(app, until=lambda: app.rail._compact, seconds=2)
    assert app.rail._compact and app.rail.settings.cget("text") == "⚙"
    app.root.geometry("1200x720")
    pump(app, until=lambda: not app.rail._compact, seconds=2)
    assert not app.rail._compact
