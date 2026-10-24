# src/utils — Utilidades transversales (Polars-first)

Funciones puras y reutilizables sobre DataFrames de **Polars**:

- `clean_whitespace.py` — normaliza espacios, vacíos → null, descarta filas nulas.
- `format_variables.py` — conversión de fechas/datetime/int/float (`strict=False` = coerce).
- `index_management.py` — consolida IDs únicos entre varios DataFrames.

> Polars es inmutable y sin índice: cada función devuelve un DataFrame nuevo.
