"""Feature 001 — the settings file and the flags that override it (spec/features/001_*/spec.md)."""

from pathlib import Path

import pytest
from support import put
from support.batch_cli import _settings, _tree

from clearmd.frontend.cli import main


def test_ac_03_the_recursive_setting_is_honored(workdir: Path) -> None:
    _settings("recursive = false\n")
    project = workdir / "project"
    put(project, "sample.txt", "top.txt")
    put(project, "sample.txt", "sub/inner.txt")
    assert main([str(project), "--quiet"]) == 0
    assert _tree(workdir / "ClearMD_Output" / "OutputMD") == ["project", "project/top.md"]


def test_ac_18_the_existing_output_setting_applies_without_asking(workdir: Path) -> None:
    source = put(workdir, "sample.txt", "notes.txt")
    assert main([str(source), "--quiet"]) == 0
    output = workdir / "ClearMD_Output" / "OutputMD" / "notes.md"
    output.write_text("edited by hand", encoding="utf-8")
    _settings('on_existing_output = "skip"\n')
    assert main([str(source), "--quiet"]) == 0
    assert output.read_text(encoding="utf-8") == "edited by hand"
    _settings('on_existing_output = "overwrite"\n')
    assert main([str(source), "--quiet"]) == 0
    assert output.read_text(encoding="utf-8") != "edited by hand"


def test_ac_33_a_broken_or_invalid_settings_file_never_stops_the_app(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = put(workdir, "sample.txt", "notes.txt")
    _settings('language = "fr"\ncolour = "blue"\n')
    assert main([str(source), "--quiet"]) == 0
    err = capsys.readouterr().err
    assert "invalid value for “language”" in err
    assert "unknown setting “colour”" in err
    _settings('language = "es\n')
    assert main([str(source), "--overwrite", "--quiet"]) == 0
    assert "settings.toml could not be read" in capsys.readouterr().err


def test_ac_34_flags_override_settings_for_that_run_only(workdir: Path) -> None:
    _settings("recursive = false\n")
    project = workdir / "project"
    put(project, "sample.txt", "sub/inner.txt")
    assert main([str(project), "--recursive", "--quiet"]) == 0
    assert (workdir / "ClearMD_Output" / "OutputMD" / "project" / "sub" / "inner.md").is_file()
