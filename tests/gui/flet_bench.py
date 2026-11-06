"""How much the flet window costs a conversion (v1.0.1): the same batch through the real flet
window (its window program drawing it) and through the command line, with every process's CPU.
Run on Windows CI by the "flet bench" workflow; the documents are the repository's fixtures.

    FLET_VIEW_PATH=build/flet-client/flet uv run python tests/gui/flet_bench.py <folder>
"""

import asyncio
import sys
import threading
import time
from pathlib import Path

import flet as ft
import psutil

from clearmd.frontend.flet.visuals.images import ASSETS
from clearmd.frontend.flet.window.flet_page import FletPage
from clearmd.frontend.flet.window.window import FletApp
from clearmd.frontend.presenter.ports import ApiBackend

SAMPLE_SECONDS = 0.5


class Sampler:
    """Every process under this one, its CPU every half second."""

    def __init__(self) -> None:
        self.samples: dict[str, list[float]] = {}
        self.stop = threading.Event()

    def run(self) -> None:
        me = psutil.Process()
        known: dict[int, psutil.Process] = {}
        while not self.stop.is_set():
            for process in [me, *me.children(recursive=True)]:
                if process.pid not in known:
                    known[process.pid] = process
                    process.cpu_percent(None)
            time.sleep(SAMPLE_SECONDS)
            for pid, process in list(known.items()):
                try:
                    name = f"{process.name()}:{pid}"
                    self.samples.setdefault(name, []).append(process.cpu_percent(None))
                except psutil.Error:
                    known.pop(pid)

    def report(self) -> str:
        return "\n".join(
            f"  {name}: mean {sum(v) / len(v):.0f}% max {max(v):.0f}%"
            for name, v in self.samples.items()
            if v
        )


async def batch(page: ft.Page, folder: Path) -> None:
    app = FletApp(FletPage(page), ApiBackend())
    app.start()
    await asyncio.sleep(3)
    if app.dialogs.current is not None:
        app.dialogs.current.close_dialog()
    app.presenter.add_paths([folder])
    app.presenter.press_primary()
    for _ in range(600):
        await asyncio.sleep(0.1)
        if app.presenter.page == 2 and app.presenter.state.value == "waiting_decision":
            break
    await asyncio.sleep(1)
    sampler = Sampler()
    threading.Thread(target=sampler.run, daemon=True).start()
    started = time.monotonic()
    app.presenter.confirm(True)
    for _ in range(6000):
        await asyncio.sleep(0.1)
        if app.presenter.page == 4:
            break
    sampler.stop.set()
    print(f"flet window: {time.monotonic() - started:.1f} s", flush=True)
    print(sampler.report(), flush=True)
    await page.window.destroy()


def main() -> int:
    folder = Path(sys.argv[1]).resolve()

    async def start(page: ft.Page) -> None:
        await batch(page, folder)

    ft.run(start, assets_dir=str(ASSETS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
