"""What each module of ClearMD imports, read from its source (relative imports resolved): the
architecture tests' raw material (ADR-0014, ADR-0039)."""

import ast
from pathlib import Path

import clearmd

PACKAGE_ROOT = Path(clearmd.__file__).parent


def imported_modules(source: str, module: str, *, is_package: bool) -> set[str]:
    """Absolute names of every module imported by ``source`` (relative imports resolved)."""
    package_parts = module.split(".") if is_package else module.split(".")[:-1]
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package_parts[: len(package_parts) - node.level + 1]
                name = ".".join([*base, node.module] if node.module else base)
            else:
                name = node.module or ""
            found.add(name)
    return found


def source_modules() -> list[tuple[str, Path]]:
    modules = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        parts = path.relative_to(PACKAGE_ROOT.parent).with_suffix("").parts
        name = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
        modules.append((name, path))
    return modules
