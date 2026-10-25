# ADR-0018: Supported Python range and ways to install

- **Status:** accepted
- **Date:** 2026-10-25

## Context

`pyproject.toml` declared `requires-python = ">=3.14,<3.15"`, but markitdown 0.1.9 only requires
`>=3.10,<3.15`. The floor only matters for people who install ClearMD as a Python package: the executables
(ADR-0008) bundle their own Python, so their users need nothing installed. Developers who want the CLI in a
script are the ones affected, and few of them already run 3.14.

## Decision

- **Supported range: Python 3.12 to 3.14** (`>=3.12,<3.15`). 3.12 keeps the modern syntax (`type` aliases,
  PEP 695 generics); the ceiling comes from markitdown (ADR-0004).
- **Development and packaging stay on 3.14** (dev container, executables). ruff and mypy target 3.12 so that
  code which only works on 3.14 is caught. CI tests 3.12 and 3.14 (feature 006).
- **Ways to install**, documented in the README:
  1. **Executables** for Windows and Linux — no Python needed. The recommendation for non-technical users.
  2. **`uv`** (`uv tool install`) — recommended for developers: the same tool as the development stack.
  3. **`pip`** — supported.
- Until the package is published on PyPI (at the end of the roadmap), `uv` and `pip` install from the GitHub
  repository.

## Consequences

- **Gains:** a developer on 3.12 or 3.13 can install the CLI; executables are unaffected.
- **Costs:** two Python versions to test in CI; no 3.13/3.14-only features in the code.

## Alternatives considered

- **Keep `>=3.14`:** rejected; it excludes most developers for no benefit.
- **Go down to 3.10:** rejected; the syntax gain of 3.12 is worth more than two old versions.
