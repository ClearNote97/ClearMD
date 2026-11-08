# Feature 029 — Minor formats: e-mail, Rich Text and subtitles

## Goal

Convert three more everyday formats to Markdown with ClearMD's own converters, using the standard
library only (ADR-0049):
- e-mails (`.eml`);
- Rich Text (`.rtf`);
- subtitles (`.srt`, `.vtt`).

## Acceptance criteria (what MUST be true)

- [x] **AC-01** **An e-mail** becomes:
  - its subject as the title;
  - From, To, Cc and Date;
  - its text body, or its HTML body converted when it has no plain text;
  - the names of its attachments.

  The attachments' contents are never extracted.
- [x] **AC-02** **Rich Text** becomes its text in paragraphs:
  - the code page's characters and Unicode escapes are read right;
  - fonts, colours, styles, pictures and hidden destinations are skipped;
  - the summary notes that the formatting was dropped.
- [x] **AC-03** **Subtitles** (SRT and WebVTT) become one line per cue, with its start time
  (`` `00:01:02` text ``), the cue's lines joined and its tags removed.
- [x] **AC-04** The formats are recognised by their extension, run in the worker with its limits,
  have an icon, and are listed in the help, in English and Spanish. A damaged file fails alone.
