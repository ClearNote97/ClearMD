# Feature 024 — Split into parts that fit an AI; Split takes Markdown

## Goal

An AI reads a limited amount of text at once. Split gains a third cut: **parts of about N words**.
The PDF's pages are grouped, whole and in order, up to N words each. Split also takes Markdown
files, cut at their headings (ADR-0045, from the council of 2026-11-07).

## Sketch

```
  How to Split   (•) Into [ 4 ] parts   ( ) Every [ 50 ] pages   ( ) Parts of About [ 30000 ] Words
  Keep:  ( ) The parts as PDF  ( ) Their Markdown  (•) Both
  Each part keeps whole pages or sections, in order. Nothing inside them changes.
  About: an AI reads a limited amount of text at once; if it refuses a part, choose fewer words.
```

## Scope

- **Includes:**
  - the words cut, for PDF and Markdown;
  - Markdown files in Split, cut into N parts or by words;
  - the cut in the three windows, Settings and the command line (`--split-words N`);
  - the summary says when a page or a section alone is larger than the size.
- **Does not include:**
  - a tokenizer;
  - presets by AI or by size;
  - the part count shown before running (the council's dissent, recorded);
  - "Split It" from Convert (025).

## Acceptance criteria (what MUST be true)

- [ ] **AC-01** **Parts of about N words:**
  - a PDF's pages are grouped whole and in order, each part up to N words, counted in the worker
    (each CJK character counts as a word);
  - a single page larger than N becomes a part alone, and the summary says so;
  - a PDF with no text to measure fails with a reason and what to do (use Every N pages); it is
    never put in one part without a word.
- [ ] **AC-02** **Split takes Markdown** (`.md`, `.markdown`) and cuts it at its headings:
  - into N parts, balanced by words; or
  - into parts of about N words.

  A section larger than the size is cut at its paragraphs. Nothing is ever cut inside a code
  fence. A file without headings is cut at paragraphs. Every part is Markdown, whatever "Keep"
  says.
- [ ] **AC-03** "Every N pages" does not apply to Markdown. A Markdown file is left out with a
  reason and what to do, on Review before anything runs, in the summary and on the command line.
- [ ] **AC-04** The command line:
  - splits with `--split-words N` (N from 500 to 1,000,000);
  - takes only one of the three cuts at a time.
- [ ] **AC-05** The three windows show the third cut ("Parts of About [N] Words") and the hint,
  in the same pattern as the other two cuts. The block's note says "whole pages or sections".
  Settings has the cut too, and it is remembered (`split_words`, default 30,000).
- [ ] **AC-06** Texts in English and Spanish: titles and buttons in Title Case; "about" wherever
  the size is shown; no AI brand names.
