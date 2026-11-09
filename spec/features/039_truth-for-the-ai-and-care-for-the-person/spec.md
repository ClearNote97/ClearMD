# Feature 039 — Truth for the AI, care for the person (audit v3's ten improvements)

## Goal

The third audit ([report](../../../docs/audit/2026-11-09-audit-boards-v3.md)) found that some
results still reach an AI with what the person never meant to send (letters broken in short
Windows texts, remote images, hidden PDF text, equations and tables that look sure and are not),
that the installer and the download page described the previous version, and that the windows
sometimes count, colour or react in ways that mislead. The owner accepted the ten improvements and
decided the open questions: web pages convert their article by default; an empty file stays
"failed", with its reason; a way to report without a GitHub account (the project's community page,
or e-mail); the installers are signed too; and a new ADR for the text no one can see in a PDF.

## Acceptance criteria (what MUST be true)

- [x] **AC-01** A short text or CSV saved by Windows (one line in Spanish, English, French; a
  three-row CSV) keeps its letters; the note says what to do if something looks odd.
- [x] **AC-02** Nothing in a result fetches or runs when opened: remote images, network-share and
  absolute images, `file:`/`javascript:` links and active HTML become text, in every format, with a
  note; an e-mail's HTML body is written in memory by ClearMD; the summary hides paths as Copy
  Details does.
- [x] **AC-03** The installer and the download page say what is true: no "one file that unpacks",
  no jargon on the cards, "Open ClearMD now" at the end, "What to Download" with every file and how
  to uninstall it, only this version's news (the history linked), the SmartScreen notice beside
  the download, and the line for screen-reader users (README, Help, download page, installer).
- [x] **AC-04** First use: the Welcome changes the language at once; Help says where results go
  (step 1) and how to use the result with an AI; Results says it in one line.
- [x] **AC-05** A large PDF is never warned about before it starts (it reports its pages); the
  progress bar moves inside a long file; "Split the large PDFs" gives the rest of the Convert list
  back and never saves its cut as the person's choice.
- [x] **AC-06** When one part of a Split stops, the other parts stay, its original part stays to
  try again, and the summary names it; an empty folder is never a result.
- [x] **AC-07** Review and Results tell the truth: each file counted once; a word before every
  left-out or missing row; what only informs in a calm tone and after the rest; singular labels;
  after an unexpected error "stopped by an error: N of M finished", never zeros; the results
  folder opens by itself only when everything went well.
- [x] **AC-08** The summary warns when a result may mislead an AI: text no one sees in a PDF is
  left out and said (ADR-0054); equations kept as their symbols, with pages; Word tables with
  merged cells; Merge keeps each document's notes and gives its footnotes their own names; Split
  never says headers were removed when a part kept them.
- [x] **AC-09** Settings always fits the screen (1366×768), in every window.
- [x] **AC-10** One keyboard rule in every window (Enter presses the focused button; Delete and
  Ctrl+A only in the list); Clear All stands apart and can be undone; an edit from Review or
  Results goes back to step 1 and says the earlier results stay in their folder.
- [x] **AC-11** The owner's decisions: article mode by default (ADR-0025 amended); the empty file
  stays "failed", with its reason; the report channel is the community page or e-mail; the
  installers are signed with the programs once SignPath is set up (ADR-0037 amended); ADR-0054.

## Out of scope (said, not hidden)

- Each Split part's opening line ("Part 2 of 5 of X — pages 6–10") and the page headers computed on
  the whole PDF (B3-03): only the false claim is removed.
- A Word converter of ClearMD's own (B3-01): the merged cells are told, not rebuilt.
- A Markdown file read as-is by Merge does not report a guessed encoding.
- White text on a white page (ADR-0054's known limit); the installers' uninstaller is not signed.
- In flet's Review, informative left-outs are still drawn as warnings (Review's rows carry no tone).
