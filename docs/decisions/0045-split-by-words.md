# ADR-0045: Parts that fit an AI are measured in words, approximately; Markdown is cut at headings

- **Status:** accepted
- **Date:** 2026-11-07
- **Refines:** ADR-0043, ADR-0044.
- **Decided by:** a Helix council of 7 roles (2026-11-07), APPROVE_WITH_PRECONDITIONS.

## Context

An AI reads a limited amount of text at once, counted in tokens. ClearMD's main user is not
technical, and ClearMD downloads nothing, so it has no tokenizer. Limits also differ from one AI
to another, and they change over time.

## Decision

- **Words, approximately.** The cut reads "Parts of About [N] Words": one radio and one number,
  as the other two cuts. It is never "tokens", and never an AI's name.
  - The default is 30,000 words. That is conservative: about 40,000 tokens in English, and more
    in Spanish, which costs about 1.3–1.55 times as many tokens (the researcher's sources:
    OpenAI's guidance, Petrov et al. 2023).
  - A generic hint: "an AI reads a limited amount of text at once; if it refuses a part, choose
    fewer words."
- **Counted in the worker.** Words are counted per page (`\w+`, with each CJK character counting
  as a word).
- **How pages are grouped:** whole and in order, each group up to N words.
  - A page larger than N becomes a part alone, and the summary notes it.
  - A PDF with no text at all fails with a reason (`nothing_to_measure`). A scanned PDF never
    becomes a silent single part.
- **Markdown** is cut in the worker.
  - Cuts fall at headings outside code fences.
  - A section larger than the size is cut at its paragraphs, and a paragraph larger than the size
    becomes a part alone.
  - Into N parts: the cut is balanced by words. Every N pages does not apply: the file is left
    out with a reason (`cut_not_for_markdown`), shown on Review before anything runs.
- **The command line:** `--split-words N`, exclusive with the other two cuts. The setting is
  `split_words`.

## Consequences

- **Gain:** a plain, honest unit with no brands that go stale.
- **Costs:**
  - the estimate's error is not measured on a corpus (the skeptic's gap);
  - the part count is known only after running (the devil's advocate's and innovator's dissent,
    left for later).

## Alternatives considered

- **Tokens:** opaque to the persona.
- **Presets named after AIs:** names brands that go stale. The arbiter ruled them inadmissible.
- **Size classes in a list:** a second control breaks the one-radio, one-number pattern.
- **A Smaller/Larger stepper with no number:** radical, but it breaks the pattern and hides the
  size.
