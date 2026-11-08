# ADR-0051: PyPI with Trusted Publishing, off until the owner turns it on

- **Status:** accepted
- **Date:** 2026-11-08
- **Refines:** ADR-0018 (Python versions and PyPI at the end).

## Context

The last roadmap item is `pip install clearmd`. Publishing to PyPI needs an account that only the
owner can create. A token in the repository's secrets would be a credential that could leak.

## Decision

- **Trusted Publishing.** PyPI trusts this repository's `pypi.yml` workflow (environment
  `pypi`) through OIDC, so no token exists anywhere. The action is
  `pypa/gh-action-pypi-publish`, pinned by commit (v1.14.3, released 2026-10-20).
- **Off by default.** The publish job runs on a version tag only when the repository variable
  `PYPI_PUBLISH` is `true`. Until the owner sets it, tags still build and check the package.
- **Checked like a user would.** The wheel is installed alone in a fresh environment and
  converts a file.
- **PyPI's own page,** `packaging/pypi-readme.md`, with absolute links. The README's relative
  links and images do not work on PyPI.
- **The owner's steps** (once):
  1. create the project on PyPI as a pending publisher: owner `ClearNote97`, repository
     `ClearMD`, workflow `pypi.yml`, environment `pypi`;
  2. create the `pypi` environment on GitHub;
  3. set the variable `PYPI_PUBLISH` to `true`;
  4. tag the next version.

## Alternatives considered

- **An API token in secrets:** a credential to guard and rotate.
- **Publishing by hand with `uv publish`:** one more step to forget, and not repeatable.
