# ADR-0001: Pure core with ports and adapters

- **Status:** accepted; module names superseded by ADR-0014
- **Date:** 2026-10-24

## Context

ClearMD has a product goal (converting documents to Markdown) and a learning goal: building
**the same app with three GUI toolkits** (ttkbootstrap, PySide6 and flet) plus a CLI. If the conversion
logic lived inside each GUI, there would be three copies of the same behavior, impossible to keep
identical and hard to test without opening windows.

In addition, converting a PDF or an entire folder can take seconds or minutes, and each toolkit handles
concurrency differently: tkinter is not thread-safe (worker thread + queue + `after()`), Qt uses
`QThreadPool` with signals, and flet is asynchronous.

## Decision

Hexagonal architecture (ports and adapters):

- **`clearmd.core`** — the domain. Defines the ports (`DocumentConverter`, `FormatDetector`), the models
  and the use cases. It imports no GUI and no conversion library.
- **`clearmd.converters`** — adapters that implement `DocumentConverter` (markitdown and own converters).
- **`clearmd.presenter`** — MVP layer with the shared interaction logic (what is shown, what is enabled,
  how progress and errors are reported). The GUIs are thin views on top of it.
- **`clearmd.cli`** and one GUI per subpackage — input adapters.

Dependencies always point toward the core. The core offers a **synchronous API with a progress callback
and a cancellation token**; each adapter decides how to run it off its UI thread.

## Exception to the template doctrine

Principle 7 of the constitution and `03_stack.md` call for **a single active UI framework at a time**. ClearMD
has three on purpose, because comparing them is part of the project's goal. The exception is bounded as follows:

- each GUI lives in its own subpackage and is installed with its own extra;
- each executable bundles **a single** GUI;
- no GUI imports another; they only share `core` and `presenter`.

## Consequences

- **Gains:** a single place for the logic, testable without a GUI; adding an interface does not touch the core;
  the comparison between toolkits is fair because they all use the same engine.
- **Costs:** more layers and more indirection than a single-file app; the presenter contract has
  to be designed carefully so that it serves three different concurrency models.

## Alternatives considered

- **Three independent apps:** rejected because it triples the logic and the tests.
- **Core without a presenter:** rejected; each GUI would reimplement the interaction logic and the
  concurrency problem would be scattered.
