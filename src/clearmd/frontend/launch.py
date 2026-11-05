"""How a GUI executable starts (ADR-0028, feature 007): the splash's later steps and the short
smoke run CI makes. The first step stays in ``packaging/launch_gui.py``: it runs before ClearMD
is imported. A module of its own: every GUI's ``main`` reads it."""

from collections.abc import Sequence

BUILDING_TEXT = "Loading · Cargando… 85 %"  # ClearMD imported: the window is being built
LOADED_TEXT = "Loading · Cargando… 100 %"  # the window is built
SMOKE_SECONDS = 3  # ``--smoke``: the executable's own check in CI (ADR-0028)


def is_smoke(arguments: Sequence[str]) -> bool:
    """Whether the window should open and close by itself after ``SMOKE_SECONDS``."""
    return "--smoke" in arguments


def splash_text(text: str) -> None:
    """The splash's line, inside the executable only (PyInstaller's ``pyi_splash``)."""
    try:
        import pyi_splash  # type: ignore[import-not-found,import-untyped,unused-ignore]  # frozen
    except ImportError:
        return
    pyi_splash.update_text(text)


def close_splash() -> None:
    """The executable shows a splash while it unpacks (PyInstaller); the window replaces it."""
    try:
        import pyi_splash  # type: ignore[import-not-found,import-untyped,unused-ignore]  # frozen only
    except ImportError:
        return
    pyi_splash.close()
