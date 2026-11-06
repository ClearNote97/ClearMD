# ADR-0040: A Windows installer and uninstaller, with Inno Setup

- **Status:** accepted
- **Date:** 2026-11-06
- **Refines:** ADR-0028 (the executables), ADR-0038 (the PySide6 app as a folder).

## Context

The PySide6 app is a folder inside a zip (ADR-0038, LGPL): the owner, opening only the `.exe`, got
"DLL not found". Non-technical users expect an installer: one file, the app in the Start menu, and a
way to remove it from "Installed apps". The budget is zero.

## Decision

- **Inno Setup** builds `ClearMD-Setup-<version>.exe` on the Windows CI runner. It is free (its own
  permissive license), widely used, scriptable (`packaging/installer/clearmd.iss`), and writes the
  uninstaller itself. Rejected: NSIS (lower-level scripting), WiX/MSI (heavy for one user, built for
  administrators), MSIX (needs signing to install at all).
- **Per user, no administrator:** `%LOCALAPPDATA%\Programs\ClearMD`, as modern apps do; nothing in the
  system's Program Files, no UAC prompt.
- **Everything in one installer:** both apps (ttk and PySide6) and the command line, so the owner can
  compare them; Start menu shortcuts for both, a desktop one if ticked. The PySide6 folder keeps its Qt
  libraries as files (still replaceable, LGPL).
- **A fixed AppId:** a newer version replaces the older one in place.
- **The uninstaller** removes what the installer wrote (files, shortcuts, its registry entry), asks
  before deleting the settings folder (kept by default), and never touches the user's documents.
- **Proved in CI:** install silently, use what was installed, uninstall silently, check that nothing
  is left.
- The zip and the single `.exe` stay in the release for whoever prefers no installer.

## Consequences

- **Gains:** an ordinary install and uninstall for non-technical users; the folder question disappears.
- **Costs:** one more build step on Windows; unsigned, so SmartScreen still warns (ADR-0037).
