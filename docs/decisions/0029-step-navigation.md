# ADR-0029: Free navigation between the steps; one primary action per step

- **Status:** accepted
- **Date:** 2026-10-28
- **Refines:** ADR-0026 (the presenter), ADR-0027 (the rail and the four steps).

## Context

The author used v0.1.0 and asked for: moving freely between the four steps of the rail; the steps
not on screen dimmed; the primary button of each step disabled — not hidden — while the step
before is not done; and "Next" on steps 1 and 2, "Convert" only on step 3 (in v0.1.0 the review
already said "Convert", and the progress page had no button of its own).

## Decision

- **What is shown and what is done are separate.** The presenter keeps the batch's state (the
  seven states of ADR-0026) and, apart from it, the **page** on screen (1 Choose, 2 Review,
  3 Convert, 4 Results). `go_to(page)` changes only the page: every page can always be seen.
- **One primary action per page**, given by the presenter with its label, whether it is enabled
  and, when it is not, **why** in one line (never a disabled button without a reason):
  1 **Next** (plans the batch, then shows Review) · 2 **Next** (shows Convert) · 3 **Convert**
  (starts it; the progress is shown there; at the end, Results opens by itself) · 4 **Open
  results folder**, with **Convert more** next to it, as prominent.
- **Editing the inputs or the output after a plan drops the plan** (back to Ready): the Review
  page then says to press Next on step 1. Nothing can be edited while analyzing or converting.
- **"Convert more" asks every time** whether to keep the chosen files.
- The rail highlights the page on screen; the other steps are dimmed; each number sits in a
  circle drawn smooth.

## Consequences

- **Gains:** the user can look back and forth without losing anything; every disabled button
  explains itself; the flow reads the same in every GUI (the presenter owns it).
- **Costs:** the view protocol gains the page and its primary action; tests of the old
  "Convert on review" path change.
