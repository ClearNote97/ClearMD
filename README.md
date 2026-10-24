# ClearMD

[Leer en español](./README.es.md)

**Turn your documents into Markdown. 100% local: your files never leave your machine.**

> 🚧 **Status: Phase 0.** Architecture, decisions, specs and the development environment are ready; conversion
> is being built in feature 001 (see the [roadmap](./spec/roadmap.md)). Today `clearmd` only answers
> `--version`.

## What it will do

- Convert **PDF, Word, PowerPoint, Excel, HTML, CSV, EPUB and notebooks** to Markdown.
- Convert **LaTeX (`.tex`)** keeping the equations (`$...$`), without pandoc.
- Convert **LibreOffice (`.odt`)** with no external dependency.
- Extract **only the article** from a saved web page.
- Process **many files or whole folders** at once, detecting the format of each file.
- Put the results in a **`ClearMD_Output`** folder next to what you chose, with a report of the batch.
- Speak **English and Spanish**, with a help window, a first-run welcome and clear progress — built for people
  who never open a terminal.
- Offer the same functionality as a **command line** tool and as **three desktop apps** (ttkbootstrap, PySide6
  and flet), with downloadable executables for Windows and Linux.

## How it is built

A pure core (ports and use cases) surrounded by interchangeable adapters: converters on one side, interfaces
on the other. The four interfaces share exactly the same logic.

```
 CLI · ttkbootstrap · PySide6 · flet  →  presenter  →  core  ←  markitdown · tex · odt · html-article
```

Details in [`docs/architecture/`](./docs/architecture/).

## Design decisions

Every non-trivial decision has an ADR in [`docs/decisions/`](./docs/decisions/), with its context, rejected
alternatives and consequences. Some of them:

- [Pure core with ports and adapters](./docs/decisions/0001-core-and-adapters.md)
- [PySide6 instead of PyQt6, for licensing reasons](./docs/decisions/0003-pyside6-over-pyqt6.md)
- [markitdown behind a port + own converters](./docs/decisions/0004-hybrid-engine-with-markitdown.md)
- [100% local](./docs/decisions/0005-fully-local.md)
- [LaTeX without pandoc](./docs/decisions/0006-own-converters.md)
- [Pruning the starting template](./docs/decisions/0009-template-pruning.md)
- [Designed for non-technical users first](./docs/decisions/0013-non-technical-users-first.md)

## Development

Requirements on the host: **Docker + Docker Compose v2** and **VS Code with Dev Containers** (on Windows,
inside WSL 2). No Python on the host.

1. Open the folder in VS Code → **Reopen in Container**.
2. The container installs the dependencies with `uv` automatically.
3. Inside the container:

```bash
uv run pytest                                   # tests
uv run ruff check . && uv run ruff format --check .
uv run mypy                                     # types (strict)
uv run clearmd --version
```

The project follows **Spec-Driven Development**: [`spec/`](./spec/) defines what must be true; [`docs/`](./docs/)
explains how and why it ended up that way. Working with AI agents follows
[`README_AGENTS.md`](./README_AGENTS.md) (in Spanish).

## License

[MIT](./LICENSE) © 2026 Nicolás Enrique Valencia Santiago
