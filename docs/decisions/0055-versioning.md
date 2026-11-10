# ADR-0055: What each version number promises

- **Status:** accepted
- **Date:** 2026-11-09
- **Origin:** the owner's question, while applying the fourth audit: when is a new major version needed?

## Context

ClearMD followed "major for a big product step" (1.0.0 with the third window, 2.0.0 with the start
screen and Split). Meanwhile some 2.x minor versions changed what an existing command produces (web
pages convert their article by default in 2.12.0; a result without text exits with code 1 in
2.13.0). Published versions are not renumbered: PyPI forbids it and the installer updates by number.

## Decision

Semantic versioning, applied to ClearMD's **public contract**:

- the command line's options, their defaults and its exit codes;
- the names and folders of the results (`ClearMD_Output`, `OutputMD`, `OutputSep`, `OutputUnif`, the
  parts' and summaries' names) and the settings file's keys;
- the Python package's public API (`clearmd.backend.api`) and where the installer puts the apps;
- what a format's result contains, when a person or a script may depend on it.

**Major** (3.0.0): something in the contract stops working as before (an option removed or
renamed, a folder renamed, a format's result rewritten, as replacing markitdown will).
**Minor** (2.13.0): something new and compatible, or a correction of something that was false (a
blank result called "converted"), always told in the release notes as a change of behaviour.
**Patch** (2.13.1): fixes only, nothing anyone could depend on changes.

## Consequences

- 3.0.0 is the version that replaces markitdown for Word and PowerPoint.
- Release notes have a "Changes in behaviour" line whenever a minor version corrects something.
- A test that pins the contract (options, exit codes, folder names) is worth adding with 3.0.0.
