# ADR-0016: Output layout, chosen output folder and the `Resumen_ClearMD.md` summary

- **Status:** accepted (the fine-grained rules are set in the spec of feature 001)
- **Date:** 2026-10-25
- **Supersedes:** the output names and collision rule of ADR-0010.

## Context

ADR-0010 wrote the converted files directly into `ClearMD_Output` and the batch report next to them, which
forced reserving a name (`clearmd-report.md`) among the user's own files. Its collision rule (a suffix with
the source extension) also fails in two cases: on Linux `report.pdf` and `Report.pdf` both become
`report (pdf).md` and collide again case-insensitively, and with an explicit output folder two inputs from
different places can share name and extension. Finally, a folder at the root of a drive or the user's home
has no useful parent to write into, and users want to decide where results go.

## Decision

### Layout

```
<output parent>/ClearMD_Output/
  Resumen_ClearMD.md     the batch summary (fixed name, in every language)
  Output/                the converted files
```

- The summary can never collide with a converted file. Its name is fixed so it is always easy to find,
  whatever the language of the app.
- `ClearMD_Output` is always created; ClearMD writes nothing outside it.

### Where `ClearMD_Output` goes

- **Next to the input** by default: a file `D/report.pdf` → `D/ClearMD_Output/Output/report.md`; a folder
  `P/project/` → `P/ClearMD_Output/Output/project/…`.
- If the input folder is the **root of a drive or the user's home**, `ClearMD_Output` goes **inside** it and
  its contents go directly into `Output/`.
- The user can **choose the output folder** for each batch: `--output-root DIR` in the CLI; in the GUIs a
  choice between "next to the originals" and a chosen folder, remembered as the suggestion for next time
  (feature 005). `ClearMD_Output` is created inside the chosen folder.
- Without write permission, the files of that output root fail with a message that suggests choosing another
  folder.

### Names

- The output keeps the full source stem: `report.v2.final.pdf` → `report.v2.final.md`.
- Outputs that collide in the same batch (compared case-insensitively) all get the source extension:
  `report (pdf).md`, `Report (docx).md`. If they still collide, a counter is added in path order:
  `report (pdf).md`, `report (pdf 2).md`. Files without an extension use their detected format.

### The summary

`Resumen_ClearMD.md` works as the README of its output folder:

- **On top, the last batch in full:** a **name table** that maps each source to the file it produced (so
  `report (pdf 2).md` is never a mystery), then skipped, failed and cancelled items, in the user's language.
- **At the bottom, a history:** one line per earlier batch, newest first (date and totals), carried over from
  the previous summary. Only ClearMD's own marked section is parsed; if it cannot be read, the history starts
  again and the summary says so.

## Consequences

- **Gains:** no reserved file names; collisions resolved in every case; an output folder that explains itself
  and its own history; users always know where results are and can choose another place.
- **Costs:** one more folder level; the history requires parsing a file ClearMD wrote before.

## Alternatives considered

- **A Windows-style counter only (`report (2).md`):** rejected; the extension tells the user at a glance
  which file each output came from.
- **A separate history file:** rejected; one file for the user to open is simpler.
- **Writing directly into a chosen folder, without `ClearMD_Output`:** rejected; it would mix results with the
  user's files and break the rule of writing only inside `ClearMD_Output`.
