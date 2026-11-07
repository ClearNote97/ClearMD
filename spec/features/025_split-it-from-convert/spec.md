# Feature 025 — "Split It" from Convert

## Goal

Convert can meet a PDF that is too big:
- one that would take longer than the time limit (AC-43 of feature 001);
- one that needs more memory than the limit (AC-42);
- one that was stopped at a limit while converting (AC-44).

ClearMD already says what to do ("Split it into smaller files"). Now it does it. A single
**Split the Large PDFs** action opens Split with those PDFs listed and a recommended number of
parts, chosen so that each part fits the limits. Their Markdown is kept (ADR-0043, ADR-0044).

## Sketch

```
Review (Convert)                                    Results (Convert)
 ⚠ big.pdf — could take more than 10 min ...         ⏹ big.pdf — stopped at the time limit ...
 [Split the Large PDFs (1)]                          [Split the Large PDFs (1)]
        │                                                   │
        └──────────► Split · step 1: big.pdf listed, Into [ 4 ] parts, Keep: Their Markdown
```

## Acceptance criteria (what MUST be true)

- [ ] **AC-01** Review offers **Split the Large PDFs (N)** when the plan holds a PDF:
  - warned about the time limit; or
  - left out for memory.

  Results offers it for the PDFs stopped at a limit. It is never offered for other formats, or
  when there are none.
- [ ] **AC-02** The action opens step 1 of Split:
  - only those PDFs are listed;
  - the cut is "Into N parts", with N recommended from the estimate so that each part fits the
    limits with a margin;
  - Keep is "Their Markdown";
  - the user can still change the cut and the list before going on.
- [ ] **AC-03** The recommended N is a pure function of the estimate and the limits, between 2
  and 1,000:
  - for time: the estimated seconds over 60 % of the time limit, rounded up;
  - for memory: the memory needed over 60 % of the worker's limit, rounded up.

  The larger of the two wins.
- [ ] **AC-04** The three windows show the action in the same place on Review and Results, as a
  secondary button. Its label is in English and Spanish, in Title Case.
