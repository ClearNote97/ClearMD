# Feature 017 — The Windows installer and uninstaller

## Goal

A person who has never unzipped a folder installs ClearMD like any Windows program: one file, a few
clicks, the apps in the Start menu; and removes it the same way, from "Installed apps", leaving
nothing behind but their own documents (ADR-0040).

## Scope

- **Includes:** `ClearMD-Setup-<version>.exe` (Inno Setup), built by CI next to the other files of
  each release; it installs both apps (ttk and PySide6) and the command line for the current user;
  its uninstaller; a real install–use–uninstall check in CI.
- **Does not include:** code signing (ADR-0037, waiting for SignPath); an installer for Linux; automatic
  updates; changing the zip and the single `.exe` (they stay for whoever prefers them).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_017_*.py`) or a CI check.

- [x] **AC-01** One file, `ClearMD-Setup-<version>.exe`, built by the release workflow on Windows from
  the same programs as the other files, and released with them.
- [x] **AC-02** It installs for the current user only (no administrator) into
  `%LOCALAPPDATA%\Programs\ClearMD`. The person chooses the parts, each with a plain explanation of
  its trade-offs: the ttk app (the classic window, the default: the lightest), the PySide6 app (the
  modern window, a folder whose Qt libraries stay replaceable, LGPL) and the command line (no window).
  Ready-made choices (classic app only, modern app only, command line only, everything, custom); a
  choice with no part is refused. Each part's files come only if it is chosen; LICENSE and the
  notices always come.
- [x] **AC-03** Start menu shortcuts for each chosen part (and the uninstaller); the command line's
  shortcut opens a console with its help, not the program itself; a desktop shortcut only when the
  user ticks it; an optional, unticked PATH entry for the command line (announced on the page, removed
  by the uninstaller); the wizard in English or Spanish (the system's language), showing the license.
  Installing again with other parts removes the files and shortcuts of the parts no longer chosen.
- [x] **AC-04** Installing a newer version over an older one replaces it (no second entry, no leftovers
  from the old one); the app must be closed first (the installer says so).
- [x] **AC-05** The uninstaller is in "Installed apps" (name, version, publisher, icon) and in the Start
  menu; it removes every installed file, shortcut and registry entry; it asks whether to delete the
  settings too (default: keep them); it never touches the user's documents or ClearMD_Output folders.
- [x] **AC-06** CI on Windows proves it: a silent install of the default choice, a reinstall of all
  the parts (the PATH option ticked), the installed command line converts a real batch, the installed
  windows open and close (`--smoke`), a reinstall with only the modern app (the other parts and the
  PATH entry gone), a silent uninstall that keeps the settings, and nothing left in the install
  folder, the Start menu or the registry.
- [x] **AC-07** ADR-0040; version 0.12.0; the READMEs and the release notes say how to install and
  uninstall.
