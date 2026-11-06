"""Feature 016 — the criteria about its documents (spec/features/016_*/spec.md): the screenshots,
the ADR, the version and how to get the app."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "docs" / "screenshots" / "016"
SCREENS = ("0-welcome", "1-choose", "1-choose-empty", "1-choose-compact", "2-review", "3-convert",
           "3-convert-ready", "4-results", "5-help", "6-settings")  # fmt: skip


def test_ac_10_screenshots_of_every_screen_in_both_themes_and_languages() -> None:
    for screen in SCREENS:
        for theme in ("light", "dark"):
            for language in ("en", "es"):
                assert (SHOTS / f"{screen}-{theme}-{language}.png").is_file(), screen
    assert (ROOT / "tests" / "gui" / "pyside_screenshots.py").is_file()


def test_ac_11_adr_version_and_how_to_get_it() -> None:
    adr = ROOT / "docs" / "decisions" / "0038-pyside-gui-delivery.md"
    assert adr.exists() and "Status:** accepted" in adr.read_text(encoding="utf-8")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert tuple(map(int, project["version"].split("."))) >= (0, 11, 0)
    for readme in ("README.md", "README.es.md"):
        text = (ROOT / readme).read_text(encoding="utf-8")
        assert "ClearMD-Qt-…-windows.zip" in text and "clearmd-pyside" in text
    notes = (ROOT / "packaging" / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "ClearMD-Qt-0.11.0-windows.zip" in notes
