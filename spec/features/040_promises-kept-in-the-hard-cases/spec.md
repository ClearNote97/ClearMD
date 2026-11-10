# Feature 040 — Promises kept in the hard cases (audit v4's eleven improvements)

## Goal

The fourth audit ([report](../../../docs/audit/2026-11-09-audit-boards-v4.md)) found that 2.12.0
made bigger promises that the hardest cases still broke: a blank result called "converted", pictures
that slipped past the output guarantee, two-letter notes in Chinese characters, a logo that turned
the hidden-text filter off, chapters merged 1, 10, 2. The owner accepted the eleven improvements, the
empty result as "failed" with its reason, and the amendments to ADR-0054 and ADR-0030. A doubts board
([report](../../../docs/audit/2026-11-09-doubts-board-2.md)) settled three more questions.

## Acceptance criteria (what MUST be true)

- [x] **AC-01** A result without text "failed", with its reason and what to do (OCR for a scan); no
  blank file is written; in every tool (Split lists the part, Merge the document).
- [x] **AC-02** Merge follows the order a person counts: 1, 2, 10.
- [x] **AC-03** One report channel: no text sends to GitHub Issues; Copy Details names the community
  page and the e-mail.
- [x] **AC-04** One output door for every result (Convert, Split's Markdown parts, Merge's Markdown):
  no way of writing a picture or an unsafe link survives, judged by a real CommonMark reader; the
  escape marks are readable ("\[", "AT&T", "juan_perez").
- [x] **AC-05** Review and Results show each row's whole reason and what to do, never cut; flet's
  rows move with the arrow keys.
- [x] **AC-06** Split never says "split" with parts missing: only stale temporary files are swept,
  and a prepared part that disappears fails the file.
- [x] **AC-07** A logo does not protect hidden text; only a picture covering half the page (a scan)
  does (ADR-0054 amended).
- [x] **AC-08** The shortest Windows notes ("Sí", "¿Qué?") keep their letters; a UTF-16 file is not a
  guess; the note names no codec; Merge renames only defined footnotes, never inside code; an inch
  mark in a CSV is text.
- [x] **AC-09** PDF: numbered and lettered lists are lists; a two- or three-page letter loses the
  letterhead on every page (ADR-0030 amended); a page's only line is never taken for its margin.
- [x] **AC-10** Numbers, colours and advice agree: "file N of M" counts what is written; "Kept" is
  never amber, left-outs only when one asks something; the summary labels a page converted whole as
  such; the stop line survives a redraw; "too large" never sends to Split.
- [x] **AC-11** Keyboard focus is visible on every control, in every window; the focused tile and
  the last used one differ. The doubts board's decisions: readable marks inside the one door; a
  saved "full page" is respected and the summary says so each time.

## Out of scope (said, not hidden)

- Each PDF part's opening line and headers computed on the whole PDF (B3-03): the next version
  (doubts board 2, D3).
- A lock per output folder: not needed after the cheap measures.
- Raising Split's 250 MB limit (ADR-0015, ADR-0010).
- Replacing markitdown: the 3.0.0 experiment.
