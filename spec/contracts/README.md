# spec/contracts — Cross-feature contracts

Contracts that **span features**: rules several parts of the system must honor alike. A contract of a single
feature belongs in its `spec/features/NNN_…/plan.md`.

| Contract | Binds |
|---|---|
| [`ux.md`](./ux.md) | Every GUI (and partly the CLI): state, progress, errors, help, layout, accessibility (ADR-0013). |
