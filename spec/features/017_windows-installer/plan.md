# Plan — Feature 017: The Windows installer and uninstaller

> The **how**. Criteria: [`spec.md`](./spec.md). Decisions: ADR-0028 (CI and the executables),
> ADR-0037 (signing), ADR-0038 (PySide6 delivery), ADR-0040 (the installer).

- `packaging/installer/clearmd.iss` — the Inno Setup script: per-user install (`PrivilegesRequired=lowest`),
  `{localappdata}\Programs\ClearMD`, a fixed `AppId` (so a new version replaces the old one), the files
  from `dist/` (ClearMD.exe, clearmd-cli.exe, ClearMD-Qt\), Start menu and optional desktop shortcuts,
  English and Spanish, the MIT license page, a close-the-app check, and the uninstall step that asks
  about the settings folder (`%LOCALAPPDATA%\ClearMD`).
- `packaging/installer/README.md` — what each part of the script does (it is also a lesson).
- `.github/workflows/release.yml` — Windows job: install a pinned Inno Setup, compile the script with
  the version, run `packaging/check_installer.ps1` (install → use → uninstall → nothing left), upload.
- `packaging/package.sh` — `release/ClearMD-Setup-<version>.exe`.
- `tests/acceptance/test_017_*.py` — what the repository can check (the script's settings, the
  workflow's steps, the check script's steps); the real proof is the CI run.
