# src/clearmd/i18n — Message catalogs (EN/ES)

One TOML file per language; tables become dotted keys (`[error.corrupt_file] message` →
`error.corrupt_file.message`). Every user-facing text comes from here (ADR-0012); English is the default
(ADR-0017). A test fails if a key or a placeholder exists in one language but not the other. Standard library
only, so backend and frontend can both use it.
