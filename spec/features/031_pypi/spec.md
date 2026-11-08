# Feature 031 — Ready for PyPI

## Goal

`pip install clearmd` and `uv tool install clearmd` (ADR-0018 left PyPI for the end). Everything
the repository can do is done here:
- the package's metadata;
- its own page for PyPI;
- a build checked on every tag;
- a publish job with Trusted Publishing, so no token is ever stored.

Publishing needs the owner's PyPI account. The job stays off until the owner turns it on
(ADR-0051).

## Acceptance criteria (what MUST be true)

- [x] **AC-01** The metadata shows ClearMD as it is now: the description of the toolkit,
  keywords, classifiers (platforms, Python versions, topic), and the project's links (source,
  issues, changelog).
- [x] **AC-02** PyPI's page (`packaging/pypi-readme.md`) has only absolute links. It says what
  ClearMD does, how to install and use it from the command line, and where the windows'
  extras and the Windows installer are.
- [x] **AC-03** On every version tag, and by hand, CI builds the sdist and the wheel. It then
  installs the wheel alone in a fresh environment and converts a file with it.
- [x] **AC-04** A publish job sends the built files to PyPI with Trusted Publishing. It runs on a
  version tag only when the repository variable `PYPI_PUBLISH` is `true`, so it is off until the
  owner adds the trusted publisher. Its action is pinned by commit.
