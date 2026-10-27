# ADR-0025: HTML article mode — trafilatura finds the article, ClearMD writes it

- **Status:** accepted (decisions confirmed by the author, 2026-10-25; refined after review, 2026-10-27)
- **Date:** 2026-10-25
- **Refines:** ADR-0006 (HTML "article mode"), ADR-0012 (the `html_strategy` setting).

## Context

ADR-0006 chose `trafilatura` (Apache-2.0) to extract only the main content of an HTML page, as a second strategy
next to markitdown's full page, selected by the user. The `html_strategy` setting (`full` / `article`) exists
since feature 001 but nothing reads it. Two questions were left open: how the strategy reaches the worker, and
whether the article's Markdown follows the output guarantee of ADR-0023, which only ClearMD's own converters
gave so far. A saved web page is untrusted input like any other, and its images are almost always remote: a
Markdown link to them makes the viewer fetch them when the file is opened.

## Decision

- **The strategy is part of the plan.** The CLI's `--html full|article` (or the setting) reaches `plan_batch`;
  each HTML file is planned with its strategy, the worker request carries it, and the registry picks the
  converter by format and strategy. The summary shows `HTML (article)`. Other formats ignore it.
- **trafilatura finds, ClearMD writes.** trafilatura runs with its XML output (headings, paragraphs, emphasis,
  lists, links, quotes, code, tables, images as `graphic`) — never its Markdown output — and ClearMD writes the
  Markdown from that XML with the shared `markdown_out` module, so the article mode gives the same guarantee as
  `.tex` and `.odt`: no raw HTML, no block structure from text, links only where the page had them and only with
  the safe schemes.
- **Images are placeholders** with their alt text (`*Image: …*`), counted in a note, as in `.odt`: an article
  converted by ClearMD never makes the viewer fetch anything. The page's title becomes `# Title`.
- **No article found** (trafilatura returns nothing, or almost nothing): the page is converted in full and a
  note says so. The file is never left out because of the strategy. *Refined on 2026-10-27 (the author's
  choice, after the security audit of 004):* the whole page is written by ClearMD itself (`html/page.py`: lxml
  parses it, its elements map to the same tree, the same renderer writes it), not by markitdown, so a page
  cannot switch the guarantee off by having no article.
- trafilatura's own network functions are never called (it is given the page's text, decoded by ClearMD, so it
  never decompresses anything either; ADR-0005), and the tree it returns is converted to ClearMD's own under
  the XML reader's limits.

### Decided while building it (2026-10-26)

- **What counts as no article:** trafilatura returns nothing, or an article with less than 200 characters of
  text (a login page has about 50; a short news piece, 500 or more).
- **The summary always says `HTML (Article)` / `HTML (Artículo)`** for a page converted with this strategy, also
  when the whole page was used: the note says why (the author's choice, "para ser claros").
- **Images get their own note:** "images are not downloaded; each is shown by its description" (an `.odt`'s
  images stay inside the file; a page's are on remote servers). The placeholder word follows the page's
  `lang` (`*Imagen: …*`).
- **Shared writing:** the inline writer of `.odt` (escaping, emphasis Markdown can hold, links, the growth
  budget) moved to `conversion/inline.py`, and the XML reader to `conversion/xmltree.py`, so the article is
  written with the same guarantees. Containers nested deeper than 32 levels are written as their text.
- **Dependencies:** `trafilatura==2.3.1` (pinned: its extraction decides the output). Two packages it brings
  were published days before (`lxml-html-clean` 0.4.6, `tzlocal` 5.4.5): `[tool.uv] constraint-dependencies`
  keeps their previous release until they are two weeks old. `tld` is triple-licensed (MPL-1.1 / GPL-2.0 /
  LGPL-2.1+): ClearMD uses it under MPL-1.1, unmodified, compatible with MIT.

### After the code review and the security audit (2026-10-27)

- A page whose article would need more memory than the worker allows is skipped, saying so and what to do
  (`--html full`): handing it to markitdown would switch the guarantee off behind the user's back
  (verification of 004); one with more than 25,000 elements is written in full by ClearMD, with its own note; a page past the
  XML reader's limits is cut, its first part kept, with a note
  (trafilatura's extraction grows faster than linear); characters XML forbids become U+FFFD before trafilatura
  (one would lose the whole article); line endings are "\n" everywhere (a "&#13;" in a code block could
  leave its list).
- **Not recovered (trafilatura 2.3.1 drops them before ClearMD sees the article):** figure captions, lists
  inside table cells, an ordered list's start number, merged cells, a `<pre>` without code-like markers
  (written as a one-line quote), and a page nested deeper than 256 levels (libxml2 stops there). A Latin-1 page
  without a declared charset may be decoded as another single-byte encoding.

## Consequences

- **Gains:** the Strategy pattern ADR-0006 promised, with one guarantee for every Markdown ClearMD writes
  itself; a clean article for an LLM or a notebook.
- **Costs:** `trafilatura` and its dependencies (`lxml`, `justext`, `courlan`, `htmldate`…) in the worker;
  a small renderer for its XML. Article images are not visible in the Markdown.

## Alternatives considered

- **trafilatura's Markdown output:** less code, but its links, images and escaping are not ClearMD's: the
  guarantee would not hold.
- **Remote images as links:** what a browser would show, but opening the file would contact the image hosts.
- **Readability ports (`readability-lxml`):** less maintained, weaker extraction in benchmarks of the field.
- **Failing when no article is found:** the user asked for content; the full page is the honest fallback.
