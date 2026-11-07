# Feature 022 — The files a public project carries; checksums with every release

## Goal

ClearMD is a public repository. Visitors look for the usual files: how to report a security problem,
how to contribute, the rules of conduct, the forms for an issue, the history of versions and how to
cite it. GitHub lists these files under *Insights → Community standards*. Each release also gets
`SHA256SUMS.txt`, so anyone can check that a download is the file ClearMD published.

## Scope

- **Includes:** `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`,
  `CITATION.cff`, the issue forms under `.github/ISSUE_TEMPLATE/`, and the checksums step of the
  Release workflow. It also covers where they are mentioned: the release notes and the READMEs.
- **Does not include:** code signing (see `CODE_SIGNING.md`); the repository's social preview image
  and website field, which are set on GitHub's settings page by the owner.

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_022_*.py`).

- [x] **AC-01** `SECURITY.md` names the supported versions, sends reports to GitHub's private
  vulnerability reporting (never a public issue), and explains how to check a download against
  `SHA256SUMS.txt` on Linux and Windows.
- [x] **AC-02** `CONTRIBUTING.md` explains the spec-first process, the four checks and the rules a
  pull request follows. It links the Code of Conduct, the security policy and the license.
- [x] **AC-03** `CODE_OF_CONDUCT.md` adopts the Contributor Covenant 2.1 and says how to report a
  problem.
- [x] **AC-04** Issues open from two forms, a bug report and a feature request. Blank issues are
  off, and security problems are sent to the private report.
- [x] **AC-05** `CHANGELOG.md` points to the release notes. `CITATION.cff` carries the version in
  `pyproject.toml`.
- [x] **AC-06** The Release workflow writes `SHA256SUMS.txt`, one line per published file and
  excluding itself, and publishes it with the release. The release notes and both READMEs say how
  to use it.
