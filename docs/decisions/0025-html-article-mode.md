# ADR-0025: HTML article mode — trafilatura finds the article, ClearMD writes it

- **Status:** accepted (decisions confirmed by the author, 2026-10-25)
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
- **No article found** (trafilatura returns nothing, or almost nothing): the page is converted in full by
  markitdown and a note says so. The file is never left out because of the strategy.
- trafilatura's own network functions are never called (it is given the HTML text; ADR-0005), and the XML it
  returns is parsed by the same limited `pyexpat` tree as OpenDocument (moved to the conversion package).

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
