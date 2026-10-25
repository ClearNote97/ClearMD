# ADR-0021: Content detection only for files without an extension

- **Status:** accepted
- **Date:** 2026-10-25
- **Supersedes:** in ADR-0010, using magika for files whose extension is unknown.

## Context

ADR-0010 chained extension → content detection for any file the extension could not classify. Implementing it
(feature 001, T10) showed the cost: magika labels most text-like files as plain text, so a `.tex` source, a `.log`
or a `.yaml` became "converted" Markdown that was just the file copied, and a folder of code or configuration
filled `OutputMD/` with noise. An intermediate rule (accept only real documents with an unknown extension) worked
but was hard to explain to a non-technical user.

## Decision

- **Known extension:** converted by its format.
- **No extension** (`scan`, `README`): magika decides, plain text included.
- **Unknown extension** (`.dat`, `.log`, `.tex` until feature 002): "unsupported format", without looking
  inside. What is not contemplated is not accepted.

## Consequences

- **Gains:** a rule that fits in one line of the help; magika runs less often; no noise from source or
  configuration files.
- **Costs:** a document renamed with a wrong extension (a docx saved as `report.dat`) is not converted; the user
  has to fix its name.

## Alternatives considered

- **Content for every unknown extension (ADR-0010 as written):** rejected; it converts source and logs.
- **Content only when it is a real document:** rejected; correct but hard to predict for the user.
