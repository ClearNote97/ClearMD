# ADR-0012: Bilingual app with TOML message catalogs and one shared settings file

- **Status:** accepted; language resolution superseded by ADR-0017
- **Date:** 2026-10-24

## Context

ClearMD targets non-technical users first (ADR-0013) and its audience is largely Spanish-speaking, while the
repository is in English (ADR-0011). The app must speak **English and Spanish**, selectable by the user.
There are four interfaces (CLI and three GUIs, ADR-0001) that must show the same texts and honor the same
preferences.

## Decision

### Message catalogs

- Every user-facing text (CLI output, GUI labels, error messages, the batch report) comes from a **message
  catalog**, never from a string literal in the code. This applies from feature 001 on.
- One TOML file per language: `src/clearmd/i18n/en.toml` and `es.toml`. Keys are stable identifiers
  (`batch.progress`, `error.password_protected`); values may contain named placeholders (`{count}`).
- A test fails if a key exists in one catalog but not in the other, or if the placeholders of a key differ
  between languages. A missing translation cannot reach a release.
- Language resolution, first match wins: explicit choice for the run (CLI `--lang`) → settings → operating
  system locale → English.

### One settings file for every interface

- A single `settings.toml` in the user configuration directory (`platformdirs`, ADR-0002), shared by the CLI
  and the three GUIs: changing the language in one interface changes it in all.
- Settings and their defaults: language (`auto`), theme (`system`), open the output folder when done (`true`,
  GUIs only; the CLI uses `--open`), when an output already exists (`ask`), include subfolders (`true`),
  HTML strategy (`full`), show the welcome screen (`true`).
- A missing, unreadable or invalid settings file never stops the app: it falls back to the defaults and says
  so. The GUIs offer "Restore defaults".
- Deliberately **not** configurable: the `ClearMD_Output` folder name, following symlinks, hidden files and
  the size limit (ADR-0010). A user who changes them would lose track of where results go, or weaken safety.

## Consequences

- **Gains:** no dependency and no compile step for translations; the parity test makes the bilingual promise
  verifiable; all interfaces behave alike.
- **Costs:** every new text needs two translations in the same change; the catalog keys become a contract
  between core, presenter and GUIs.

## Alternatives considered

- **gettext (`.po` / `.mo`):** the industry standard and friendly to translation tools, but it needs a compile
  step and extra tooling, and its strengths (many languages, external translators) do not apply to a
  two-language app. Rejected for now; catalogs are plain data and could be converted later.
- **English only in v1:** rejected; the main audience reads Spanish.
