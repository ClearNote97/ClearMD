# Feature 019 — The installer's look

## Goal

The installer looks like ClearMD, not like any Inno Setup wizard: the same colours, mark and cards as
the apps, in light and dark Windows, so the first thing a person sees of ClearMD is ClearMD (ADR-0041).

## Scope

- **Includes:** ClearMD's pictures (the tall one beside Welcome and Finished, the mark in the top
  corner) for every DPI and both themes; the wizard following Windows' light or dark setting; the
  header, titles and the comparison page painted with the apps' palette (option 2, chosen by the
  owner from photographs of three looks); titles in Title Case; a CI workflow that photographs the
  looks on Windows.
- **Does not include:** restyling the native controls Windows draws (buttons, check list, combo box)
  beyond what Inno's own styles do; a custom VCL style file; any change to what the installer
  installs or how it uninstalls (feature 017).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_019_*.py`) or a CI check.

- [x] **AC-01** The painted look is the installer's default and the release builds it; the release
  needs Inno Setup 6.7 or newer and says so when it is older.
- [x] **AC-02** ClearMD's pictures replace Inno's (the tall picture and the top-corner mark), one file
  per DPI (100, 125, 150, 200 %) in light and dark, drawn by a script (never by hand) and checked
  against it; the wizard follows Windows' light or dark setting; the Welcome page shows.
- [x] **AC-03** Every colour the look uses comes from the apps' palette (`frontend/design/palette.py`).
- [x] **AC-04** The comparison page shows one card per part (title, size, a short explanation), the
  recommended one marked; English and Spanish.
- [x] **AC-05** The installer's own titles are in Title Case (connectors in lower case), in English
  and Spanish.
- [x] **AC-06** A workflow photographs every page of the three looks on Windows, light and dark, and
  in Spanish, and keeps the installers and the photographs as artifacts.
- [x] **AC-07** ADR-0041; version 0.13.0; the release notes and the installer's README describe it;
  photographs in `docs/screenshots/019/`.
