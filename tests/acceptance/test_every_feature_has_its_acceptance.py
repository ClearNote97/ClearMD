"""Every feature folder under spec/features has its acceptance file, with a test per criterion.

Test names are read with ``ast`` (nothing is imported): a feature added without its tests, or a
criterion added to a spec without a test, fails here.
"""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
FEATURES = sorted(
    path for path in (ROOT / "spec" / "features").iterdir() if (path / "spec.md").is_file()
)


def _criteria(feature: Path) -> set[int]:
    return {
        int(n) for n in re.findall(r"\*\*AC-(\d+)\*\*", (feature / "spec.md").read_text("utf-8"))
    }


def _covered(test_file: Path) -> set[int]:
    tree = ast.parse(test_file.read_text("utf-8"))
    names = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    return {
        int(n)
        for name in names
        if name.startswith("test_ac_")
        for n in re.findall(r"ac_(\d+)", name)
    }


def test_there_are_features_to_check() -> None:
    assert [feature.name[:3] for feature in FEATURES] == ["001", "002"]


@pytest.mark.parametrize("feature", FEATURES, ids=lambda feature: feature.name)
def test_every_acceptance_criterion_has_a_test(feature: Path) -> None:
    number = feature.name.split("_", 1)[0]
    (test_file,) = sorted((ROOT / "tests" / "acceptance").glob(f"test_{number}_*.py"))
    criteria = _criteria(feature)
    assert criteria, f"{feature.name}: no **AC-NN** in spec.md"
    assert sorted(criteria - _covered(test_file)) == []
