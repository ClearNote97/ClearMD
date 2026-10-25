# ADR-0019: `OutputMD/` for converted files, and room for the v2 tools (merge and split)

- **Status:** accepted
- **Date:** 2026-10-25
- **Supersedes:** the name of the results folder in ADR-0016 (`Output/` → `OutputMD/`).

## Context

Two tools were proposed for a second version of ClearMD:

- **Merge:** join several converted `.md` files into one — the natural input for an LLM chat, one of the
  personas of `00_purpose`.
- **Split:** cut a large **source document** (a 2,000-page PDF) into N similar parts. The benchmark of feature
  001 shows PDF as the time bottleneck (about 10 text pages per second), so a split PDF fits the time limit of
  ADR-0015 part by part.

Each tool produces its own kind of result, and a generic `Output/` folder would leave no clean place for them.
No code depends on the name yet beyond feature 001's first slice, so renaming now is cheap.

## Decision

- Converted Markdown goes to **`ClearMD_Output/OutputMD/`**. The rest of ADR-0016 stands.
- The v2 tools, when they come, live in one window **"Tools"**, with two tabs **Merge | Split** (not "Edit
  File": ClearMD does not edit content, `02_scope`), and write next to the conversion results:

  ```
  ClearMD_Output/
    Resumen_ClearMD.md
    OutputMD/      converted Markdown (v1)
    OutputSep/     parts of split source documents (v2)
    OutputUnif/    merged Markdown files (v2)
  ```

- **Merge** takes the `.md` files of the last batch by default, and lets the user pick any `.md` files (for
  example from earlier batches) with an "Add .md files" button.
- **Split** cuts the **source document** into the number of parts the user chooses, in the same format,
  starting with the formats where it is natural (PDF by pages; csv/txt by lines; xlsx by rows or sheets).
- Both tools are **out of v1**: they get their own feature specs after the GUIs (roadmap, "Version 2").

## Consequences

- **Gains:** one predictable layout for every kind of result; v1 does not have to change again when v2 lands.
- **Costs:** a slightly longer folder name; the v2 tools need specs of their own (merge order and headers;
  split units per format).

## Alternatives considered

- **Keep `Output/` and add `Split/` and `Merge/` later:** rejected; the three folders read better as a family.
- **Automatic chunked conversion instead of a split tool:** not excluded — it can be added for PDF without a
  user-facing tool; the v2 spec decides with the benchmark data.
