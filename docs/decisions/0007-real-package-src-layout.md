# ADR-0007: Real package with `src/` layout instead of a `--no-package` project

- **Status:** accepted; the README-per-folder rule superseded by ADR-0014
- **Date:** 2026-10-24

## Context

In State 0, the template generates the project with `uv init --no-package --no-workspace` from
`requirements.txt`. That works for scripts and analysis, but ClearMD needs:

- a core importable by four adapters (CLI and three GUIs);
- an installable command (`clearmd`);
- to be packaged as an executable and, eventually, published on PyPI (the name `clearmd` is available).

## Decision

- A hand-written `pyproject.toml`, with the **`uv_build`** build backend and the `src/clearmd/` layout.
- Dependencies in `[project.dependencies]`; development tools in the `dev` group
  (`[dependency-groups]`, PEP 735). The GUIs and PyInstaller will come in as extras or groups in their phase.
- `requirements.txt` goes away; `init.sh` only runs `uv sync` (or `uv lock && uv sync` the first time).
- Each subpackage documents its role in the docstring of its `__init__.py`, instead of a `README.md` per folder:
  a README inside the package would end up packaged in the wheel.

## Consequences

- **Gains:** clean imports (`from clearmd.core import ...`) without manipulating `PYTHONPATH`; the `src/` layout
  forces tests to use the installed package, not loose files; the `clearmd` command exists from the
  first commit.
- **Costs:** the template's State 0 → State N flow is abandoned; anyone familiar with the template has to read
  this ADR to understand why there is no `requirements.txt`.
