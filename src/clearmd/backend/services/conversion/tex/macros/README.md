# tex/macros — the author's own macros

Collected in document order, expanded with a budget, and substituted as text where they open or
close an environment (ADR-0022).

| Module | Role |
|---|---|
| `definition.py` | `MacroDefinition`: arguments, default, size and substitution of one use; `opens_or_closes_an_environment`. |
| `collect.py` | `collect_definitions`, `definition_sites`, `DefinitionSite`, `is_parametrized_def`: the definitions found in the nodes. |
| `expander.py` | `MacroExpander` with its budget (expansions, growth, nesting); `expansion_limit`, `BudgetExceeded`, `build_expander`. |
| `substitution.py` | `substitute_structural`: `\beq` → `\begin{equation}` in the text itself. |

`__init__.py` re-exports the names other packages use, with `__all__`. Imports: `definition` ←
`collect` ← `expander` ← `substitution`; the parsing context comes from `tex.parsing`.
