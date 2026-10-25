# ADR-0023: LaTeX — includes as inserted text, images never fetched, a file never fails whole

- **Status:** accepted
- **Date:** 2026-10-25
- **Refines:** ADR-0022.

## Context

The code review and the security audit of feature 002 found that the first design of includes was wrong in
shape, not only in details: a pre-pass read every include a second time on a separate budget (up to twice the
250 MiB limit), out of document order (a `\renewcommand` after an `\input` lost), and looked into comments and
code blocks. They also found that an `\includegraphics` naming a remote or absolute path became an image link,
so opening the Markdown in a viewer could fetch it (a tracking beacon; on Windows, an SMB request that leaks
the user's NTLM hash) — a request the compiled PDF would never make. And that deep nesting or an odd `\verb`
made pylatexenc fail, so a whole thesis failed for one bad line, against AC-21.

## Decision

- **An include is text inserted in place**, as in TeX. Each allowed include is read **once**, on **one budget**
  for the whole document (200 files, 250 MiB including the main file), and spliced where it is written, so the
  document is parsed once and definitions apply in document order. Includes inside comments, code environments
  and `\verb` are not includes. A refused include stays in the text, shown as code, with its note; an include
  produced by a macro is not followed (`made_by_macro`).
- **Reading is the check:** the file is opened by walking its folders by descriptor with `O_NOFOLLOW`, so the
  file read is the file checked (on Windows, the identity of the opened file is compared with the checked one).
- **An image is a link only when it can be inside the document folder.** Names with a drive, a scheme
  (`http:`), a leading `/` or `//`, `~` or `..` are shown as code, never as a link. Only image files are looked
  up (a name without an image extension gets one added), and link targets are escaped.
- **A file never fails as a whole.** If pylatexenc cannot read the source at all (recursion, internal errors),
  the whole flattened source is kept as a LaTeX code block with a `parse_recovered` note.
- **Declared `latin1` is read as cp1252** (its superset with the Windows quotes and dashes in 0x80–0x9F that
  would otherwise become invisible control characters), falling back to latin-1 for its undefined bytes.
- **Macro arguments are substituted once:** `#1`…`#9` are replaced in a single pass (what an argument brings is
  never replaced again; `##` is `#`), and an expansion's size is charged to the budget before it is built.
- **The Markdown never does what the document did not write as LaTeX** (chosen after three verification rounds,
  checked with a CommonMark parser in `test_output_guarantee.py`). Inline: every path that copies document
  text escapes `<`, `[`, `]` and backticks; pieces written next to each other never form `![` or `](`; math
  gets only `< ` for an HTML-looking `<tag` and an escaped backtick. Blocks: ClearMD marks the block lines it
  writes (U+E000, stripped from the input), and a final pass neutralizes every other line a viewer would read as
  a heading, list, quote, table, fence, rule, setext underline or link reference definition; display-math lines
  that look like a block get a `{}`. Footnote definitions are ClearMD's: a viewer without footnotes may show a
  footnote whose text is only a URL as a link (never an image).
- **Note subjects are bounded** to 200 characters and at most 1,000 distinct unknown commands are listed; the
  text keeps every one as written.

## Consequences

- **Gains:** the byte and file limits of ADR-0022 hold as written; definitions behave as in LaTeX; parsing
  happens once (the strict pass that only produced an error message is gone, about half the time); a converted
  document never makes a network request on its own.
- **Costs:** a parse error is located through a map of the spliced pieces (`file, line N`); a remote or absolute
  image the author really wanted shows as code, and the user adds it by hand.

## Alternatives considered

- **Keeping the pre-pass with a shared budget:** rejected; still two reads per file (a window for the file to
  change between them) and still out of document order.
- **Remote images as links, with a note:** rejected; the fetch happens when the viewer opens the file, whatever
  the note says.
- **Failing the file on a parser crash:** rejected; one bad line would lose a whole thesis.
