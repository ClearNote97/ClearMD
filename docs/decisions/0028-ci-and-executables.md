# ADR-0028: CI and the executables (PyInstaller, built on GitHub Actions)

- **Status:** accepted
- **Date:** 2026-10-28
- **Refines:** ADR-0008 (executables come out of CI), ADR-0015 (the worker process), ADR-0026
  (the splash), ADR-0027 (the app icon).

## Context

ClearMD is for people who never open a terminal: what they use is a program they double-click.
The author tries the app only that way (no Python, no uv on their computer). ADR-0008 already
said the executables are built on GitHub Actions, one job per operating system, because
PyInstaller only builds for the system it runs on.

## Decision

### Continuous integration (`.github/workflows/ci.yml`)

- Lint and types once (ruff, `mypy --strict`); the whole test suite on **Linux and Windows**,
  **Python 3.12 and 3.14** (the supported range's ends, ADR-0018). GUI tests get a virtual
  display on Linux (Xvfb); Windows draws on the runner's desktop.
- Every action is pinned to a **commit**, not a tag (supply chain), and `uv sync --locked` uses
  the lock as it is. Permissions are read-only except the step that publishes a release.

### The executables (`packaging/clearmd.spec`, `.github/workflows/release.yml`)

- **PyInstaller, one file per program**: `ClearMD` (the desktop app: no console window, the app
  icon, a splash while it unpacks — ADR-0026) and `clearmd` (the command line). One file is what
  a non-technical user can download and open; the cost is a few seconds of unpacking at start.
  (PySide6 will need *onedir* for its license, ADR-0003: that is feature 007's.)
- The worker process (ADR-0015) runs inside the same executable: `multiprocessing` with *spawn*
  and `freeze_support()` at both entry points. The converters' registry is imported by name in
  the worker, so every ClearMD module is bundled explicitly; the data files of the libraries that
  read documents (magika's model, trafilatura's and justext's data) and ClearMD's own catalogs
  and icons are bundled too.
- **Each build is checked before it is published** (`packaging/check_executables.sh`): the
  command line converts a real batch (a document of every format, one without extension, LaTeX,
  OpenDocument) and the window opens and closes by itself (`--smoke`).
- Built with **Python 3.13** (the newest with a long track record; tests run on 3.12–3.14). The
  Linux binary is built on Ubuntu 22.04 so it runs on older distributions.
- `pyinstaller` lives in a `build` dependency group: never in the app's own dependencies.

### Releases

- A tag `v*` publishes a **GitHub Release** (a pre-release until 1.0) with: the Windows app, the
  Windows command line, a Linux archive with both, and `THIRD-PARTY-NOTICES.txt` — the license
  of every bundled library, read from its own package metadata (`packaging/notices.py`). A manual
  run of the workflow only builds and checks (artifacts), without publishing.

### Deferred, on purpose

- **Code signing** (SignPath, free for open source) needs the repository to be public; until
  then Windows SmartScreen warns, and the release notes say how to proceed ("More info → Run
  anyway"). It comes with the public release (the author's decision: public only after using
  and approving the executable).
- **A Windows Job Object** as the worker's hard memory cap and an advisory check of `uv.lock`
  (known limitations of 001) move to a later hardening feature: they do not block a usable
  executable; the worker's sampled memory limit already applies on Windows.

## Consequences

- **Gains:** a program the author and the users can open without installing anything; every
  release checked by a real batch on the system it is for; the tests run where the users are.
- **Costs:** about 100 MB per program (magika's model and onnxruntime are most of it); a few
  seconds at start; Windows warns until the executables are signed.

## Alternatives considered

- **onedir distributions:** faster start, but a folder of hundreds of files is confusing to
  download and to keep together. Rejected for ttk; required later for PySide6.
- **Nuitka:** smaller and faster, but much slower to build and less proven with these libraries.
- **One program with both interfaces:** a windowed program cannot print to the terminal on
  Windows. Two programs from one build.
- **Building on the author's Windows computer:** not reproducible, and the author does not
  install Python. CI it is (ADR-0008).
