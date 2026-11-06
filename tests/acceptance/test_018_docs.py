"""Feature 018 — AC-12, its documents: the ADR, version 1.0.0, how to get the flet app, and the
screenshots (AC-11) made on CI by tests/gui/flet_screenshots.py."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ac_11_screenshots_of_every_screen_light_and_dark_english_and_spanish() -> None:
    shots = {path.name for path in (ROOT / "docs" / "screenshots" / "018").glob("*.png")}
    for screen in ("1-choose", "2-review", "3-convert", "4-results", "5-help", "6-settings"):
        for tag in ("light-en", "light-es", "dark-en", "dark-es"):
            assert f"{screen}-{tag}.png" in shots, f"{screen}-{tag}"
    script = (ROOT / "tests" / "gui" / "flet_screenshots.py").read_text(encoding="utf-8")
    assert "take_screenshot" in script
    workflow = (ROOT / ".github" / "workflows" / "flet-screenshots.yml").read_text(encoding="utf-8")
    assert "fetch_flet_client.py" in workflow and "flet_screenshots.py" in workflow


def test_ac_12_adr_version_and_how_to_get_it() -> None:
    adr = ROOT / "docs" / "decisions" / "0042-flet-gui-delivery.md"
    assert "Status:** accepted" in adr.read_text(encoding="utf-8")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert tuple(map(int, project["version"].split("."))) >= (1, 0, 0)
    for readme in ("README.md", "README.es.md"):
        text = (ROOT / readme).read_text(encoding="utf-8")
        assert "ClearMD-Flet-…-windows.zip" in text and "clearmd-flet" in text
    notes = (ROOT / "packaging" / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "ClearMD-Flet-1.0.0-windows.zip" in notes
