# Feature 038 — Say only what is true, and start faster (audit v2's ten improvements)

## Goal

The second audit ([report](../../../docs/audit/2026-11-09-audit-boards-v2.md)) found that ClearMD
no longer loses work but still says some things that are not true: a Windows text with "ańo",
"3 parts" that is one part, a "Copy Details" that lets a name through, an empty file called
"damaged", a cancel shown as an unexpected error. It also found the windows loading the
converters' libraries, a CI four times slower than needed, and the installed Classic App unpacking
itself at every start. The owner accepted every recommendation and the conciliator's answers to
the disagreements (confirm only when closing during a task; "Process Summary").

## Acceptance criteria (what MUST be true)

- [x] **AC-01** One decoder for every plain text: a cp1252 text or CSV keeps its ñ and accents in
  Convert, Merge and Split; when the encoding is guessed, a plain note says to check the accents.
- [x] **AC-02** "Copy Details" hides quoted file names, the names of the files the person chose,
  and folders with spaces; the texts promise "we try", one catalog text says how to report, and
  no message asks to attach the whole summary.
- [x] **AC-03** "Split into N parts" gives N parts when the file has at least N units, even with
  the weight at one end; when it cannot, the summary says so.
- [x] **AC-04** A cancel during Merge's last step is a cancel (the summary is written); an
  unexpected error during a task lands on Results with the folders that may hold what was written.
- [x] **AC-05** A table cell written over several lines in a PDF stays one cell; a rebuilt
  equation with an incoherent shape is kept as text, never said with confidence.
- [x] **AC-06** Closing the window during a task asks once (Keep Working / Close); Cancel and
  closing when idle never ask.
- [x] **AC-07** Messages that can be followed: "split it" only for formats Split takes; an empty
  file is "empty" in every tool; step 3's subtitle follows the work; hints name the real button;
  the Home note reassures; the command line refuses a merge of fewer than two documents before it
  starts; real plurals instead of "(s)"; "task", not "batch"; "Process Summary".
- [x] **AC-08** A result's names do not depend on the language: parts and image folders written in
  one language are recognised in the other; images are kept only by Convert, in every interface.
- [x] **AC-09** Faster: no interface loads PDFium, openpyxl or lxml at start; the test suite
  collects garbage only after window tests and CI keeps every run's timing; the installed Classic
  App is a folder (ADR-0053) and CI prints each window's start time.
- [x] **AC-10** PDF estimates recalibrated with real documents (time and memory per MiB).
