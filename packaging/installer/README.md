# The Windows installer and uninstaller

This folder holds the installer of ClearMD for Windows: `ClearMD-Setup-<version>.exe`, built by
the release workflow (ADR-0040, feature 017). It is a lesson too: each part of `clearmd.iss` says
what it does and why.

## What an installer is

A program that copies other programs' files into place and remembers what it did. Writing one by
hand is error-prone (shortcuts, the entry in "Installed apps", the PATH), so we use a tool:
**Inno Setup 6**, free and widely used. Inno Setup reads a script (`clearmd.iss`) and writes one
`.exe` that contains the files, the wizard the user sees, and an **uninstaller** (`unins000.exe`)
that knows exactly what was installed, so it can undo it.

## What this installer does

- **Per user, no administrator.** It goes to `%LOCALAPPDATA%\Programs\ClearMD`. No UAC prompt.
- **The user chooses the parts** (the first page after the folder). The classic app is the default
  (the lightest). The choices are the *components*:
  - `ttk`: the classic app (`ClearMD.exe`, one file, about 36 MB). The default.
  - `qt`: the modern app (`ClearMD-Qt\`, a folder, about 130 MB, its Qt libraries can be replaced).
  - `cli`: the command line (`clearmd-cli.exe`, no window, about 36 MB).

  The *types* are ready-made choices: classic app only (default), modern app only, command line
  only, everything, or custom. Both apps do exactly the same conversions with the same results.
- **Shortcuts** in the Start menu folder `ClearMD`: one per chosen part, and the uninstaller. The
  command line's shortcut opens the Windows command prompt with the help shown; it does not open
  the console program directly (it would close at once).
- **Desktop shortcuts** only when the task "A desktop shortcut for each part I chose" is ticked
  (it is not ticked by default).
- **PATH (optional, command line only, unticked by default).** Adds the install folder to the
  user's PATH, so `clearmd-cli` works in any terminal. It changes the user's environment, so it
  is announced on the page. The installer remembers that it added the entry (a marker in
  `HKCU\Software\ClearMD`): the uninstaller, and a re-install without the option, remove exactly
  that entry, never another one.
- **Languages:** English or Spanish, by the system's language.
- **License page:** the MIT license is shown and must be accepted.

## How the script is organised (`clearmd.iss`)

| Section | What it does |
|---|---|
| `[Setup]` | The identity (`AppId`, version, publisher), the folder, the privileges (`lowest` = no administrator), the output file, the icon, the license, and `CloseApplications` (if ClearMD is open, Windows lists it and asks to close it first). |
| `[Languages]` | English and Spanish. |
| `[CustomMessages]` | Every text we wrote, per language (the choices' names and explanations, the questions). |
| `[Types]` | The ready-made choices on the first wizard page. The first one is the default. |
| `[Components]` | The three parts. Each part's `Types:` says on which choices it is ticked. |
| `[Tasks]` | The two yes/no questions (desktop shortcuts, PATH). Both unticked by default. |
| `[Files]` | What is copied, and for which component (`Components:`). |
| `[Icons]` | The shortcuts, each for its component. |
| `[InstallDelete]` | Before copying: removes the files and shortcuts of components that a *previous* install left and that are now unticked (Inno does not do that by itself). |
| `[Code]` | The logic the sections cannot express: the explanation page, "at least one part" check, the PATH entry, the settings question on uninstall. |

**The AppId is fixed** (`{F1E42AD8-...}`). A new version with the same AppId replaces the old one
in place: same folder, same "Installed apps" entry. Never change it.

**Upgrades and re-installs:** running a newer installer (or the same one with other choices)
replaces the files of the chosen parts, removes the files of the parts no longer chosen, and
keeps the settings.

## What it writes

| Where | What |
|---|---|
| `%LOCALAPPDATA%\Programs\ClearMD\` | The chosen programs, `clearmd.ico`, `LICENSE`, `THIRD-PARTY-NOTICES.txt`, and `unins000.exe` with its data file. |
| `%APPDATA%\Microsoft\Windows\Start Menu\Programs\ClearMD\` | The shortcuts of the chosen parts, and "Uninstall ClearMD". |
| Desktop | Only with the desktop task: one shortcut per chosen part. |
| `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\{AppId}_is1` | The "Installed apps" entry: name, version, publisher, icon, uninstaller. |
| `HKCU\Environment\Path` | Only with the PATH task: one entry, the install folder. |
| `HKCU\Software\ClearMD` | Only with the PATH task: the marker that says the entry was added by ClearMD. |

## What the uninstaller undoes

- Every file and folder the installer wrote (Inno's own list), the shortcuts, and the
  "Installed apps" entry.
- The PATH entry, and its marker.
- **The settings folder** `%LOCALAPPDATA%\ClearMD` (`settings.toml`) is **asked about**, with
  "No" as the default. A silent uninstall keeps it, unless the command has `/REMOVESETTINGS`.
- **Never** the user's documents or the `ClearMD_Output` folders: the uninstaller does not know
  where they are, and it deletes nothing outside the list above.

## How it looks (`look/`, feature 019, ADR-0041)

The wizard wears ClearMD's colours and follows Windows' light or dark setting
([photographs](../../docs/screenshots/019/)). Two layers, both in `look/`:

- `brand.iss` — Inno's own directives: `WizardStyle=modern dynamic hidebevels` (light or dark like
  Windows, no grey lines), the background colours, and ClearMD's pictures in `images/`: the tall one
  beside Welcome and Finished, the mark in the top corner, one file per DPI (100–200 %) and theme.
  They are **drawn by a script**, never by hand: `uv run python tests/gui/make_installer_images.py`.
- `painted.iss` — Pascal code that paints Inno's controls: the header in the rail's ink with a teal
  line, the titles in teal, and the comparison page as one card per part. Windows still draws the
  buttons and the check list. The lesson it holds: a styled control keeps the style's painter for
  its background (`StyleElements - [seFont]` only); without it, Windows draws see-through text in black.

`/DLook=painted` is the default; `/DLook=brand` (pictures only) and `/DLook=plain` (Inno's own look)
still compile. After changing the look, run the **Installer look** workflow (Actions → Run workflow):
it compiles the three looks on Windows and photographs every page, light, dark and in Spanish.

## Build it locally (Windows)

1. Install Inno Setup 6.7 or newer (https://jrsoftware.org/isinfo.php), or `choco install innosetup --version=6.7.1`.
2. From the repository root, with the programs already built into `dist\` (see `packaging/`):

   ```
   uv run --no-default-groups --group build python packaging/notices.py > dist\installer\THIRD-PARTY-NOTICES.txt
   iscc /DAppVersion=0.12.0 packaging\installer\clearmd.iss
   ```

   The result is `dist\installer\ClearMD-Setup-0.12.0.exe`. `/DAppVersion` sets the version
   shown in "Installed apps" and in the file name; without it the version is `0.0.0-local`.
3. Check it the way CI does (silent installs, use, uninstall, nothing left):

   ```
   packaging\check_installer.ps1 -Installer dist\installer\ClearMD-Setup-0.12.0.exe -Version 0.12.0
   ```

   The check changes your user's installed programs and PATH, and it deletes
   `%LOCALAPPDATA%\ClearMD`. Run it on a machine where you do not keep ClearMD's settings.

## Not done yet

- The installer is **not signed** (ADR-0037 waits for SignPath). Windows SmartScreen warns on
  first run, as for the other files.
- Releases only: the installer is built on each tag and on manual runs of the release workflow.
