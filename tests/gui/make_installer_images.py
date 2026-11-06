"""Draws the Windows installer's pictures into packaging/installer/images (feature 019).

Run in the dev container (the letters use its DejaVu Sans Bold, as the logo does):

    uv run python tests/gui/make_installer_images.py
"""

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/: gui.drawing.*

from gui.drawing.installer import installer_images  # noqa: E402

TARGET = Path(__file__).resolve().parents[2] / "packaging" / "installer" / "images"


def files() -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for name, image in installer_images().items():
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        out[name] = buffer.getvalue()
    return out


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    for name, data in files().items():
        (TARGET / name).write_bytes(data)
        print(f"packaging/installer/images/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
