"""Refactor R01 — one test per acceptance criterion (spec/features/R01_*/spec.md). What the
refactor has not reached yet is an expected failure, strict: the day it passes, its mark must go."""

import ast
import importlib
import sys
import tomllib
from pathlib import Path

import pytest
from support.golden import MANIFEST, outputs
from support.size_ratchet import CLASSES, ENTRY_FILES, FILES
from support.source_tree import ROOT, measured

FRONTEND = ROOT / "src" / "clearmd" / "frontend"
GUIS = ("ttk", "pyside")
FOLDERS = ("window", "layout", "views", "components", "visuals")


def test_ac_01_every_file_and_class_within_the_rule() -> None:
    assert (FILES, CLASSES) == ({}, {})


def test_ac_02_every_gui_has_the_same_small_layout() -> None:
    for gui in GUIS:
        assert all((FRONTEND / gui / folder).is_dir() for folder in FOLDERS), gui
    assert ENTRY_FILES == {}


def test_ac_03_every_source_module_says_what_it_is() -> None:
    silent = [
        file.path
        for file in measured()
        if file.path.startswith("src/")
        and ast.get_docstring(ast.parse((ROOT / file.path).read_text("utf-8"))) is None
    ]
    assert silent == []


@pytest.mark.skipif(sys.platform == "win32", reason="recorded on Linux: the refactor's gate")
def test_ac_04_every_fixture_converts_to_the_recorded_bytes() -> None:
    expected = set(MANIFEST.read_text(encoding="utf-8").splitlines())
    actual = set(outputs())
    assert (sorted(expected - actual), sorted(actual - expected)) == ([], [])


def test_ac_05_the_ttk_and_cli_executables_carry_no_other_toolkit() -> None:
    spec = (ROOT / "packaging" / "clearmd.spec").read_text(encoding="utf-8")
    assert "*OTHER_TOOLKITS" in spec and "not module.startswith(OTHER_GUIS)" in spec


def test_ac_06_every_command_resolves() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    commands = {**project["scripts"], **project["gui-scripts"]}
    assert {"clearmd", "clearmd-ttk", "clearmd-pyside"} <= set(commands)
    for target in commands.values():
        module, _, name = target.partition(":")
        assert callable(getattr(importlib.import_module(module), name))


def test_ac_07_adr_0039_accepted_and_a_readme_in_every_folder() -> None:
    adr = (ROOT / "docs" / "decisions" / "0039-modular-layout-and-file-size.md").read_text("utf-8")
    assert "**Status:** accepted" in adr
    folders = {path.parent for path in (ROOT / "src").rglob("*.py")} - {ROOT / "src"}
    assert sorted(str(f) for f in folders if not (f / "README.md").exists()) == []


def test_the_size_rule_is_measured_where_it_applies() -> None:
    assert Path(ROOT / "tests" / "unit" / "test_module_size.py").is_file()
