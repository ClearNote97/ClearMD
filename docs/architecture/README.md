# docs/architecture — System design

ClearMD follows a **ports and adapters** architecture (ADR-0001): a core that knows neither the GUIs
nor the conversion libraries, surrounded by interchangeable adapters.

```
              Input adapters                                      Conversion adapters
   ┌──────────────────────────────────┐                   ┌──────────────────────────────────┐
   │ cli   ttk   qt   flet            │                   │ markitdown (pdf, docx, pptx,     │
   │   (each GUI is a view)           │                   │   xlsx, html, csv, epub, ipynb)  │
   └───────────────┬──────────────────┘                   │ tex  (pylatexenc + visitor)      │
                   │                                      │ odt  (stdlib)                    │
           ┌───────▼────────┐                             │ html article mode (trafilatura)  │
           │   presenter    │  interaction logic          └────────────────▲─────────────────┘
           │     (MVP)      │  shared by the GUIs                          │ implement
           └───────┬────────┘                                              │ DocumentConverter
                   │                                                       │
           ┌───────▼───────────────────────────────────────────────────────┴───┐
           │ core: ports (DocumentConverter, FormatDetector), models and       │
           │ use cases (plan batch → confirm → execute, ADR-0010)              │
           └───────────────────────────────────────────────────────────────────┘
```

**Dependency rule:** everything points toward `core`. `core` imports only the standard library and
`clearmd.i18n`; a test enforces it (feature 001). Feature 001's
[plan](../../spec/features/001_batch-conversion-core-cli/plan.md) details the modules, including `i18n/`,
`detection/`, `config/` and the composition root.

## Flow of a batch conversion (ADR-0010)

1. The input adapter receives files and/or folders.
2. `core` scans, detects the format of each file and computes the destinations in `ClearMD_Output`
   (resolving collisions) → **batch plan**.
3. The adapter shows the plan; if there are existing outputs, the user decides.
4. `core` executes: for each file it picks the converter, writes the Markdown, reports progress and honors
   cancellation. A failure does not stop the batch.
5. The batch report is written to `ClearMD_Output`.

> This document describes the target architecture of Phase 0. It is updated as each feature
> builds it.
