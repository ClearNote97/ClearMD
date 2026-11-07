"""Feature 018 — The window, its steps and its look (AC-01, AC-06); spec/features/018_*/spec.md.

The flet window is built on a page that is not flet's (no screen), on the presenter's fake backend.
"""

import tomllib
from collections.abc import Iterator
from dataclasses import replace

import flet as ft
import pytest
from support.flet_acceptance import QUIET, ROOT, Window, click, page_of, walk, windows
from support.gui_fakes import FakeBackend

import clearmd.frontend.presenter.presenter as presenter_module
from clearmd.frontend.design.metrics import COMPACT_RAIL_WIDTH, GUTTER, RAIL_WIDTH, on_grid
from clearmd.frontend.design.palette import DARK, LIGHT, Palette
from clearmd.frontend.design.typography import BODY
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.visuals.images import asset_file
from clearmd.frontend.flet.visuals.look import button_style
from clearmd.frontend.flet.visuals.theme import ROLES
from clearmd.frontend.presenter.state import HOME, STEPS
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def test_ac_01_clearmd_flet_is_a_script_and_opens_the_window_on_the_presenter(
    flet_window: Window,
) -> None:
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert scripts["project"]["gui-scripts"]["clearmd-flet"] == "clearmd.frontend.flet:main"
    app = flet_window(FakeBackend(settings=QUIET))
    assert page_of(app).root is app.root  # on the page
    assert asset_file(str(app.rail.mark.src)).is_file()  # the logo
    assert [span.text for span in app.rail.wordmark.spans or []] == ["Clear", "·", "MD"]
    assert app.rail.home_text() == "> Home"  # it opens on Home (feature 023)
    assert app.rail.step_texts() == ["Choose", "Review", "Convert", "Results"]
    assert app.presenter.page == HOME and app.presenter.version in str(app.rail.foot.value)
    app.presenter.go_to(1)
    assert app.rail.step_texts() == ["> Choose", "Review", "Convert", "Results"]


def test_ac_01_every_step_opens_by_click_and_by_ctrl_1_to_4(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    for step in (4, 2, 3, 1):
        click(app.rail.steps[step - 1])
        assert app.presenter.page == step
        assert [page.visible for page in app.pages] == [n == step for n in (1, 2, 3, 4)]
    for key in ("3", "4", "2", "1"):
        page_of(app).press(key, ctrl=True)
        assert app.presenter.page == int(key)
    page_of(app).press("3")  # without Ctrl: nothing
    assert app.presenter.page == 1 and app.rail.step_texts()[0] == "> Choose"
    assert len(app.rail.steps) == len(STEPS) == 4


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_01_the_texts_come_from_the_catalogs(flet_window: Window, language: str) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    catalog = load_catalog(language)
    app.presenter.go_to(1)  # from Home (feature 023)
    assert page_of(app).title == catalog.text("gui.app.title")
    assert app.surface.title.value == catalog.text("gui.page.choose_title")
    assert app.surface.eyebrow.value == catalog.text("gui.steps.counter", step=1, total=4).upper()
    assert app.actions.primary.content == catalog.text("gui.nav.next")
    assert app.main.add_files.content == catalog.text("gui.main.add_files")
    assert app.rail.settings.tooltip == catalog.text("gui.main.settings")
    assert [text.removeprefix("> ") for text in app.rail.step_texts()] == [
        catalog.text(f"gui.steps.{name}") for name in STEPS
    ]


def scheme_matches(theme: ft.Theme | None, palette: Palette) -> bool:
    assert theme is not None and theme.color_scheme is not None
    return all(
        getattr(theme.color_scheme, slot) == colour(palette) for slot, colour in ROLES.values()
    )


@pytest.mark.parametrize(("system", "palette"), [("dark", DARK), ("light", LIGHT)])
def test_ac_06_the_theme_follows_the_system_by_default(
    flet_window: Window, monkeypatch: pytest.MonkeyPatch, system: str, palette: Palette
) -> None:
    monkeypatch.setattr(presenter_module, "detect_system_theme", lambda: system)
    app = flet_window(FakeBackend(settings=QUIET))  # theme: "system"
    page = page_of(app)
    assert app.shown.palette is palette and page.themes is not None
    assert page.mode is (ft.ThemeMode.DARK if system == "dark" else ft.ThemeMode.LIGHT)
    assert scheme_matches(page.themes[0], LIGHT) and scheme_matches(page.themes[1], DARK)


def test_ac_06_an_explicit_theme_wins_and_applies_at_once(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, theme="dark")))
    assert app.shown.palette is DARK and page_of(app).mode is ft.ThemeMode.DARK
    app.presenter.save_settings(replace(app.presenter.settings, theme="light"))
    assert app.shown.palette is LIGHT and page_of(app).mode is ft.ThemeMode.LIGHT


def grid_problems(root: ft.BaseControl) -> list[str]:
    """Paddings, gaps and text sizes off the rules: 8 px grid, text never below 14 px."""
    found = []
    for control in walk(root):
        for name in ("padding", "content_padding", "title_padding", "actions_padding"):
            padding = getattr(control, name, None)
            if isinstance(padding, ft.Padding):
                sides = (padding.left, padding.top, padding.right, padding.bottom)
                found += [f"{control} {name} {side}" for side in sides if not on_grid(int(side))]
        if isinstance(control, ft.Row | ft.Column | ft.ListView) and not on_grid(
            int(control.spacing)
        ):
            found.append(f"{control} spacing {control.spacing}")
        if isinstance(control, ft.Text) and (control.size or 0) < BODY:
            found.append(f"{control.value!r} size {control.size}")
    return found


def test_ac_06_the_8_px_grid_14_px_text_and_one_primary_action(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    assert grid_problems(app.root) == []
    for open_dialog in (app.dialogs.show_help, app.dialogs.show_settings, app.dialogs.convert_more):
        open_dialog()
        assert app.dialogs.current is not None
        assert grid_problems(app.dialogs.current.control) == []
        app.dialogs.current.close_dialog()
    primary = button_style("primary")
    for page in (1, 2, 3, 4):  # one primary action per screen: the bar's
        app.presenter.go_to(page)
        primaries = [
            c
            for c in walk(app.root, visible=True)
            if isinstance(c, ft.Button) and c.style == primary
        ]
        assert primaries == [app.actions.primary]


def test_ac_06_the_page_and_the_rail_share_one_gutter(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    outer = app.root.padding
    assert isinstance(outer, ft.Padding)
    assert (outer.left, outer.top, outer.right, outer.bottom) == (GUTTER, GUTTER, 0, GUTTER)
    inside = app.panel.padding
    assert isinstance(inside, ft.Padding) and inside.left == inside.top == GUTTER
    beside = app.surface.control.controls[-1]  # the header and the page, beside the rail
    assert isinstance(beside, ft.Container) and isinstance(beside.padding, ft.Padding)
    assert beside.padding.left == beside.padding.right == GUTTER


def test_ac_06_a_narrow_window_gets_the_compact_rail(flet_window: Window) -> None:
    app: FletApp = flet_window(FakeBackend(settings=QUIET))
    page_of(app).resize(900, 700)
    assert app.rail.compact and app.rail.control.width == COMPACT_RAIL_WIDTH
    foot = str(app.rail.foot.value)
    assert app.presenter.version in foot and "\n" not in foot and not app.rail.wordmark.visible
    page_of(app).resize(1200, 700)
    assert not app.rail.compact and app.rail.control.width == RAIL_WIDTH
