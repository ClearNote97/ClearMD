# Feature 004 — HTML article mode

## Goal

A saved web page (`.html`) can become just its article — title, text, lists, links, tables — without menus,
footers, cookie banners or ads, when the user asks for it; the same page converts in full as before when they
do not. Either way, nothing in the Markdown makes a viewer contact the page's servers.

## Scope

- **Includes:**
  - A second strategy for HTML (ADR-0006, ADR-0025): `article`, with `trafilatura` finding the main content and
    ClearMD writing it through the shared output guarantee (`markdown_out`).
  - Choosing it: the `html_strategy` setting (ADR-0012), and `--html full|article` on the CLI for one run.
  - The strategy in the plan, the worker request and the summary (`HTML (article)`).
  - The fallback to the full page with a note when no article is found.
  - A benchmark case, so the HTML speed and memory factors cover both strategies.
- **Does not include:** fetching pages from the web (never, ADR-0005); keeping images (placeholders, as in
  `.odt`); article mode for other formats; changing the full-page strategy (markitdown, as in feature 001).

## The supported subset (article mode)

| trafilatura's XML | Markdown |
|---|---|
| the page title | `# Title` |
| `head` (`rend="h1"`…`"h6"`) | headings, the shallowest at `##` |
| `p` | a paragraph |
| `hi` (`#b`, `#i`, `#u`, `#t`, `#sup`, `#sub`) | `**…**`, `*…*`, `<u>…</u>`, `` `…` ``, `<sup>…</sup>`, `<sub>…</sub>` |
| `list` / `item` (ordered when `rend="ol"`) | `-` / `1.` (nested) |
| `ref target` | `[text](url)` with the link rules of ADR-0023 |
| `quote` | `>` block quote |
| `code` (block) | fenced code block |
| `table` / `row` / `cell` (`role="head"`) | a Markdown table |
| `graphic` | `*Image: alt*`, a note with the count |
| `lb` | a hard line break |

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test named after its id (`tests/acceptance/test_004_html_article_mode.py`).

- [ ] **AC-01** With the default settings, an `.html` converts in full exactly as in feature 001.
- [ ] **AC-02** With `html_strategy = "article"` in the settings, or `--html article` for one run, an `.html`
  converts to its article only: the menu, the footer and the cookie banner of the fixture page are gone, its
  title and article text are there. `--html full` overrides an `article` setting.
- [ ] **AC-03** The summary shows the strategy: `HTML (article)`.
- [ ] **AC-04** The article keeps headings, emphasis, lists (nested, ordered), links, quotes, code and tables, as
  the table above says.
- [ ] **AC-05** Images become placeholders with their alt text, counted in a note; nothing but the Markdown and the
  summary is written, and the Markdown links to no image.
- [ ] **AC-06** A page where no article is found converts in full, with a note saying so; the exit code stays 0.
- [ ] **AC-07** The output guarantee of ADR-0023 holds for article mode (checked with a CommonMark parser and a
  seeded fuzz): hostile text, links with `javascript:` or entities, and raw HTML in the page never become
  links, images, HTML or block structure in the Markdown.
- [ ] **AC-08** No network is used: converting in article mode works with the network guard of the tests on.
- [ ] **AC-09** Notes are shown in the user's language (EN/ES).
- [ ] **AC-10** The CLI process never imports trafilatura (it runs in the worker, as markitdown does).
- [ ] **AC-11** The benchmark measures the article strategy and `schemas/limits.py` covers it.

## Actors and data

- **Actors:** the same as feature 001.
- **Data:** saved `.html` / `.htm` files, read-only; nothing is downloaded.

## Risks / open questions

- **Extraction quality varies by site:** the fallback to the full page and its note keep the user informed.
- **trafilatura's dependencies** grow the executable (feature 006 measures it).
