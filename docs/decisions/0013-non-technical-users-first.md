# ADR-0013: Designed for non-technical users first, with a shared UX contract

- **Status:** accepted
- **Date:** 2026-10-24

## Context

ClearMD serves students and academics, people preparing documents for LLMs, developers, and non-technical
users. The author's requirement: everything must be **foolproof**. If the app works for someone who has never
opened a terminal, it works for everyone.

Three GUIs built with three different toolkits (ADR-0001) will drift apart unless the experience is defined
once, outside any of them.

## Decision

- **The primary persona is a non-technical user.** When a design choice trades simplicity against power,
  simplicity wins in the GUIs; power lives in the CLI flags.
- The experience rules live in **`spec/contracts/ux.md`**, a contract shared by the three GUIs: always-visible
  state, progress and loading feedback, human error messages with a suggested action, an 8 px spacing grid,
  keyboard access, the "?" help window and the first-run welcome.
- **The core is designed for that experience**, even before any GUI exists:
  - it emits **progress events** (scanning, plan ready, converting file *i* of *n*, finished) that any
    interface can render;
  - every failure maps to an **error code** with a human message and a suggested action (from the catalogs,
    ADR-0012); technical details go to the batch report, never as a traceback on screen;
  - outputs are written atomically, so a cancelled or failed conversion never leaves a half-written file.

## Consequences

- **Gains:** one definition of "good experience" for three toolkits; the core's events and error codes make
  every interface informative by construction; the CLI benefits too (clear messages, exit codes).
- **Costs:** more design work in the core (events, error taxonomy) before anything is visible; the UX contract
  must be kept in sync with what each GUI can actually do.
