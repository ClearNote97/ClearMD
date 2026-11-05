"""Draws ClearMD's logo and file icons (ADR-0027): one geometry, written as SVG and as PNG.

Run in the dev container (the icons' letters use its DejaVu Sans Bold):

    uv run python tests/gui/make_assets.py

``tests/unit/frontend/test_assets.py`` checks that the committed files match what this draws.
"""

import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/: gui.drawing.*

from gui.drawing.file_icons import FILE_ICONS, ICON_SIZE, file_icon_png, folder_png  # noqa: E402
from gui.drawing.mark import APP_SIZES, MARK_SIZES, MARKS, app_png, app_svg, mark_png, mark_svg  # noqa: E402
from gui.drawing.splash import ico_bytes, splash_png  # noqa: E402

ASSETS = Path(__file__).resolve().parents[2] / "src" / "clearmd" / "frontend" / "assets"


def _png_bytes(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()


def assets() -> dict[str, bytes]:
    """Every asset file, by its path under ``frontend/assets``."""
    files: dict[str, bytes] = {}
    for colours in MARKS:
        files[f"logo/clearmd-{colours.name}.svg"] = mark_svg(colours).encode()
        for size in MARK_SIZES:
            files[f"logo/clearmd-{colours.name}-{size}.png"] = _png_bytes(mark_png(colours, size))
    files["logo/clearmd-app.svg"] = app_svg().encode()
    files["logo/clearmd.ico"] = ico_bytes()
    files["logo/splash.png"] = _png_bytes(splash_png())
    for size in APP_SIZES:
        files[f"logo/clearmd-app-{size}.png"] = _png_bytes(app_png(size))
    for icon in FILE_ICONS:
        files[f"icons/{icon.name}.png"] = _png_bytes(file_icon_png(icon, ICON_SIZE))
        files[f"icons/{icon.name}@2x.png"] = _png_bytes(file_icon_png(icon, 2 * ICON_SIZE))
    files["icons/folder.png"] = _png_bytes(folder_png(ICON_SIZE))
    files["icons/folder@2x.png"] = _png_bytes(folder_png(2 * ICON_SIZE))
    return files


def main() -> int:
    for relative, data in assets().items():
        target = ASSETS / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(target.relative_to(ASSETS.parents[3]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
