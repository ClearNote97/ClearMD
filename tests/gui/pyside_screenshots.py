"""Screenshots of the PySide6 GUI for docs/ (feature 016, AC-10): every screen, light and dark,
English and Spanish, drawn offscreen with the presenter's fake backend (the same demo as ttk's);
the start screen and Split's step 1 since feature 023; Review's offer to split since 025;
Merge's step 1 since 026; What Next? and Split at 800 px since 032;
Settings on a 1366 x 768 screen since 039.

    uv run python tests/gui/pyside_screenshots.py --out docs/screenshots/016
"""

import argparse
import sys
import threading
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/: support.*, gui.*

import support.ttk_demo as demo  # noqa: E402
from support.gui_fakes import FakeBackend  # noqa: E402
from support.pyside_acceptance import open_window, pump, shut  # noqa: E402 -- sets offscreen

import clearmd.frontend.pyside.components.dialog as dialog_module  # noqa: E402
from clearmd.backend.schemas.models import PlanWarning  # noqa: E402
from clearmd.backend.schemas.settings import Settings  # noqa: E402
from clearmd.frontend.design.metrics import START_HEIGHT, START_WIDTH  # noqa: E402
from clearmd.frontend.presenter.state import Tool  # noqa: E402
from clearmd.frontend.pyside import PySideApp  # noqa: E402
from clearmd.i18n import load_catalog  # noqa: E402

COMPACT = (900, 640)  # below 1000 px the rail is compact (feature 007)
LAPTOP = 768 - 40  # a 1366 x 768 screen less its taskbar: the room a dialog has (039)
NARROWEST = (800, 600)  # the window's least width (032): Split's cuts and the list stay usable


def shot(app: PySideApp, target: Path) -> None:
    pump(app, seconds=0.8)  # past the primary action's pause after a page change (F-1)
    app.window.grab().save(str(target))


def dialog_shot(app: PySideApp, target: Path) -> None:
    pump(app, seconds=0.5)
    if app.dialogs.current is not None:
        app.dialogs.current.grab().save(str(target))
        app.dialogs.current.close_dialog()
        pump(app, seconds=0.2)


def screens(out: Path, theme: str, language: str) -> None:
    tag = f"{theme}-{language}"
    held = threading.Event()
    settings = Settings(
        show_welcome=False, open_output_when_done=False, theme=theme, language=language
    )
    fake = FakeBackend(settings=settings, plan=demo.PLAN, statuses=demo.FAILED)
    app = open_window(fake)
    app.window.resize(START_WIDTH, START_HEIGHT)
    shot(app, out / f"0-home-{tag}.png")
    app.presenter.choose_tool(Tool.CONVERT)
    shot(app, out / f"1-choose-empty-{tag}.png")
    app.presenter.add_paths(demo.INPUTS)
    shot(app, out / f"1-choose-{tag}.png")
    app.presenter.press_primary()
    pump(app, until=lambda: app.presenter.page == 2, seconds=5)
    shot(app, out / f"2-review-{tag}.png")
    app.presenter.go_to(3)
    shot(app, out / f"3-convert-ready-{tag}.png")

    def hold() -> None:  # the batch waits here: the progress stays on screen for the shot
        held.wait(20)

    fake.before_finish = hold
    app.presenter.confirm(False)
    pump(app, until=lambda: app.presenter.state.value == "converting", seconds=5)
    shot(app, out / f"3-convert-{tag}.png")
    held.set()
    pump(app, until=lambda: app.presenter.page == 4, seconds=10)
    shot(app, out / f"4-results-{tag}.png")
    app.dialogs.what_next()  # "What Next?" (032, its tiles since 033)
    dialog_shot(app, out / f"4-what-next-{tag}.png")
    app.dialogs.show_help()
    dialog_shot(app, out / f"5-help-{tag}.png")
    app.dialogs.show_settings()
    dialog_shot(app, out / f"6-settings-{tag}.png")
    room = dialog_module.screen_room
    dialog_module.screen_room = lambda widget: LAPTOP - dialog_module.SCREEN_MARGIN
    app.dialogs.show_settings()  # a 1366 x 768 screen: the settings scroll, Save stays (039)
    dialog_shot(app, out / f"6-settings-1366x768-{tag}.png")
    dialog_module.screen_room = room
    catalog = load_catalog(language)
    app.dialogs.welcome(tuple(catalog.text(f"gui.welcome.step{n}") for n in (1, 2, 3)))
    dialog_shot(app, out / f"0-welcome-{tag}.png")
    app.window.resize(*COMPACT)
    app.presenter.go_to(1)
    shot(app, out / f"1-choose-compact-{tag}.png")
    app.window.resize(START_WIDTH, START_HEIGHT)
    app.presenter.choose_tool(Tool.SPLIT)
    app.presenter.clear_inputs()
    app.presenter.add_paths([path for path in demo.INPUTS if path.suffix == ".pdf"])
    shot(app, out / f"1-choose-split-{tag}.png")
    app.presenter.add_paths([path for path in demo.INPUTS if path.suffix == ".xlsx"])
    app.window.resize(*NARROWEST)
    shot(app, out / f"1-choose-split-800-{tag}.png")
    app.window.resize(START_WIDTH, START_HEIGHT)
    app.presenter.choose_tool(Tool.MERGE)
    app.presenter.clear_inputs()
    app.presenter.add_paths([path for path in demo.INPUTS if path.suffix][:3])
    shot(app, out / f"1-choose-merge-{tag}.png")
    app.presenter.clear_inputs()  # Clear All: the line and Undo (039)
    shot(app, out / f"1-choose-cleared-{tag}.png")
    shut(app)


def offer_shot(out: Path, theme: str, language: str) -> None:
    """Review with "Split the Large PDFs" (feature 025): the demo's PDF over the time limit."""
    first, *rest = demo.PLAN.conversions
    big = PlanWarning(replace(first, cost=2400.0), 2400.0, 600.0)
    plan = replace(demo.PLAN, conversions=(big.item, *rest), warnings=(big,))
    settings = Settings(
        show_welcome=False, open_output_when_done=False, theme=theme, language=language
    )
    app = open_window(FakeBackend(settings=settings, plan=plan))
    app.window.resize(START_WIDTH, START_HEIGHT)
    app.presenter.choose_tool(Tool.CONVERT)
    app.presenter.add_paths(demo.INPUTS)
    app.presenter.press_primary()
    pump(app, until=lambda: app.presenter.page == 2, seconds=5)
    shot(app, out / f"2-review-split-offer-{theme}-{language}.png")
    shut(app)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    demo.demo_files()
    for theme in ("light", "dark"):
        for language in ("en", "es"):
            screens(out, theme, language)
            offer_shot(out, theme, language)
    print(f"{len(list(out.glob('*.png')))} screenshots in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
