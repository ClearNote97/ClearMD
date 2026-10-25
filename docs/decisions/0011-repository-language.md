# ADR-0011: Repository language — English, with a Spanish README

- **Status:** accepted; the list of verbatim template files corrected by ADR-0014 (`spec_agents/`)
- **Date:** 2026-10-24

## Context

ClearMD is a public portfolio project. The first round of documentation (ADRs 0001–0010, constitution,
README) was written in Spanish, the author's working language. English reaches a wider audience on GitHub
(recruiters, contributors, the Python community), while Spanish is part of the project's identity and of the
template it was born from.

The repository mixes two kinds of text:

- **Template doctrine**, shared verbatim across the author's repositories: `README_AGENTS.md`,
  `spec/constitution/01_principles.md`, the default-stack tables of `spec/constitution/03_stack.md` and the
  agent roster in `spec_agents/`.
- **Project text**, written for ClearMD.

## Decision

- **Project text is in English:** README, ADRs, architecture, constitution files written for ClearMD
  (`00_purpose`, `02_scope`, the ClearMD section of `03_stack`), roadmap, feature specs, contracts,
  `AGENTS.md`, folder READMEs, code, comments and configuration comments.
- **A Spanish README** (`README.es.md`) mirrors the English one, linked from its first line.
- **Template doctrine stays in Spanish, untouched**, so it can still be compared with and updated from the
  template.
- ADRs 0001–0010 were translated faithfully; their decisions did not change.

The language of the **app itself** is a separate decision (ADR-0012).

## Consequences

- **Gains:** the project is readable by an international audience; Spanish-speaking visitors still have a
  full README in their language.
- **Costs:** two READMEs to keep in sync; a few files mix languages (the ClearMD section of `03_stack.md` sits
  above the template's Spanish tables). Every README change must update both versions.
