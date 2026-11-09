# Feature 034 — Never lose or misreport work (audit improvements 1–3)

## Goal

The audit of 2.8.1 ([`docs/audit/2026-11-08-audit-boards.md`](../../../docs/audit/2026-11-08-audit-boards.md))
found results reported as fine that were not: earlier work deleted, merges overwritten, broken
images, one-column tables, files done twice. A non-technical user cannot check any of it. This
feature closes the first three recommendations: what the product writes is complete, is never
lost, and is reported truthfully.

## Acceptance criteria (what MUST be true)

- [x] **AC-01** Splitting again replaces the earlier parts only once every new part is written:
  a failure, a time limit or a cancel halfway leaves the earlier parts as they were and no new
  part behind (B1-01).
- [x] **AC-02** A merged file never replaces another: a second merge in the same minute gets
  "(2)" (B1-02). In a merged Markdown, each document opens with a visible line, "Document 2 of
  3: b.pdf", after the hidden comment (B3-08).
- [x] **AC-03** Merge always leaves its summary with a reason: with fewer than two documents
  that could be joined, the output folder is still created, the summary is written and each
  document says why nothing was merged; a cancelled merge is told as cancelled. The texts no
  longer guess "is the disk full?" (B4-01, B1-07e).
- [x] **AC-04** Merge asks for two documents before it starts: step 1's Next is disabled with
  one file ("Add at least two documents to merge them"), and step 2's when only one is left
  (F1-02, F4-11).
- [x] **AC-05** A folder and a file inside it, chosen together, give that file once, in every
  tool; the second appearance is listed as "already inside a folder you chose" (B1-11, F1-01).
- [x] **AC-06** A CSV separated by semicolons, tabs or bars becomes a table with its columns;
  a comma CSV converts exactly as before (B1-03).
- [x] **AC-07** Splitting or merging a Markdown keeps its images: every relative link to a file
  that exists next to the source points to that file from the new folder (B1-12, B3-01).
- [x] **AC-08** The texts in English and Spanish.
