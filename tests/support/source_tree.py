"""The project's Python files measured for the size rule (ADR-0039): lines per file, lines per
class, ClearMD's own base classes. Shared by the size test and the refactor's tooling."""

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEASURED = ("src", "tests", "packaging")


@dataclass(frozen=True)
class Measured:
    path: str  # relative to the repository, with forward slashes
    lines: int
    classes: dict[str, int]  # class name -> its lines
    bases: dict[str, tuple[str, ...]]  # class name -> the names of its bases


def python_files(root: Path = ROOT) -> Iterator[Path]:
    """Every ``.py`` file under the measured folders, subpackages included."""
    for folder in MEASURED:
        for path in sorted((root / folder).rglob("*.py")):
            if "__pycache__" not in path.parts and ".venv" not in path.parts:
                yield path


def measure(path: Path, root: Path = ROOT) -> Measured:
    text = path.read_text(encoding="utf-8")
    classes: dict[str, int] = {}
    bases: dict[str, tuple[str, ...]] = {}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ClassDef):
            end = node.end_lineno or node.lineno
            classes[node.name] = end - node.lineno + 1
            bases[node.name] = tuple(ast.unparse(base) for base in node.bases)
    relative = path.relative_to(root).as_posix()
    return Measured(relative, len(text.splitlines()), classes, bases)


def measured(root: Path = ROOT) -> list[Measured]:
    return [measure(path, root) for path in python_files(root)]
