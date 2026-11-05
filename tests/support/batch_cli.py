"""Helpers shared by the feature 001 acceptance tests."""

from pathlib import Path


def _tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _summary(folder: Path) -> str:
    return (folder / "ClearMD_Output" / "Resumen_ClearMD.md").read_text(encoding="utf-8")


def _settings(text: str) -> None:
    from clearmd.backend.api import settings_path

    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
