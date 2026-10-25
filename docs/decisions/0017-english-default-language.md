# ADR-0017: English by default, no operating-system language detection

- **Status:** accepted
- **Date:** 2026-10-25
- **Supersedes:** the language resolution order and the `language = "auto"` default of ADR-0012.

## Context

ADR-0012 resolved the language as `--lang` → settings → operating-system locale → English. Detecting the
locale is unreliable on Windows, the main platform of the primary persona: `locale.getlocale()` may return
names such as `Spanish_Colombia` instead of `es_CO`, so a simple `es*` rule fails, and getting it right
needs Windows-specific calls. A wrong guess on first run is worse than a predictable default.

## Decision

- Resolution: `--lang` for one run → the `language` setting → **English**.
- The `language` setting accepts `en` or `es`; its default is `en`. There is no `auto`.
- The first-run welcome and the help window say, in English and in Spanish, how to switch the language in the
  settings, so a Spanish speaker finds the way on the first screen.
- argparse's own messages (`usage:`, `error: …`) stay in English for now: a known, accepted gap.

## Consequences

- **Gains:** predictable behavior on every OS; no platform-specific code; nothing to test on a real Windows
  locale.
- **Costs:** Spanish-speaking users change one setting once.

## Alternatives considered

- **Locale detection with Windows APIs (`GetUserDefaultLocaleName`):** rejected for now; more code and tests
  for a choice the user makes once.
