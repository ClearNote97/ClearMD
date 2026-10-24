# ADR-0004: Hybrid engine — markitdown behind a port + own converters

- **Status:** accepted
- **Date:** 2026-10-24

## Context

Microsoft publishes `markitdown` (MIT), which converts many formats to Markdown: PDF, docx, pptx, xlsx, HTML,
CSV, EPUB, Jupyter notebooks, Outlook emails (`.msg`), ZIP, RSS and plain text. Writing all of that from
scratch would mean reinventing a mature library. But depending on it directly also carries risks:

- it is at version **0.1.9** (pre-1.0): its API may change between minor versions;
- it requires Python `<3.15`;
- its core always brings `magika` (content-based type detection), which in turn brings `onnxruntime`;
- it does **not** cover `.tex`, OpenDocument (`.odt`), `.rtf`, `.eml` or subtitles;
- some of its extras send data to the cloud (see ADR-0005).

## Decision

- The core defines its own port, `DocumentConverter`. No module outside `clearmd.converters`
  imports markitdown.
- `markitdown[pdf,docx,pptx,xlsx]==0.1.9` is used as an adapter for the formats it already handles well. The
  **exact version** is pinned: upgrading it is a deliberate change, with tests.
- ClearMD provides **own converters** for what markitdown does not cover or covers only partially: `.tex`, `.odt` and
  HTML in "article mode" (details in ADR-0006).

## Consequences

- **Gains:** broad format coverage from day one; the dependency stays isolated and can be
  replaced without touching the core; the own converters add value where there is no alternative.
- **Costs:** `magika` + `onnxruntime` add weight to every executable; size has to be monitored in CI.
  The pinned version requires reviewing upgrades by hand.

## Alternatives considered

- **Everything from scratch:** rejected; months of work to match formats that markitdown already handles.
- **markitdown only, with no port or own converters:** rejected; it couples the core to a pre-1.0 API and adds
  nothing beyond the library.
