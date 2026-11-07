# Feature 023 — Start screen and Split PDF (ClearMD 2.0)

## Goal

ClearMD becomes a local toolkit that prepares documents for AI (ADR-0043). This feature adds:

- a **start screen** where the user picks a tool;
- the second tool, **Split**, which cuts a PDF into parts by whole pages, without touching their
  content.

The user chooses how to cut the file and what to keep (ADR-0044).

## Sketch

The start screen (the rail gains **Home** above the steps):

```
┌──────────┬───────────────────────────────────────────────────────┐
│ Clear·MD │  What Do You Want to Do?                              │
│          │  Everything happens on your computer.                 │
│ ⌂ Home   │  ┌─────────────────────────┐ ┌─────────────────────────┐ │
│ 1 Choose │  │          📄→M           │ │           ✂             │ │
│ 2 Review │  │  Convert to Markdown    │ │      Split a PDF        │ │
│ 3 Convert│  │ PDF, Word, Excel, Power-│ │ Into parts of whole     │ │
│ 4 Results│  │ Point, HTML and more    │ │ pages, as PDF, Markdown │ │
│          │  │                         │ │ or both                 │ │
│          │  └─────────────────────────┘ └─────────────────────────┘ │
│ Settings │  The tools change files, never what is inside them.   │
│ Help     │                                                       │
└──────────┴───────────────────────────────────────────────────────┘
```

Step 1 of Split: the same list, and in place of the results card's images and summary choices,
"How to Split" and "Keep":

```
  Choose What to Split                          ( step 3 is named "Split" )
  [Add Files] [Add Folder]   list of files …
  ┌ How to Split ─────────────────────────────────────────────────┐
  │ (•) Into [ 4 ] parts      ( ) Every [ 50 ] pages              │
  │ Keep:  ( ) The parts as PDF  ( ) Their Markdown  (•) Both      │
  │ Each part keeps whole pages, in order. Nothing inside changes. │
  │ The Results Go:  (•) Next to the originals ( ) In a folder I…  │
  └───────────────────────────────────────────────────────────────┘
```

## Scope

- **Includes:**
  - the start screen and the Home entry in the three windows;
  - Split for PDF, into N parts or every N pages;
  - keeping the PDF parts, their Markdown, or both, in `ClearMD_Output/OutputSep/<name>/`;
  - Split in the command line (`--split-parts`, `--split-pages`, `--keep`);
  - the summary lists what was split.
- **Does not include:**
  - the cut that fits an AI (024);
  - "Split It" from Convert (025);
  - Merge (026);
  - formats other than PDF (027).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_023_*.py`).

- [x] **AC-01** The cut is computed from the page count:
  - **N parts:** pages are spread as evenly as possible, and the first parts take one more page when
    the count does not divide evenly.
  - **Every N pages:** the last part may be shorter.
  - In both cases there are never more parts than pages, and never an empty part.
- [x] **AC-02** Splitting a PDF writes one PDF per part into `ClearMD_Output/OutputSep/<name>/`.
  - Each part is named `<name> - part <i> of <n>.pdf` (Spanish: `parte <i> de <n>`).
  - Each part holds exactly its pages, in order, and the parts together hold every page.
  - The source PDF is never changed.
- [x] **AC-03** The user chooses what to keep:
  - the PDF parts;
  - each part's Markdown (`<name> - part <i> of <n>.md`, converted part by part, each within the
    time limit);
  - both.

  With "Markdown" alone, no PDF part is left behind.
- [x] **AC-04** In Split, a file that is not a PDF is left out, with a reason in plain words and what
  to do. A damaged or locked PDF fails alone; the batch goes on.
- [x] **AC-05** An existing `OutputSep/<name>/` follows the "if the result already exists" setting
  (ask, overwrite, skip). On overwrite, the parts of the earlier cut are replaced; other files are
  never removed.
- [x] **AC-06** The command line splits with `--split-parts N` or `--split-pages N`, and `--keep`
  `pdf|markdown|both` (default `both`). The two cuts cannot be combined, and N must be at least 1
  (2 for parts).
- [x] **AC-07** `Resumen_ClearMD` (Markdown and PDF) says, for each split file, into how many parts
  and where they are.
- [x] **AC-08** The three windows open on the start screen. It has two tiles, Convert to Markdown and
  Split a PDF, each with its icon, title and what it does, and a line that says the tools change
  files, never their content. Home in the rail brings it back while no work is running.
- [x] **AC-09** Choosing Split names the steps for it: "Choose What to Split" and step 3 "Split".
  Step 1 shows "How to Split" (into N parts / every N pages, with the number) and "Keep" (PDF /
  Markdown / both). Review says, for each file, how it will be cut.
- [x] **AC-10** The cut and what to keep are remembered between sessions, and can also be set in
  Settings.
- [x] **AC-11** Texts in English and Spanish, with titles and buttons in Title Case.
