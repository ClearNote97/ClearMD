# ADR-0053: The installed Classic App is a folder

- **Status:** accepted
- **Date:** 2026-11-09
- **Amends:** ADR-0028 (one-file executables) and ADR-0040 (the installer) for the installed copy
  only. The portable download stays one file.
- **Origin:** the second audit (`docs/audit/2026-11-09-audit-boards-v2.md`, recommendation 10).

## Context

The Classic App is the recommended one, and the one most people install. As a one-file program it
unpacks itself into a temporary folder at every start: about 5 s on Windows, against about 1.2 s
for the Modern App, which is installed as a folder. ADR-0028 chose one file so that a download is
one file to double-click; an installed copy is never seen as files by the person, so that reason
does not hold there.

## Decision

- The build makes the classic app twice from one analysis: the one-file `ClearMD.exe` (the
  portable download, with its splash) and the folder `dist/ClearMD-Classic/` (`ClearMD.exe` and
  `_internal/`).
- Both installer editions install the folder's contents into the install folder, so the program
  keeps its place (`{app}\ClearMD.exe`) and its shortcuts; `_internal\` goes with the component.
- CI starts both copies and prints each window's time from launch to close (`--smoke`).

## Consequences

- **Gains:** the recommended app opens without unpacking; the start time is visible in every run.
- **Costs:** one more build output to sign and check; the light installer's size is checked by its
  limit (≤ 45 MB).
