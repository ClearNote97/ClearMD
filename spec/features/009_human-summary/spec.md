# Feature 009 — A summary in human language, and its PDF

## Goal

`Resumen_ClearMD.md` tells a person how the batch went and what to do, in their language. On
request, the same summary comes as a PDF in the app's look (ADR-0031).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_009_human_summary.py`).

### The Markdown summary
- [ ] **AC-01** The summary starts with a headline: a mark (✅ ⚠️ ❌ ⏹️) and one sentence saying how
  many of how many documents were converted and how many things need attention; then the line of
  the batch (date · version · totals).
- [ ] **AC-02** **Where your files are** says in one sentence the folder that holds the Markdown.
- [ ] **AC-03** **Needs your attention** lists, before anything else, every file that failed, was
  stopped, or was converted with notes: its mark, its name, what happened and what to do.
- [ ] **AC-04** Files are shown by their name, their folder apart, and only when it is not the top
  folder; the converted files are a table (document, folder, result, time).
- [ ] **AC-05** The history is folded and still holds the earlier batches (200 at most, only
  ClearMD's own lines).
- [ ] **AC-06** A hostile file name never breaks the summary (ADR-0023), in every place it shows.
- [ ] **AC-07** The summary is in the app's language, English or Spanish, singular and plural.

### The PDF report
- [ ] **AC-08** With "Markdown + PDF", `Resumen_ClearMD.pdf` is written next to the Markdown. It
  has the same headline, sections and table, in the app's look, its text selectable, and no link
  or action.
- [ ] **AC-09** If the PDF cannot be written, the Markdown is still written and the batch says so.

### The choice
- [ ] **AC-10** The summary format is chosen on step 1 (Markdown · Markdown + PDF), remembered;
  it is also in Settings; the command line has `--summary-pdf`.
- [ ] **AC-11** Everything new follows ADR-0027, in English and Spanish, works with the keyboard,
  and has screenshots in `docs/screenshots/009/`.
