# Plan — Feature 022: community files and release checksums

> The **how**. Criteria: [`spec.md`](./spec.md).

- Repository root: `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`,
  `CITATION.cff`.
- `.github/ISSUE_TEMPLATE/`: `bug_report.yml`, `feature_request.yml` and `config.yml` (blank issues
  off; a link to the private security report).
- `.github/workflows/release.yml`, `publish` job: `sha256sum` over the downloaded files, written
  outside the folder first so the list does not include itself, then published with them.
- `packaging/RELEASE_NOTES.md`, `README.md`, `README.es.md`: one line on checking a download.
- On GitHub: private vulnerability reporting turned on, so `SECURITY.md`'s link works.
- A version bump keeps `CITATION.cff` in step (AC-05 checks it).
