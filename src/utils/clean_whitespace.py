"""Limpieza de espacios en blanco en DataFrames de Polars.

Primer paso del flujo: normaliza nombres de columna y celdas de texto, convierte cadenas
vacías en null y elimina filas totalmente vacías. No modifica el DataFrame original (Polars
es inmutable: cada operación devuelve uno nuevo).

Nota: reescrito a Polars (la plantilla es Polars-first). Validar en el contenedor.
"""

import polars as pl


def limpiar_espacios_en_blanco(df: pl.DataFrame) -> pl.DataFrame:
    """Normaliza espacios en nombres de columna y en celdas de texto.

    - Recorta extremos y colapsa espacios internos en los nombres de columna.
    - Hace lo mismo en las celdas de texto (columnas String).
    - Convierte cadenas vacías en null y descarta las filas completamente nulas.
    """
    # Nombres de columna: colapsar espacios internos + recortar extremos
    df = df.rename({c: " ".join(c.split()) for c in df.columns})

    # Celdas de texto: colapsar espacios, recortar extremos y cadena vacía -> null
    df = df.with_columns(
        pl.col(pl.String)
        .str.replace_all(r"\s+", " ")
        .str.strip_chars()
        .replace("", None)
    )

    # Descartar filas totalmente nulas
    df = df.filter(~pl.all_horizontal(pl.all().is_null()))

    return df
