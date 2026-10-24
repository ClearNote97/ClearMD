# spec/ — What MUST be true (prescriptive)

The **system contract**. If the code does not match what is declared here, **the code is wrong**.
It follows the SDD flow: **Constitution → Spec → Plan → Tasks**.

| Folder / file | SDD level | Contents |
|---|---|---|
| `constitution/` | 1 | Project-wide rules: purpose, principles, scope, stack. |
| `roadmap.md` | — | What gets built and in which order (per project; **not** constitution). |
| `features/` | 2–4 | One folder per feature: `spec.md` (what), `plan.md` (how), `tasks.md` (steps). |
| `contracts/` | — | **Cross-feature** contracts, such as the UX contract shared by every GUI. |

> `docs/` answers *how and why it ended up this way*; `spec/` answers *what must be true*. **They fail
> differently.**
