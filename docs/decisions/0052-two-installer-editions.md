# ADR-0052: Two installer editions from one script

- **Status:** accepted
- **Date:** 2026-11-09
- **Amends:** ADR-0040 (one installer with every part). The portable executables and the zips stay.
- **Origin:** the audit of 2.8.1 (`docs/audit/2026-11-08-audit-boards.md`, recommendation 9), and
  the doubts board of 2026-11-09 (D1).

## Context

`ClearMD-Setup-2.8.1.exe` weighed about 176 MB to install, by default, the Classic App: about
37 MB. The first thing a person does with ClearMD is download it, often on a slow or metered
connection. The owner keeps the three windows (they are also a development exercise), so the
other parts must stay available. The lead cannot run Windows locally: only CI can check an
installer.

## Decision

- **One script, two editions**, chosen at compile time (`ISCC /DEdition=Light|Full`; no default,
  the compiler stops without it):
  - **Light** — `ClearMD-Setup-<version>.exe`: the Classic App alone, no page of choices, no PATH
    option. The name people already download is the light one.
  - **Full** — `ClearMD-Setup-Full-<version>.exe`: today's installer, every part and every type.
- Both share the AppId, the folder and the "Installed apps" entry.
- **The light edition never touches the other parts.** If the registered install has the Modern
  App, the Mobile-Style App or the Command Line, it tells the person which file updates
  everything and stops without changing anything (silent: a non-zero exit code). It has none of
  the code that removes other parts.
- The release notes and the READMEs say first which file most people need.
- CI builds both, limits their sizes (light ≤ 45 MB, full ≤ 190 MB), installs the light one,
  updates over the real 2.8.1 installer (the light one must refuse over every part; the full one
  must leave no shortcut with an old name), and a manual run of the release workflow on a
  branch is required before the tag.

## Consequences

- **Gains:** the recommended download weighs what it installs; nobody with the other parts can
  lose them by downloading the obvious file.
- **Costs:** two unsigned installers (two SmartScreen warnings while signing is pending); every
  component-dependent line of the script lives inside `#if Edition == "Full"` (a test checks it);
  the Command Line is only in the full edition and as its own executable (the doubts board's
  dissent wanted it in the light one too).
