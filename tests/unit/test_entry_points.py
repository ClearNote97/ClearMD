"""Every command ClearMD installs (pyproject's scripts and gui-scripts) resolves to a function:
a module moved by refactor R01 must never leave a command pointing at nothing."""

import importlib
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
COMMANDS = {**PROJECT["scripts"], **PROJECT["gui-scripts"]}


@pytest.mark.parametrize(("command", "target"), sorted(COMMANDS.items()))
def test_each_command_resolves_to_a_function(command: str, target: str) -> None:
    module, _, name = target.partition(":")
    assert callable(getattr(importlib.import_module(module), name)), command


def test_the_executables_start_from_the_same_functions() -> None:
    launcher = (ROOT / "packaging" / "launch_gui.py").read_text(encoding="utf-8")
    assert "clearmd.frontend.ttk" in launcher and COMMANDS["clearmd-ttk"].startswith(
        "clearmd.frontend.ttk:"
    )
