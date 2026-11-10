# ADR-0054: Text no one can see in a PDF is left out, and said

- **Status:** accepted
- **Date:** 2026-11-09
- **Origin:** the third audit (`docs/audit/2026-11-09-audit-boards-v3.md`, B2-02); the owner's
  decision on it.

## Context

A PDF can hold text that a person never sees on the page: placed off the page, drawn too small to
read, or drawn in PDF's "invisible" mode. An AI reads every character. Text that a reader cannot
see is therefore a way to hand an AI instructions that the person sending the document never saw
(prompt injection), and in any case it is not what the person meant to share.

One kind of invisible text must stay: a scanned PDF passed through text recognition (OCR) carries
its text in invisible mode, laid over the picture of the page. It is the only text such a PDF has.

## Decision

- While reading a page, ClearMD leaves out (turns into spaces, so the reader's places still match)
  every character that is:
  - more than an inch (72 points) outside the page;
  - drawn smaller than 1 point;
  - drawn in invisible mode **on a page with no picture**. On a page with a picture, invisible text
    is the scanner's recognised text and stays.
- The summary says it, with the pages: "text that cannot be seen on the page was left out, so an AI
  does not read what you cannot".
- White text is **not** left out: it may sit on a coloured box, and ClearMD does not see the page's
  background. This is a known limit.

## Consequences

- **Gains:** the Markdown holds what the person sees; an AI is not handed hidden instructions from
  the cases above; nothing is removed silently.
- **Costs:** white-on-white text still passes; a line cut by the page's edge by less than an inch
  stays (a reader half sees it). The checks add one pass over a page's characters, and a look at its
  objects when it has invisible text.

## Amendment (2026-11-09, the owner's decision on the fourth audit, B3-04)

"A page with a picture" was too broad: a letterhead's small logo was enough to let hidden text
through. Invisible text now stays only on a page where **one picture covers at least half of the
page**, as a scan does. A logo or a photo no longer protects it.
