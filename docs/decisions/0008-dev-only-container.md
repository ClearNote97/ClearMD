# ADR-0008: The container is for development; executables come out of CI

- **Status:** accepted
- **Date:** 2026-10-24

## Context

The working contract (`README_AGENTS.md`) runs everything inside a Linux Dev Container. Two facts clash
with a desktop app:

1. **GUIs need a display.** The container has none; on WSL2 the WSLg one can be forwarded, at the cost
   of extra graphics libraries and configuration in the compose file.
2. **PyInstaller and `flet build` produce the executable for the system they run on.** A Linux container never
   produces a Windows `.exe`.

## Decision

- The container runs: core, CLI, tests (the GUIs with `xvfb`, a virtual display) and the Linux build.
- The GUIs are viewed occasionally by forwarding WSLg. The graphics libraries and the WSLg configuration are
  added to the `Dockerfile` and the compose file **in each GUI's phase**, not before.
- The Windows and Linux executables are built on **GitHub Actions** with a per-operating-system matrix and
  published in *Releases*. macOS is left out for now: notarization requires a paid Apple Developer
  account.

## Consequences

- **Gains:** the development image stays minimal (413 MB, see ADR-0009); the binaries are built in a
  clean, reproducible environment for each system.
- **Costs:** viewing a GUI requires WSLg and some configuration; the Windows executables are only
  tested in CI or on a Windows machine.

## Alternatives considered

- **GUI always inside the container:** rejected for now; more libraries and configuration from day one,
  with no benefit while the core and the CLI are being built.
- **Building the `.exe` with Wine inside the container:** fragile and slow. Rejected.
