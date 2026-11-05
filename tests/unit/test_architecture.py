"""The dependency rule of ADR-0014, checked on the real source tree.

| Package                                 | May import (besides the standard library)            |
|-----------------------------------------|------------------------------------------------------|
| clearmd.backend.schemas                 | clearmd.backend.schemas                              |
| clearmd.backend.use_cases               | clearmd.backend.schemas, clearmd.backend.use_cases   |
| clearmd.i18n                            | clearmd.i18n                                         |
| clearmd.backend.services                | third-party; clearmd.backend (not api), clearmd.i18n |
| …services.conversion.odt, .markdown_out | standard library only (ADR-0006, ADR-0024); odt also |
| …services.conversion.xmltree, .inline   | schemas, markdown_out, safe_files, xmltree, inline,  |
|                                         | itself (inline: markdown_out only)                   |
| clearmd.backend.api                     | third-party; clearmd.backend, clearmd.i18n           |
| clearmd.frontend                        | third-party; clearmd.backend.api, .schemas, i18n,    |
|                                         | clearmd.frontend                                     |
| clearmd.frontend.presenter              | standard library; backend.api, .schemas, i18n, itself|
| clearmd.frontend.design                 | standard library only (shared by every GUI)          |
| clearmd.frontend.launch                 | the frozen executable's splash only                  |
| clearmd.frontend.ttk, .pyside, .flet    | third-party; the presenter, design, launch, .schemas,|
|                                         | i18n, itself                                         |
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from support.imports import imported_modules, source_modules


@dataclass(frozen=True)
class Rule:
    allows_third_party: bool
    allowed_internal: tuple[str, ...]
    forbidden_stdlib: tuple[str, ...] = ()  # standard modules a layer must not use (a toolkit)


_ARTICLE = (  # what the article renderer and its writer may import besides the standard library
    "clearmd.backend.schemas",
    "clearmd.backend.services.conversion.markdown_out",
    "clearmd.backend.services.conversion.inline",
    "clearmd.backend.services.conversion.xmltree",
)
RULES: dict[str, Rule] = {
    "clearmd.backend.schemas": Rule(False, ("clearmd.backend.schemas",)),
    "clearmd.backend.use_cases": Rule(
        False, ("clearmd.backend.schemas", "clearmd.backend.use_cases")
    ),
    "clearmd.i18n": Rule(False, ("clearmd.i18n",)),
    "clearmd.backend.services": Rule(
        True,
        (
            "clearmd.backend.schemas",
            "clearmd.backend.use_cases",
            "clearmd.backend.services",
            "clearmd.i18n",
        ),
    ),
    # ClearMD's own .odt converter and the output guarantee: the standard library only.
    "clearmd.backend.services.conversion.odt": Rule(
        False,
        (
            "clearmd.backend.schemas",
            "clearmd.backend.services.conversion.markdown_out",
            "clearmd.backend.services.conversion.safe_files",
            "clearmd.backend.services.conversion.xmltree",
            "clearmd.backend.services.conversion.inline",
            "clearmd.backend.services.conversion.odt",
            # Its pictures, kept in the images folder (012): the standard library and the above.
            "clearmd.backend.services.conversion.images",
        ),
    ),
    # The article renderer and its writer: trafilatura's XML in, ClearMD's Markdown out; stdlib.
    "clearmd.backend.services.conversion.html.render": Rule(
        False, (*_ARTICLE, "clearmd.backend.services.conversion.html.writer")
    ),
    "clearmd.backend.services.conversion.html.writer": Rule(
        False, (*_ARTICLE, "clearmd.backend.services.conversion.html.writer")
    ),
    # Inline text as ClearMD's own converters write it: the standard library and markdown_out.
    "clearmd.backend.services.conversion.inline": Rule(
        False,
        (
            "clearmd.backend.services.conversion.markdown_out",
            "clearmd.backend.services.conversion.inline",
        ),
    ),
    "clearmd.backend.services.conversion.markdown_out": Rule(
        False, ("clearmd.backend.services.conversion.markdown_out",)
    ),
    # The XML reader shared by .odt and the article mode (004): the standard library only.
    "clearmd.backend.services.conversion.xmltree": Rule(False, ()),
    "clearmd.backend.api": Rule(True, ("clearmd.backend", "clearmd.i18n")),
    "clearmd.frontend": Rule(
        True, ("clearmd.backend.api", "clearmd.backend.schemas", "clearmd.i18n", "clearmd.frontend")
    ),
    # The presenter (ADR-0026): every GUI's interaction logic; the standard library, no toolkit.
    "clearmd.frontend.presenter": Rule(
        False,
        (
            "clearmd.backend.api",
            "clearmd.backend.schemas",
            "clearmd.i18n",
            "clearmd.frontend.presenter",
        ),
        forbidden_stdlib=("tkinter", "turtle"),
    ),
    # The tokens every GUI draws with (ADR-0039): plain data, the standard library only.
    "clearmd.frontend.design": Rule(False, ("clearmd.frontend.design",)),
    # The executables' start (splash, smoke run): PyInstaller's own module only.
    "clearmd.frontend.launch": Rule(True, ()),
    # A GUI talks to the presenter only: never to the api or another interface (ADR-0001/0026).
    "clearmd.frontend.ttk": Rule(
        True,
        (
            "clearmd.frontend.presenter",
            "clearmd.frontend.design",
            "clearmd.frontend.launch",
            "clearmd.backend.schemas",
            "clearmd.i18n",
            "clearmd.frontend.ttk",
        ),
    ),
    # The PySide6 GUI (feature 016) and flet: as ttk.
    **{
        gui: Rule(
            True,
            (
                "clearmd.frontend.presenter",
                "clearmd.frontend.design",
                "clearmd.frontend.launch",
                "clearmd.backend.schemas",
                "clearmd.i18n",
                gui,
            ),
        )
        for gui in ("clearmd.frontend.pyside", "clearmd.frontend.flet")
    },
    # The package root and `clearmd.backend` itself only hold docstrings.
    "clearmd.backend": Rule(False, ()),
    "clearmd": Rule(False, ()),
}


def _is_within(module: str, package: str) -> bool:
    return module == package or module.startswith(package + ".")


def rule_for(module: str) -> Rule:
    """The most specific rule whose package contains ``module``."""
    owner = max((pkg for pkg in RULES if _is_within(module, pkg)), key=len)
    return RULES[owner]


def violations(module: str, imports: set[str]) -> list[str]:
    rule = rule_for(module)
    problems = []
    for name in sorted(imports):
        top = name.split(".")[0]
        if top in rule.forbidden_stdlib:
            problems.append(f"{module} imports {name}")
            continue
        if top == "__future__" or top in sys.stdlib_module_names:
            continue
        if top == "clearmd":
            if not any(_is_within(name, allowed) for allowed in rule.allowed_internal):
                problems.append(f"{module} imports {name}")
        elif not rule.allows_third_party:
            problems.append(f"{module} imports third-party {name}")
    return problems


@pytest.mark.parametrize(("module", "path"), source_modules(), ids=lambda value: str(value))
def test_module_respects_the_dependency_rule(module: str, path: Path) -> None:
    imports = imported_modules(
        path.read_text(encoding="utf-8"), module, is_package=path.name == "__init__.py"
    )
    assert violations(module, imports) == []


# --- The checker itself must catch what it claims to catch ---------------------------------------


@pytest.mark.parametrize(
    ("module", "source"),
    [
        ("clearmd.backend.use_cases.planning", "import markitdown"),
        ("clearmd.backend.use_cases.planning", "from clearmd.backend.services import worker"),
        ("clearmd.backend.schemas.models", "from ..use_cases import ports"),
        ("clearmd.backend.services.worker", "from clearmd.frontend.cli import app"),
        ("clearmd.backend.services.worker", "from clearmd.backend.api import run_batch"),
        ("clearmd.frontend.cli.app", "from clearmd.backend.use_cases import planning"),
        ("clearmd.frontend.cli.app", "from clearmd.backend.services.worker import supervisor"),
        ("clearmd.i18n", "import tomli"),
        ("clearmd.backend.services.conversion.odt.render", "import lxml.etree"),
        (
            "clearmd.backend.services.conversion.odt",
            "from clearmd.backend.services.worker import child",
        ),
        ("clearmd.backend.services.conversion.markdown_out", "import markdown_it"),
        ("clearmd.backend.services.conversion.html.writer.runs", "import trafilatura"),
        ("clearmd.frontend.presenter.presenter", "import tkinter"),
        ("clearmd.frontend.presenter.presenter", "import ttkbootstrap"),
        ("clearmd.frontend.presenter.presenter", "from clearmd.backend.services import folders"),
        ("clearmd.frontend.ttk.app", "from clearmd.backend.api import plan_batch"),
        ("clearmd.frontend.ttk.app", "from clearmd.frontend.cli import main"),
        ("clearmd.frontend.pyside.app", "from clearmd.frontend.ttk import TtkApp"),
        ("clearmd.frontend.pyside.app", "from clearmd.backend.api import plan_batch"),
        ("clearmd.frontend.ttk.app", "from clearmd.frontend.pyside import PySideApp"),
    ],
)
def test_checker_reports_forbidden_imports(module: str, source: str) -> None:
    assert violations(module, imported_modules(source, module, is_package=False)) != []


@pytest.mark.parametrize(
    ("module", "source"),
    [
        ("clearmd.backend.use_cases.planning", "import zipfile\nfrom pathlib import Path"),
        ("clearmd.backend.use_cases.planning", "from ..schemas.models import BatchPlan"),
        (
            "clearmd.backend.services.worker",
            "import psutil\nfrom clearmd.backend.use_cases import ports",
        ),
        ("clearmd.backend.api", "from clearmd.backend.services.worker import supervisor"),
        ("clearmd.frontend.cli.app", "from clearmd.backend.api import plan_batch"),
        ("clearmd.frontend.cli.app", "from clearmd.backend.schemas.models import BatchPlan"),
        (
            "clearmd.backend.services.conversion.odt.render",
            "import pyexpat\nfrom clearmd.backend.services.conversion.markdown_out import MARK",
        ),
    ],
)
def test_checker_accepts_allowed_imports(module: str, source: str) -> None:
    assert violations(module, imported_modules(source, module, is_package=False)) == []


def test_relative_imports_resolve_from_packages_and_modules() -> None:
    assert imported_modules(
        "from . import ports", "clearmd.backend.use_cases", is_package=True
    ) == {"clearmd.backend.use_cases"}
    assert imported_modules(
        "from .ports import X", "clearmd.backend.use_cases.planning", is_package=False
    ) == {"clearmd.backend.use_cases.ports"}
