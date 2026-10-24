# ADR-0003: PySide6-Essentials instead of PyQt6

- **Status:** accepted
- **Date:** 2026-10-24

## Context

One of ClearMD's three GUIs uses Qt. Python has two mature Qt 6 bindings, with the same library
underneath and nearly identical APIs, but with different licenses (verified on PyPI on 2026-10-24):

| Binding | Version | License |
|---|---|---|
| PyQt6 (Riverbank) | 6.11.0 | GPL-3.0-only, or a paid commercial license |
| PySide6 (The Qt Company) | 6.12.0 | LGPL-3.0-only or GPL-2.0/3.0 |

ClearMD is published under the **MIT** license (`LICENSE`) and distributed as an executable.

## Decision

Use **`PySide6-Essentials`**, not PyQt6, and not the `PySide6` metapackage.

- PyQt6 would force relicensing the whole app as GPL or paying for a commercial license. PySide6, under LGPL,
  is compatible with distributing an MIT app.
- The `PySide6` metapackage pulls in `PySide6_Addons`, `PySide6_WebEngine` and `PySide6_Pdf`, which ClearMD does not use.
  `PySide6-Essentials` brings only the base modules (~82 MB wheel on Windows and Linux).

## Consequences

- **Gains:** MIT-compatible license, at no cost; a lighter executable than with the metapackage.
- **Costs:** the LGPL requires that the user be able to replace the Qt libraries. That is why the Qt GUI
  executable is distributed in folder mode (*onedir*) and not as a single `.exe` (*onefile*). There are fewer
  PySide6 tutorials than PyQt ones, although the API is practically the same.

## Alternatives considered

- **PyQt6 with the app under GPL:** rejected; it would change the license of the whole project for a single GUI.
- **`PySide6` metapackage:** rejected because of size.
