# ADR-0037: The Windows executables signed by SignPath

- **Status:** accepted
- **Date:** 2026-11-04
- **Refines:** ADR-0028 (CI and the executables: code signing was deferred until the repository
  was public).

## Context

An unsigned Windows executable makes SmartScreen warn ("Windows protected your PC"); a
non-technical user stops there. The budget is zero (`spec/constitution/02_scope.md`). The
repository is public since 2026-11-04, so SignPath Foundation's free certificate for open source
can be requested. The request is the author's: SignPath Foundation reviews the project and grants
it a project in its organization; that takes days.

## Decision

- **The two Windows executables are signed on SignPath, from the release workflow**, after the
  build and before they are checked and packaged: so the checks run the signed files.
  - The unsigned files go up as an artifact; SignPath's action (pinned by commit) signs them,
    waits and writes them back to `dist/`; `Get-AuthenticodeSignature` must say *Valid* for both.
  - The connection is the repository's: variables `SIGNPATH_ORGANIZATION_ID`,
    `SIGNPATH_PROJECT_SLUG`, `SIGNPATH_SIGNING_POLICY_SLUG`, secret `SIGNPATH_API_TOKEN`.
- **Until SignPath is set up, the build is as before:** each signing step runs only when
  `SIGNPATH_ORGANIZATION_ID` is set. The release notes keep saying how to pass the warning until
  the first signed release.
- **The code signing policy SignPath Foundation asks for is [`CODE_SIGNING.md`](../../CODE_SIGNING.md)**,
  linked from both READMEs: what is signed, the team roles, the privacy policy.
- **The Linux archive is not signed:** Linux has no such warning.
- **Each Windows executable carries its product name and version** (`packaging/version_info.py`,
  from `pyproject.toml`): SignPath's artifact configuration requires them; every Windows build
  checks them.
- **SignPath Foundation's terms** (signpath.org/terms) asked too: "Code signing policy" named on
  the home and release pages; Authors, Reviewers and Approvers; uninstall instructions.

## Consequences

- With signing, SmartScreen knows the publisher; its reputation still grows with downloads, so
  the very first signed releases may warn less, not never.
- Each release waits for the author's approval on SignPath (manual approval of the signing
  request), so a release can no longer finish unattended.
- The author does once: apply at signpath.org, then add the variables and the secret in the
  repository's settings (*Settings → Secrets and variables → Actions*).
