"""Every feature folder under spec/features has its acceptance file, with a test per criterion.

A feature may spread its criteria over several ``test_<number>_*.py`` files (a long file is split by
group of criteria): the criteria are covered by the union of them, and each file must hold at least
one ``test_ac_`` function.

A planned feature (no acceptance file yet, tasks still open) is skipped; a closed one (every task
ticked) must have it.

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


def _closed(feature: Path) -> bool:
    """Every task of the feature ticked: it cannot be closed without its acceptance file."""
    tasks = (feature / "tasks.md").read_text("utf-8")
    return "- [x] **T" in tasks and "- [ ] **T" not in tasks


def _acceptance_files(feature: Path) -> list[Path]:
    number = feature.name.split("_", 1)[0]
    return sorted((ROOT / "tests" / "acceptance").glob(f"test_{number}_*.py"))


def test_there_are_features_to_check() -> None:
    names = [feature.name[:3] for feature in FEATURES]
    assert names[:2] == ["001", "002"] and all(_closed(f) for f in FEATURES[:2])


@pytest.mark.parametrize("feature", FEATURES, ids=lambda feature: feature.name)
def test_every_acceptance_criterion_has_a_test(feature: Path) -> None:
    files = _acceptance_files(feature)
    # A feature under way (a task still open) completes its acceptance with its tasks.
    under_way = (feature / "tasks.md").is_file() and not _closed(feature)
    if under_way or (not files and not _closed(feature)):
        pytest.skip(f"{feature.name} is open: its acceptance is complete when its tasks are")
    assert files, f"{feature.name}: closed feature without an acceptance file"
    empty = [file.name for file in files if not _covered(file)]
    assert empty == [], f"{feature.name}: files without a test_ac_ function"
    criteria = _criteria(feature)
    assert criteria, f"{feature.name}: no **AC-NN** in spec.md"
    assert sorted(criteria - set().union(*(_covered(file) for file in files))) == []
