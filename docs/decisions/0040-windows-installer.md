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
- **The person chooses the parts.** Three components: the ttk app, the PySide6 app and the command
  line. Ready-made choices on the first page: the classic app only (the default, the lightest), the
  modern app only, the command line only, everything, or custom. Each part is explained in plain
  language, in English and Spanish, on a page before the choice (the classic app is recommended for
  most people; the modern one looks smoother at the cost of space). A choice with no part is refused.
  Only the chosen parts get files and shortcuts. The PySide6 folder keeps its Qt libraries as files
  (still replaceable, LGPL). The command line's Start menu entry opens a console with its help. An
  optional, unticked PATH entry for the command line is removed by the uninstaller.
- **A re-install follows the choice:** the files and shortcuts of parts no longer chosen are removed;
  the PATH entry follows the same rule.
- **A fixed AppId:** a newer version replaces the older one in place.
- **The uninstaller** removes what the installer wrote (files, shortcuts, its registry entry), asks
  before deleting the settings folder (kept by default), and never touches the user's documents.
- **Proved in CI:** install silently, use what was installed, uninstall silently, check that nothing
  is left.
- **Upgrade (AC-04):** CI installs an older build of the same script (AppId unchanged), then
  installs the current one over it: one Installed apps entry, the new version's name, one uninstaller,
  no leftover shortcut. The older build here carries the same programs (only the version differs).
- The zip and the single `.exe` stay in the release for whoever prefers no installer.

## Consequences

- **Gains:** an ordinary install and uninstall for non-technical users; the folder question disappears.
- **Costs:** one more build step on Windows; unsigned, so SmartScreen still warns (ADR-0037).
- **Running apps:** the installer's `CloseApplications=yes` makes Windows' Restart Manager ask the
  user to close a running ClearMD before it replaces the files. CI does not test that prompt (silent
  installs); the mechanism is Inno Setup's own.
- **TODO (not done in feature 017):** sign the installer itself. The programs inside are signed
  through SignPath (ADR-0037); the setup file is not, yet. Signing it is a later step of the release
  workflow, after the signing service accepts it.
