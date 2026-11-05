# tex/parsing — the parsing context

pylatexenc's defaults plus what ClearMD needs to read real documents: argument parsers for the
commands it does not know, a tolerant walker, and the mask that hides what is not source.

| Module | Role |
|---|---|
| `braces.py` | Where a brace closes; `forget_brace_pairs` frees the cache of a large text. |
| `cursor.py` | What every parser reads off the walker: whitespace, the `\verb` window, a chars node, a recovered error. |
| `verbatim_args.py` | Parsers for `\cmidrule`, verbatim environments, `\verb`, `\url`/`\href`. |
| `definition_args.py` | `ParsedDef`, `DefParser`, `RawBodyParser`: definitions keep their body raw. |
| `specs.py` | The macro and environment specs; `make_context`. |
| `walker.py` | `parse`, `ParseError`, `Unparseable`. |
| `mask.py` | `mask`: comments, code, `\verb`, `\iffalse` and URL arguments replaced by spaces. |

`__init__.py` re-exports the names other packages use, with `__all__`. Imports: `cursor`, `braces` ←
`verbatim_args`, `definition_args` ← `specs`; `mask` ← `braces`, `cursor`; `walker` stands alone.
