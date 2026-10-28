"""Screenshots of the ttk GUI for docs/ (feature 005, AC-21): every screen, light and dark, EN/ES.

Run in the dev container (a virtual display is started when there is none):

    uv run python tests/gui/screenshots.py --out docs/screenshots/005

The window is filled through the presenter with a fake backend: no document is converted.
"""

import argparse
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/: support.*

from PIL import ImageGrab  # noqa: E402
from support.display import virtual_display  # noqa: E402
from support.gui_fakes import FakeBackend  # noqa: E402

from clearmd.backend.schemas.settings import Settings  # noqa: E402
from clearmd.frontend.ttk import TtkApp  # noqa: E402

WIDTH, HEIGHT = 960, 720
INPUTS = [
    Path("/home/ana/Documentos/Informe anual 2026.pdf"),
    Path("/home/ana/Documentos/Tesis"),
    Path("/home/ana/Descargas/Contrato de arriendo.docx"),
    Path("/home/ana/Descargas/Notas de clase.odt"),
]


def settle(app: TtkApp, seconds: float = 0.3) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.root.update()
        time.sleep(0.02)


def capture(app: TtkApp, target: Path) -> None:
    settle(app)
    x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
    width, height = app.root.winfo_width(), app.root.winfo_height()
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height), xdisplay=os.environ["DISPLAY"])
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, optimize=True)
    print(f"{target}  {width}x{height}")


def window(language: str, theme: str) -> TtkApp:
    settings = Settings(language=language, theme=theme, show_welcome=False)
    app = TtkApp(FakeBackend(settings=settings))
    app.root.geometry(f"{WIDTH}x{HEIGHT}+0+0")
    app.start()
    return app


SCREENS: dict[str, Callable[[TtkApp], None]] = {
    "main-empty": lambda app: None,
    "main-with-inputs": lambda app: app.presenter.add_paths(INPUTS),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Screenshots of the ttk GUI")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with virtual_display(WIDTH + 64, HEIGHT + 64) as display:
        if display is None:
            print("no display and no Xvfb", file=sys.stderr)
            return 1
        for language in ("en", "es"):
            for theme in ("light", "dark"):
                for name, prepare in SCREENS.items():
                    app = window(language, theme)
                    prepare(app)
                    capture(app, args.out / f"{name}-{theme}-{language}.png")
                    app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
