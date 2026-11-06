# ADR-0041: The installer looks like ClearMD

- **Status:** accepted
- **Date:** 2026-11-06
- **Refines:** ADR-0040 (the installer), ADR-0027 (the logo and palette).

## Context

The first installer (v0.12.0) used Inno Setup's own pictures (a box with a disc) and colours: it
looked like any installer, not like ClearMD. Three ways were weighed: (1) Inno's directives for
pictures and colours; (2) on top of that, Pascal code that paints Inno's controls; (3) a different
installer or a third-party skin. Option 3 was rejected: it gives up Inno's tested upgrade and
uninstall, and adds an unsigned component.

## Decision

- **Option 2**, chosen by the owner from photographs of the three looks taken on Windows CI.
- Inno Setup **6.7** (dark mode since 6.6, custom background colours since 6.7): `WizardStyle=modern
  dynamic hidebevels` follows Windows' light or dark setting, like the apps.
- The pictures are **drawn by a script** from the logo's geometry and the palette, one file per DPI
  and theme; a test keeps them in step with the script.
- The header, titles and the comparison page are **painted with the apps' palette**; each part is a
  card, as in the apps. The buttons and the check list stay native (Windows draws them; Inno's style
  adapts them to the theme).
- Titles in **Title Case** (the owner's rule for every title).
- `/DLook=brand|plain` still compiles the other looks; the `Installer look` workflow photographs all
  three, run by hand after a change.

## Consequences

- The release needs Inno Setup 6.7 or newer (preinstalled on the runner; the fallback is pinned to
  6.7.1 and the version is checked).
- Lesson: a label painted by hand must keep the style's painter (`StyleElements - [seFont]`); removing
  `seClient` too makes Windows draw see-through text in black.

## Amendment (v1.0.1, 2026-11-06)

The owner found the dark wizard too heavy: the installer is **always light**
(`WizardStyle=modern light hidebevels`), whatever Windows' setting. The dark pictures and the
`DynamicDark` directives stay in place, unused, should a dark wizard come back.
