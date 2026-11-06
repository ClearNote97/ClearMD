# Plan — Feature 019: The installer's look

> The **how**. Criteria: [`spec.md`](./spec.md). Decisions: ADR-0040 (the installer), ADR-0041 (its look),
> ADR-0027 (the logo and palette).

- `tests/gui/drawing/installer.py` + `tests/gui/make_installer_images.py` — draw the pictures into
  `packaging/installer/images/` from the logo's geometry and the palette; `tests/unit/test_installer_images.py`
  fails when the committed files and the script disagree.
- `packaging/installer/look/brand.iss` — option 1, Inno's directives: `WizardStyle=modern dynamic
  hidebevels`, the background colours, the pictures (light and `DynamicDark`).
- `packaging/installer/look/painted.iss` — option 2, Pascal code: the header in the rail's ink with a
  teal line, the titles in teal, the comparison page as cards. Lesson: a styled label keeps the
  style's painter (remove only `seFont`); without it Windows draws see-through text in black.
- `packaging/installer/clearmd.iss` — `#define Look "painted"` by default; `/DLook=brand|plain` for the
  other looks; Spanish Welcome/Finished titles in Title Case (`[Messages]`).
- `.github/workflows/installer-look.yml` + `packaging/installer/look/shoot.ps1` — on Windows, the
  three looks compiled from the published programs and every page photographed (light, dark, Spanish).
- `.github/workflows/release.yml` — Inno Setup pinned to 6.7.1, with a version check.
