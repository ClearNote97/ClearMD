# Contributing to ClearMD

Thank you for your interest. ClearMD is a personal portfolio project, so changes are reviewed
carefully and some may be declined, but issues and pull requests are welcome.

## Reporting a problem or asking for a feature

Open an [issue](https://github.com/ClearNote97/ClearMD/issues/new/choose) with its form. For a
security problem, follow [SECURITY.md](./SECURITY.md) instead. Never attach a document with private
content: make a small sample that shows the problem.

## How the project works

- **Spec first.** Each feature has a spec with numbered acceptance criteria, a plan and tasks under
  `spec/features/`, and each decision has an ADR under `docs/decisions/`. Read
  [`spec/roadmap.md`](./spec/roadmap.md) and [`AGENTS.md`](./AGENTS.md) before a larger change, and
  open an issue to discuss it first.
- **One acceptance test per criterion** (`tests/acceptance/test_NNN_*.py`, functions `test_ac_NN_*`).
  A meta-test fails if a criterion has no test.
- **Small files.** Source and test files stay under 200 lines.
- **100 % local.** No change may add a network call, telemetry or a cloud service.

## Development setup

You need [uv](https://docs.astral.sh/uv/) and Python 3.12–3.14:

```bash
uv sync --locked --all-extras
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src tests
uv run pytest -q
```

All four must pass before a pull request is reviewed. CI runs them on Windows and Linux.

## Pull requests

- One topic per pull request, from a branch (`feat/NNN-name`, `fix/name`).
- Commit messages in English, in the form `type(scope): what changed` (`feat`, `fix`, `docs`, `test`).
- User-facing texts go in both catalogs (`src/clearmd/i18n/en.toml` and `es.toml`). Titles and
  buttons are in Title Case (a test checks it).
- Add or update screenshots under `docs/screenshots/` when a window changes.

By contributing you agree that your work is published under the [MIT License](./LICENSE) and that you
follow the [Code of Conduct](./CODE_OF_CONDUCT.md).
