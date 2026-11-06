"""Feature 017 — the criterion about its documents (spec/features/017_*/spec.md): the ADR, the
version, and how to install and uninstall."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ac_07_adr_version_and_how_to_install_and_uninstall() -> None:
    adr = ROOT / "docs" / "decisions" / "0040-windows-installer.md"
    assert adr.exists() and "Status:** accepted" in adr.read_text(encoding="utf-8")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["version"] == "0.12.0"
    for readme, uninstall in (("README.md", "Installed apps"), ("README.es.md", "Aplicaciones")):
        text = (ROOT / readme).read_text(encoding="utf-8")
        assert "ClearMD-Setup-….exe" in text and uninstall in text
    notes = (ROOT / "packaging" / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "ClearMD-Setup-0.12.0.exe" in notes
