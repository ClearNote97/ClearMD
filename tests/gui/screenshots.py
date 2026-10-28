"""Screenshots of the ttk GUI for docs/ (feature 005, AC-21): every screen, light and dark, EN/ES.

Run in the dev container (a virtual display is started when there is none):

    uv run python tests/gui/screenshots.py --out docs/screenshots/005

The window is driven through the presenter with a fake backend: no document is converted, but
the flow is the real one (the worker thread, the steps, the views).
"""

import argparse
import os
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/: support.*

from PIL import ImageGrab  # noqa: E402
from support.display import virtual_display  # noqa: E402
from support.gui_fakes import FakeBackend, planned  # noqa: E402

from clearmd.backend.schemas.errors import SkipReason  # noqa: E402
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem  # noqa: E402
from clearmd.backend.schemas.settings import Settings  # noqa: E402
from clearmd.frontend.presenter import AppState  # noqa: E402
from clearmd.frontend.ttk import TtkApp  # noqa: E402

WIDTH, HEIGHT = 1080, 720
# Real files and folders (a folder must exist to be shown as one), under a temporary home.
DEMO = Path(tempfile.gettempdir()) / "Usuarios" / "ana"
DOCUMENTS, DOWNLOADS = DEMO / "Documentos", DEMO / "Descargas"
INPUTS = [
    DOCUMENTS / "Informe anual 2026.pdf",
    DOCUMENTS / "Tesis",
    DOWNLOADS / "Contrato de arriendo.docx",
    DOCUMENTS / "Finanzas" / "Ventas 2026.xlsx",
    DOWNLOADS / "Notas de clase.odt",
    DOCUMENTS / "Tesis" / "Artículo.tex",
]
PLAN = BatchPlan(
    (
        planned("Informe anual 2026.pdf", folder=DOCUMENTS),
        planned("Capítulo 1.docx", folder=DOCUMENTS / "Tesis"),
        planned("Artículo.tex", folder=DOCUMENTS / "Tesis", exists=True),
        planned("Contrato de arriendo.docx", folder=DOWNLOADS),
        planned("Ventas 2026.xlsx", folder=DOCUMENTS / "Finanzas"),
        planned("Notas de clase.odt", folder=DOWNLOADS),
    ),
    (
        SkippedItem(DOCUMENTS / "Tesis" / "borrador.md", SkipReason.ALREADY_MARKDOWN),
        SkippedItem(DOCUMENTS / "Tesis" / "figuras.zip", SkipReason.ZIP_ARCHIVE),
    ),
    (),
)
FAILED = {"Contrato de arriendo.docx": OutcomeStatus.FAILED}


def demo_files() -> None:
    for path in INPUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix:
            path.write_bytes(b"")
        else:
            path.mkdir(exist_ok=True)


def settle(app: TtkApp, seconds: float = 0.3, until: Callable[[], bool] | None = None) -> None:
    deadline = time.monotonic() + (seconds if until is None else 10)
    while time.monotonic() < deadline:
        app.root.update()
        if until is not None and until():
            until = None
            deadline = time.monotonic() + seconds
        time.sleep(0.02)


def capture(app: TtkApp, target: Path) -> None:
    settle(app)
    x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
    width, height = app.root.winfo_width(), app.root.winfo_height()
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height), xdisplay=os.environ["DISPLAY"])
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, optimize=True)
    print(f"{target}  {width}x{height}")


def window(language: str, theme: str, fake: FakeBackend) -> TtkApp:
    fake.settings = Settings(
        language=language, theme=theme, show_welcome=False, open_output_when_done=False
    )
    app = TtkApp(fake)
    app.root.geometry(f"{WIDTH}x{HEIGHT}+0+0")
    app.start()
    return app


def choose(app: TtkApp) -> None:
    app.presenter.add_paths(INPUTS)


def to_review(app: TtkApp) -> None:
    app.presenter.add_paths(INPUTS)
    app.presenter.analyze()
    settle(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)


def to_results(app: TtkApp) -> None:
    to_review(app)
    app.presenter.confirm(overwrite=False)
    settle(app, until=partial(converted, app))


def converted(app: TtkApp) -> bool:
    return app.presenter.state is not AppState.CONVERTING


class Held:
    """Holds the batch on its third file, so the progress can be photographed mid-way."""

    def __init__(self) -> None:
        self.gate = threading.Event()
        self.files = 0

    def __call__(self) -> None:
        self.files += 1
        if self.files == 3:
            self.gate.wait(10)


def converting(app: TtkApp, held: Held) -> None:
    to_review(app)
    app.presenter.confirm(overwrite=False)
    settle(app, until=lambda: held.files == 3)


def main() -> int:
    parser = argparse.ArgumentParser(description="Screenshots of the ttk GUI")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    demo_files()
    with virtual_display(WIDTH + 64, HEIGHT + 64) as display:
        if display is None:
            print("no display and no Xvfb", file=sys.stderr)
            return 1
        for language in ("en", "es"):
            for theme in ("light", "dark"):
                shots: list[tuple[str, FakeBackend, Callable[[TtkApp], None]]] = [
                    ("1-choose-empty", FakeBackend(plan=PLAN), lambda app: None),
                    ("1-choose", FakeBackend(plan=PLAN), choose),
                    ("2-review", FakeBackend(plan=PLAN), to_review),
                    ("4-results", FakeBackend(plan=PLAN, statuses=FAILED), to_results),
                    ("4-results-all-good", FakeBackend(plan=BatchPlan(PLAN.conversions, (), ())),
                     to_results),
                ]  # fmt: skip
                for name, fake, prepare in shots:
                    app = window(language, theme, fake)
                    prepare(app)
                    capture(app, args.out / f"{name}-{theme}-{language}.png")
                    app.close()
                held = Held()
                app = window(language, theme, FakeBackend(plan=PLAN, before_finish=held))
                converting(app, held)
                capture(app, args.out / f"3-convert-{theme}-{language}.png")
                held.gate.set()
                settle(app, until=partial(converted, app))
                app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
