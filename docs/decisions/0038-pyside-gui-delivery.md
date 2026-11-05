# ADR-0038: The PySide6 GUI, delivered as a folder next to the ttk app

- **Status:** accepted
- **Date:** 2026-11-05
- **Refines:** ADR-0003 (PySide6-Essentials, LGPL, onedir), ADR-0028 (CI and the executables).

## Context

ClearMD offers the same app in several toolkits on one presenter (ADR-0001): ttk is released; PySide6
is the second (feature 016), flet the third (017). The owner will choose a main one after trying the
three. PySide6 is LGPL: the user must be able to replace the Qt libraries, so it cannot be a single
self-unpacking file (ADR-0003). Qt adds about 45 MB that the ttk app and the CLI must not carry
(found in refactor R01).

## Decision

- **One release per version, every interface in it.** The version is ClearMD's; each GUI is one more
  file of the same release: `ClearMD-<v>-windows.exe` (ttk), `ClearMD-Qt-<v>-windows.zip` (PySide6),
  `clearmd-cli-<v>-windows.exe`, and `ClearMD-<v>-linux.tar.gz` with all of them.
- **PySide6 as a folder** (`ClearMD-Qt/`, PyInstaller onedir): unzip, open `ClearMD-Qt.exe`. Its Qt
  libraries are plain files next to it: replaceable, as the LGPL asks. The notices file lists PySide6
  and Qt with their licenses.
- **Its own spec** (`packaging/clearmd_pyside.spec`): it leaves ttk, tkinter and the other GUIs out;
  the ttk spec leaves Qt out. Each executable carries one toolkit.
- **The `pyside` extra** (`pip install clearmd[pyside]`, command `clearmd-pyside`) for whoever runs it
  from Python; the base install stays light.

## Consequences

- **Gains:** the owner tries both apps from the same release; the ttk app stays at ~40 MB; LGPL
  respected.
- **Costs:** a bigger download for the Qt app (a folder of ~100 MB, zipped); two specs to build; once
  the owner chooses, the others may leave the release.
