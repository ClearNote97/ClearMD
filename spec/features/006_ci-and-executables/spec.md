# Feature 006 — CI and the executables

## Goal

A person downloads ClearMD and opens it with a double click — no Python, no installer, no
terminal — and every release is built and checked by a machine, the same way, on the system it
is for.

## Scope

- **Includes:** CI (lint, types, tests on Linux and Windows, Python 3.12 and 3.14); the desktop
  app and the command line as one-file executables for Windows and Linux (PyInstaller), with the
  app icon and a splash; a check of each build by a real batch; GitHub Releases with the
  third-party notices (ADR-0028).
- **Does not include:** code signing (with the public release), a Windows Job Object for the
  worker and the `uv.lock` audit (a later hardening feature), macOS (no runner budget decided),
  installers.

## Acceptance criteria (what MUST be true)

Tests: `tests/acceptance/test_006_ci_and_executables.py` (what can be checked from the
repository) and the workflow itself (what only CI can run).

- [ ] **AC-01** CI runs ruff, `mypy --strict` and the whole test suite on Linux and Windows with
  Python 3.12 and 3.14, from the lock file, with every action pinned to a commit and read-only
  permissions.
- [ ] **AC-02** The release workflow builds, on Windows and on Linux, two one-file programs:
  `ClearMD` (the desktop app: no console, the app icon, a splash) and `clearmd` (the command line).
- [ ] **AC-03** Each build is checked before it is published: the command line converts a real
  batch (every format, a file without extension, LaTeX, OpenDocument) through the worker process,
  and the desktop app opens and closes by itself (`--smoke`).
- [ ] **AC-04** A version tag publishes a GitHub pre-release with the Windows app, the Windows
  command line, a Linux archive and `THIRD-PARTY-NOTICES.txt` (every bundled library's license,
  from its own metadata); a manual run only builds and checks.
- [ ] **AC-05** The release notes tell, in English and Spanish, how to open the app when Windows
  warns that it is not signed, and that nothing leaves the computer.
- [ ] **AC-06** PyInstaller is a build-only dependency (its own group), pinned like every other
  dependency (at least two weeks old).

## Risks / open questions

- Windows-only test failures the Linux container never showed (paths, links, permissions).
- The size (~100 MB per program): mostly magika's model and onnxruntime.
