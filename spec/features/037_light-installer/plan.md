# Plan — Feature 037

- `packaging/installer/clearmd.iss`: `#define Edition` required; every line about the Modern App,
  the Mobile-Style App or the Command Line inside `#if Edition == "Full"`; the light edition skips
  the components page, has a fixed Classic App component, a finish text that names the full
  installer, and an `InitializeSetup` that reads the uninstall key's selected components.
- `.github/workflows/release.yml`: both editions compiled, the old one as Full, the real 2.8.1
  installer downloaded; `packaging/check_installer.ps1`: `-LightInstaller`, `-ReleasedInstaller`,
  steps L1–L4 and the size limits; `packaging/package.sh`: one of each.
- `installer-look.yml`: the light edition photographed too.
- Verified by a manual run of the release workflow on the branch before the tag.
