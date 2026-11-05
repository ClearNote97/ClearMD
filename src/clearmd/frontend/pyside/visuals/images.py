"""The pictures Qt draws from the assets: file icons, the logo and the window's icon."""

from functools import cache
from importlib.resources import files

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap

from clearmd.frontend.pyside.layout.units import ICON

ASSETS = files("clearmd.frontend") / "assets"


@cache
def icon(name: str) -> QIcon:
    """A file icon by its asset name (presenter.icons), sharp on high-density screens."""
    result = QIcon()
    folder = ASSETS / "icons"
    result.addFile(str(folder / f"{name}.png"), QSize(ICON, ICON))
    result.addFile(str(folder / f"{name}@2x.png"), QSize(2 * ICON, 2 * ICON))
    return result


def logo(name: str) -> QPixmap:
    return QPixmap(str(ASSETS / "logo" / f"{name}.png"))


def app_icon() -> QIcon:
    result = QIcon()
    for size in (16, 32, 48, 64, 128, 256):
        result.addFile(str(ASSETS / "logo" / f"clearmd-app-{size}.png"), QSize(size, size))
    return result
