# ADR-0048: Incremental mode compares an original's date with its result's

- **Status:** accepted
- **Date:** 2026-11-08
- **Refines:** ADR-0016 (results and their summary), ADR-0012 (settings).

## Context

Converting a folder again converts everything again, or keeps every existing result. The
roadmap asked for "skip the files unchanged since the last run". ClearMD keeps no database
(`02_scope`), and the user should not have to learn a new mode.

## Decision

- **A fourth answer to a question ClearMD already asks.** "When a Result Already Exists" gains
  **Replace it if the original changed** (`changed`). It is in Settings, on Review when Review
  asks, and on the command line as `--changed` (never together with `--overwrite` or `--skip`).
- **The rule:** an original modified after its result was written has changed
  (`st_mtime` of the source > that of the result). For Split, the result is the parts' folder.
  When either date cannot be read, the safe answer is a fresh result.
- Merge always writes a new file, so the rule does not apply to it.
- An unchanged result is kept and counted as kept, as with "Keep it".

## Consequences

- **Gains:** no stored state; the same summary; a choice that reads as plain words.
- **Cost:** a copy that keeps an older modification date, or an edited result, can mislead the
  rule. "Replace it" is always there to start fresh.

## Alternatives considered

- **A manifest of hashes in `ClearMD_Output`:** exact, but it is state to keep in step, and a new
  file next to the user's results.
- **A separate "incremental" switch:** two settings answering the same question.
