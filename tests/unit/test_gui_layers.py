"""Inside each GUI, the layers of ADR-0039: ``app.py`` → ``window/`` → ``views/`` →
``components/`` → ``layout/``, ``visuals/``. A module imports its own layer or the ones after it,
never one before; only the window and the entry file know the window class."""

import ast
from pathlib import Path

import pytest
from support.imports import imported_modules, source_modules

GUIS = ("clearmd.frontend.ttk", "clearmd.frontend.qt", "clearmd.frontend.pyside")
RANK = {"app": 0, "window": 1, "views": 2, "components": 3, "layout": 4, "visuals": 4}
WINDOW_CLASSES = ("TtkApp", "QtApp", "PySideApp", "FletApp")


def layer(module: str) -> tuple[str, int] | None:
    """The GUI a module belongs to and its layer's rank (``None``: outside the layers)."""
    for gui in GUIS:
        if module.startswith(gui + "."):
            first = module[len(gui) + 1 :].split(".")[0]
            return (gui, RANK[first]) if first in RANK else None
    return None


def upward(module: str, imports: set[str]) -> list[str]:
    here = layer(module)
    if here is None:
        return []
    found = []
    for name in sorted(imports):
        there = layer(name)
        if there is not None and there[0] == here[0] and there[1] < here[1]:
            found.append(f"{module} imports {name}")
    return found


def window_parameters(source: str) -> list[str]:
    """Parameters annotated with a whole window: a collaborator must get only what it uses."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for argument in node.args.args + node.args.kwonlyargs:
                shown = ast.unparse(argument.annotation) if argument.annotation else ""
                if any(name in shown for name in WINDOW_CLASSES):
                    found.append(f"{node.name}({argument.arg}: {shown})")
    return found


GUI_MODULES = [(m, p) for m, p in source_modules() if layer(m) is not None or m.endswith(".app")]


@pytest.mark.parametrize(("module", "path"), GUI_MODULES, ids=lambda value: str(value))
def test_a_layer_never_imports_one_before_it(module: str, path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    assert upward(module, imported_modules(source, module, is_package=False)) == []


@pytest.mark.parametrize(("module", "path"), GUI_MODULES, ids=lambda value: str(value))
def test_only_the_window_knows_the_window_class(module: str, path: Path) -> None:
    here = layer(module)
    if here is None or here[1] <= RANK["window"]:
        return
    assert window_parameters(path.read_text(encoding="utf-8")) == []


def test_the_checkers_catch_what_they_claim() -> None:
    assert upward(
        "clearmd.frontend.pyside.components.rail", {"clearmd.frontend.pyside.views.choose"}
    )
    assert upward("clearmd.frontend.ttk.views.choose", {"clearmd.frontend.ttk.window.view"})
    assert not upward("clearmd.frontend.ttk.views.choose", {"clearmd.frontend.ttk.components.rail"})
    assert not upward("clearmd.frontend.ttk.layout.frame", {"clearmd.frontend.ttk.visuals.look"})
    assert window_parameters("def f(app: 'TtkApp') -> None: ...")
    assert not window_parameters("def f(rail: Rail) -> None: ...")
