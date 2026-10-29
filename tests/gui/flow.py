"""An animated capture of a real batch through the ttk GUI, for docs/ (feature 005).

Real documents (the test fixtures, renamed as a person would have them) are converted by the real
backend: choose, review, convert, results. Run in the dev container:

    uv run python tests/gui/flow.py --out docs/screenshots/005 --language es

Settings stay in memory: the user's settings file is never read or written.
"""

import argparse
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/: support.*, gui.*

from PIL import Image, ImageGrab  # noqa: E402
from support.display import virtual_display  # noqa: E402
from support.gui_fakes import MemoryBackend  # noqa: E402

from clearmd.backend.schemas.settings import Settings  # noqa: E402
from clearmd.frontend.presenter import AppState  # noqa: E402
from clearmd.frontend.ttk import TtkApp  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "documents"
WIDTH, HEIGHT = 1080, 720
DOCUMENTS = {  # fixture → the name it has in the demo folder
    "sample.pdf": "Informe anual 2026.pdf",
    "sample.docx": "Contrato de arriendo.docx",
    "sample.xlsx": "Ventas 2026.xlsx",
    "sample.pptx": "Presentación de resultados.pptx",
    "sample.epub": "Manual del usuario.epub",
    "sample.ipynb": "Análisis de datos.ipynb",
    "sample.html": "Noticia guardada.html",
    "sample.csv": "Inventario.csv",
    "sample.txt": "Notas de la reunión.txt",
    "encrypted.pdf": "Extracto protegido.pdf",
}


def grab(app: TtkApp) -> Image.Image:
    app.root.update()
    x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
    box = (x, y, x + app.root.winfo_width(), y + app.root.winfo_height())
    return ImageGrab.grab(bbox=box, xdisplay=os.environ["DISPLAY"]).convert("RGB")


def run(app: TtkApp, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.root.update()
        time.sleep(0.02)


def wait(app: TtkApp, states: set[AppState], frames: list[tuple[Image.Image, int]]) -> None:
    """Run until one of ``states``, capturing a frame every quarter second meanwhile."""
    deadline = time.monotonic() + 120
    while app.presenter.state not in states and time.monotonic() < deadline:
        run(app, 0.25)
        frames.append((grab(app), 250))


def flow(language: str, theme: str) -> list[tuple[Image.Image, int]]:
    home = Path(tempfile.mkdtemp(prefix="clearmd-flow-"))
    folder = home / "Documentos"
    folder.mkdir()
    for fixture, name in DOCUMENTS.items():
        shutil.copyfile(FIXTURES / fixture, folder / name)
    (folder / "Borrador.md").write_text("# Ya es Markdown\n", encoding="utf-8")

    settings = Settings(language=language, theme=theme, show_welcome=False)
    app = TtkApp(MemoryBackend(settings))
    app.root.geometry(f"{WIDTH}x{HEIGHT}+0+0")
    frames: list[tuple[Image.Image, int]] = []
    try:
        app.start()
        run(app, 0.4)
        frames.append((grab(app), 1200))
        app.presenter.add_paths([folder])
        run(app, 0.3)
        frames.append((grab(app), 2000))
        app.presenter.analyze()
        wait(app, {AppState.WAITING_DECISION}, frames)
        run(app, 0.3)
        frames.append((grab(app), 2800))
        app.presenter.go_to(3)
        run(app, 1.0)  # as a person would: the Convert page is seen, then pressed
        frames.append((grab(app), 1500))
        app.actions.primary.invoke()
        wait(app, {AppState.FINISHED, AppState.FINISHED_WITH_PROBLEMS}, frames)
        run(app, 0.4)
        frames.append((grab(app), 4000))
    finally:
        app.close()
        shutil.rmtree(home, ignore_errors=True)
    return frames


def main() -> int:
    parser = argparse.ArgumentParser(description="An animated capture of a real batch")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--language", default="es", choices=("en", "es"))
    parser.add_argument("--theme", default="light", choices=("light", "dark"))
    args = parser.parse_args()
    with virtual_display(WIDTH + 64, HEIGHT + 64) as display:
        if display is None:
            print("no display and no Xvfb", file=sys.stderr)
            return 1
        frames = flow(args.language, args.theme)
    target = args.out / f"flow-{args.theme}-{args.language}.gif"
    target.parent.mkdir(parents=True, exist_ok=True)
    pictures = [frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for frame, _ in frames]
    pictures[0].save(
        target,
        save_all=True,
        append_images=pictures[1:],
        duration=[duration for _, duration in frames],
        loop=0,
        optimize=True,
    )
    print(f"{target}  {len(frames)} frames, {target.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
