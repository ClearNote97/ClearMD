"""The pictures flet draws from the assets: file icons, the logo and the window's icon.

flet's window program reads pictures from the assets folder it is given at the start
(``ft.run(assets_dir=…)``): a picture is named by its path inside that folder. A module of its
own: the one place that knows the assets' layout.
"""

from importlib.resources import files
from pathlib import Path

ASSETS = Path(str(files("clearmd.frontend") / "assets"))


def icon_src(name: str) -> str:
    """A file icon by its asset name (presenter.icons): the sharp one, drawn at 16 px."""
    return f"icons/{name}@2x.png"


def logo_src(name: str) -> str:
    return f"logo/{name}.png"


def window_icon() -> str:
    """The window's icon, as a file (the operating system reads it, not flet's program)."""
    return str(ASSETS / "logo" / "clearmd.ico")


def asset_file(src: str) -> Path:
    """Where a picture named by ``src`` is on disk."""
    return ASSETS / src
