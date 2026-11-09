# Feature 037 — A light installer and a full one (audit 9, doubts board D1, ADR-0052)

## Goal

The recommended download weighs what it installs. The audit of 2.8.1 measured about 176 MB to
install about 37 MB by default. Two editions of the one installer script: the light one keeps the
name people already download.

## Acceptance criteria (what MUST be true)

- [x] **AC-01** One script compiles two installers, chosen at compile time with no default:
  `ClearMD-Setup-<version>.exe` (light: the Classic App alone, no page of choices) and
  `ClearMD-Setup-Full-<version>.exe` (every part, as before).
- [x] **AC-02** The light edition never touches the other parts: none of its lines can install or
  remove them, and over an install that has them it says which file to use and stops without
  changing anything.
- [x] **AC-03** CI builds and checks both: size limits (light ≤ 45 MB, full ≤ 190 MB), the light
  install and uninstall, and updates over the real 2.8.1 installer (the light one refuses over
  every part; the full one leaves no shortcut with an old name; the light one updates a Classic
  App alone). The release ships both.
- [x] **AC-04** The release notes and both READMEs say first which file most people need.
