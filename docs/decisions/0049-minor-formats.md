# ADR-0049: E-mail, Rich Text and subtitles with ClearMD's own converters

- **Status:** accepted
- **Date:** 2026-11-08
- **Refines:** ADR-0004 (hybrid engine), ADR-0006 (own converters).

## Context

The roadmap left three everyday formats for later. markitdown handles none of them well
(`.rtf`, subtitles), or it would bring dependencies for them (`.eml` through its Outlook
extra). Each can be read with the standard library.

## Decision

- **`.eml`:** the standard `email` parser (policy `default`). The subject becomes the title.
  From, To, Cc and Date are a short list. The body is the plain text, or the HTML body through
  markitdown's HTML converter when there is no plain text. The attachments are listed by name
  only, and their contents are never extracted (`02_scope`: no attachments, no extraction).
- **`.rtf`:** a small reader of our own. It skips the groups that hold no document text (fonts,
  colours, styles, pictures, `\*` destinations). It reads `\'hh` bytes in the declared code page
  and `\uN` characters with their `\uc` fallbacks, and turns `\par` into paragraphs. The
  formatting is dropped and noted.
- **`.srt`, `.vtt`:** one line per cue, its start time in a code span, its lines joined, its
  tags removed. An AI reads the transcript and can still point at a moment.
- All three are recognised by extension, run in the worker with its limits, and borrow an icon
  (text or Word).

## Alternatives considered

- **striprtf, extract-msg and similar:** more dependencies for tasks the standard library
  covers.
- **Subtitles as a table:** heavier to read than one line per cue.
