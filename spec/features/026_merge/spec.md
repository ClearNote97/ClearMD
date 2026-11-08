# Feature 026 — Merge

## Goal

The third tool (ADR-0043): several documents joined into **one file**, in the order of the list.
The result is either:
- **one Markdown**: every document is converted (Markdown files are taken as they are) and
  joined. This is the file to give an AI in one go.
- **one PDF**: only when every document is a PDF. Their pages are copied whole, in order.

As with every tool, ClearMD changes files and never their content (ADR-0046).

## Sketch

```
Home:   [ Convert to Markdown ]  [ Split a Document ]  [ Merge Documents ]

Step 1 of Merge:
  Choose What to Merge            (the list's order is the order of the result)
  [Add Files] [Add Folder]  1 intro.pdf  2 chapter.docx  3 notes.md
  ┌ How to Merge ────────────────────────────────────────────────┐
  │ Into:  (•) One Markdown   ( ) One PDF (only PDF files)       │
  │ Each document keeps its content whole, in the list's order.  │
  │ The Results Go … · Summary …                                 │
  └──────────────────────────────────────────────────────────────┘
```

## Acceptance criteria (what MUST be true)

- [ ] **AC-01** **Into one Markdown:** each document is converted as Convert would convert it,
  each within the time limit; Markdown files are taken as they are. The documents are joined
  in the list's order into `ClearMD_Output/OutputUnif/Merged <date time>.md`. Each document
  starts with a comment naming its source (`<!-- ClearMD: name.pdf -->`), which a Markdown
  viewer does not show. Nothing else is added.
- [ ] **AC-02** **Into one PDF:** the PDFs' pages are copied whole, in order, into
  `OutputUnif/Merged <date time>.pdf`. Any file that is not a PDF is left out with a reason
  (choose One Markdown).
- [ ] **AC-03** A document that fails is left out of the result, and the summary says so. The
  result is still written with the others. A merge that would hold fewer than two documents
  writes nothing, and says why.
- [ ] **AC-04** The command line merges with `--merge markdown|pdf` (the order is the order of
  the paths, and the files of a folder go in name order). It cannot be combined with a split.
- [ ] **AC-05** The start screen gains its third tile, **Merge Documents**. Step 1 of Merge shows
  "How to Merge" (One Markdown / One PDF) in place of the images, and says that the list's order
  is the result's. The steps speak as Merge (Merge's words in place of Convert's). The choice is
  remembered (`merge_into`) and is in Settings.
- [ ] **AC-06** Texts in English and Spanish, with titles and buttons in Title Case.
