# Feature 006b — Code signing of the Windows executables

## Goal

The Windows executables signed with SignPath Foundation's free certificate (ADR-0037), so
SmartScreen does not scare non-technical users. Part of 006b (hardening); the Job Object, the
`uv.lock` check and the size metric stay for later.

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_006b_code_signing.py`).

- [x] **AC-01** The release workflow signs both Windows executables on SignPath after the build
  and before the checks, and waits for the signed files.
- [x] **AC-02** With no SignPath set up (no `SIGNPATH_ORGANIZATION_ID`), the build is as before.
- [x] **AC-03** A signed build is verified: both signatures are *Valid*.
- [x] **AC-04** The code signing policy (`CODE_SIGNING.md`) says what SignPath Foundation asks
  for, and both READMEs link to it.
- [x] **AC-05** ADR-0037.
- [x] **AC-06** Both Windows executables carry the product name `ClearMD` and the project's
  version (SignPath checks them); the release build verifies it on every Windows build.
- [x] **AC-07** "Code signing policy" is named on the home page (both READMEs) and on each
  release's page; the policy names the Authors, Reviewers and Approvers, and the third-party
  components' privacy.
- [x] **AC-08** How to uninstall is told: the executable, the command line and the settings folder.

## Does not include

- The request to SignPath Foundation and the repository's variables and secret: the author's.
- A new version: the first signed build comes with the next release.
