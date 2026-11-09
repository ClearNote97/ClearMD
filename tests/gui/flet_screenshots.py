"""Screenshots of the flet GUI for docs/ (feature 018, AC-11): every screen, light and dark,
English and Spanish, drawn by flet's real window program with the presenter's fake backend (the
same demo as ttk's and Qt's). flet draws in its own program, so this runs on a machine with a
screen: the "flet screenshots" workflow on Windows, with the pinned program fetched first.

    uv run python packaging/fetch_flet_client.py
    FLET_VIEW_PATH=build/flet-client/flet uv run python tests/gui/flet_screenshots.py \\
        --out docs/screenshots/018 --theme light --language en
"""

import argparse
import asyncio
import ctypes
import sys
import threading
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/: support.*, gui.*

import flet as ft  # noqa: E402
import support.ttk_demo as demo  # noqa: E402
from support.gui_fakes import FakeBackend  # noqa: E402

from clearmd.backend.schemas.models import BatchPlan, PlanWarning  # noqa: E402
from clearmd.backend.schemas.settings import Settings  # noqa: E402
from clearmd.frontend.design.metrics import START_HEIGHT, START_WIDTH  # noqa: E402
from clearmd.frontend.flet.layout.units import FRAME_HEIGHT, FRAME_WIDTH  # noqa: E402
from clearmd.frontend.flet.visuals.images import ASSETS  # noqa: E402
from clearmd.frontend.flet.window.flet_page import FletPage  # noqa: E402
from clearmd.frontend.flet.window.window import FletApp  # noqa: E402
from clearmd.frontend.presenter.state import Tool  # noqa: E402
from clearmd.i18n import load_catalog  # noqa: E402

COMPACT = (900, 640)  # below 1000 px the rail is compact (feature 007)


class Shooter:
    def __init__(self, page: ft.Page, out: Path, tag: str) -> None:
        self.page, self.out, self.tag = page, out, tag

    async def shot(self, name: str, settle: float = 0.9) -> None:
        # The script calls the presenter outside flet's events: nothing is sent to flet's program
        # until a window callback runs (FletPage.post). A change that stays on the same page posts
        # none (Split's step 1 to Merge's, 026), so the page is sent here, before every shot.
        self.page.update()
        park_pointer()
        # Past the primary action's pause after a page change (F-1), and flet's own drawing.
        await asyncio.sleep(settle)
        picture = await self.page.take_screenshot()
        (self.out / f"{name}-{self.tag}.png").write_bytes(picture)

    @staticmethod
    async def until(done: Callable[[], bool], seconds: float = 10) -> None:
        for _ in range(int(seconds / 0.1)):
            if done():
                return
            await asyncio.sleep(0.1)


def park_pointer() -> None:
    """The CI's pointer rests in the middle of the screen, over the page, and flet draws the control
    under it hovered: "Clear All" looked pressed in Merge's shot (032). It goes to the screen's
    corner, over no control."""
    if sys.platform == "win32":
        ctypes.windll.user32.SetCursorPos(0, 0)


async def close_dialog(app: FletApp) -> None:
    """As Esc does: the dialog's own close, then a moment for flet's program to take it away."""
    dialog = app.dialogs.current
    if dialog is not None:
        dialog.close_dialog()
        await asyncio.sleep(0.5)


def large_pdf_plan() -> BatchPlan:
    """The demo's plan with its PDF over the time limit: Review offers to split it (025)."""
    pdf = demo.PLAN.conversions[0]
    slow = PlanWarning(replace(pdf, cost=2400.0), 2400.0, 600.0)
    return replace(demo.PLAN, warnings=(slow,))


async def screens(page: ft.Page, out: Path, theme: str, language: str) -> None:
    shooter = Shooter(page, out, f"{theme}-{language}")
    held = threading.Event()
    settings = Settings(
        show_welcome=False, open_output_when_done=False, theme=theme, language=language
    )
    fake = FakeBackend(settings=settings, plan=demo.PLAN, statuses=demo.FAILED)
    page.enable_screenshots = True
    page.window.width, page.window.height = START_WIDTH + FRAME_WIDTH, START_HEIGHT + FRAME_HEIGHT
    app = FletApp(FletPage(page), fake)
    app.start()
    await shooter.shot("0-home")  # the window opens on Home (feature 023)
    app.presenter.choose_tool(Tool.CONVERT)
    await shooter.shot("1-choose-empty")
    app.presenter.add_paths(demo.INPUTS)
    await shooter.shot("1-choose")
    app.presenter.press_primary()
    await shooter.until(lambda: app.presenter.page == 2)
    await shooter.shot("2-review")
    app.presenter.go_to(3)
    await shooter.shot("3-convert-ready")

    def hold() -> None:  # the batch waits here: the progress stays on screen for the shot
        held.wait(20)

    fake.before_finish = hold
    app.presenter.confirm(False)
    await shooter.until(lambda: app.presenter.state.value == "converting")
    await shooter.shot("3-convert")
    held.set()
    await shooter.until(lambda: app.presenter.page == 4)
    await shooter.shot("4-results")
    app.dialogs.what_next()  # Results' "What Next?": the three tools and the box (033)
    await shooter.shot("4-what-next")
    await close_dialog(app)
    dialogs = (("5-help", app.dialogs.show_help), ("6-settings", app.dialogs.show_settings))
    for name, show in dialogs:
        show()
        await shooter.shot(name)
        await close_dialog(app)
    catalog = load_catalog(language)
    app.dialogs.welcome(tuple(catalog.text(f"gui.welcome.step{n}") for n in (1, 2, 3)))
    await shooter.shot("0-welcome")
    await close_dialog(app)
    app.presenter.choose_tool(Tool.SPLIT)  # Split's step 1, a PDF listed: How to Split (023)
    app.presenter.clear_inputs()
    app.presenter.add_paths([demo.INPUTS[0]])
    await shooter.shot("1-choose-split")
    # Merge's step 1, three files in their order, each with its ▲ ▼ (026, 032)
    app.presenter.choose_tool(Tool.MERGE)
    app.presenter.clear_inputs()
    app.presenter.add_paths([demo.INPUTS[0], demo.INPUTS[2], demo.INPUTS[4]])
    await shooter.shot("1-choose-merge")
    if theme == "light":  # Clear All: the line and Undo (039), as Qt's 1-choose-cleared-*
        app.presenter.clear_inputs()
        await shooter.shot("1-choose-cleared")
    app.presenter.choose_tool(Tool.CONVERT)
    app.presenter.add_paths(demo.INPUTS)
    fake.plan = large_pdf_plan()  # Review offers to split the large PDF (025)
    app.presenter.press_primary()
    await shooter.until(lambda: app.presenter.page == 2)
    await shooter.shot("2-review-split-offer")
    fake.plan = demo.PLAN
    page.window.width, page.window.height = COMPACT[0] + FRAME_WIDTH, COMPACT[1] + FRAME_HEIGHT
    app.presenter.go_to(1)
    await shooter.shot("1-choose-compact")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--theme", choices=("light", "dark"), required=True)
    parser.add_argument("--language", choices=("en", "es"), required=True)
    arguments = parser.parse_args()
    arguments.out.mkdir(parents=True, exist_ok=True)
    demo.demo_files()

    async def start(page: ft.Page) -> None:
        try:
            await screens(page, arguments.out, arguments.theme, arguments.language)
        finally:
            await page.window.destroy()

    ft.run(start, assets_dir=str(ASSETS))
    print(f"{len(list(arguments.out.glob('*.png')))} screenshots in {arguments.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
