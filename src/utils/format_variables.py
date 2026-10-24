"""Conversión de formatos de variables (fechas, enteros, decimales) en Polars.

Cada función recibe las columnas a convertir y devuelve un DataFrame nuevo. Las columnas
que no existen se ignoran. Las conversiones usan `strict=False` -> los valores que no
convierten quedan en null (equivalente a "coerce").

Nota: reescrito a Polars (la plantilla es Polars-first). Validar en el contenedor.
"""

from datetime import datetime
from typing import Literal

import polars as pl

TimestampUnit = Literal["ms", "s", "excel"]


def _a_datetime(name: str, dtype: pl.DataType,
                date_format: str | None, timestamp_unit: TimestampUnit | None) -> pl.Expr:
    """Construye la expresión que convierte una columna a datetime."""
    col = pl.col(name)
    if dtype.is_numeric():
        if timestamp_unit == "excel":
            # días desde el epoch de Excel (1899-12-30)
            return (pl.lit(datetime(1899, 12, 30)) + pl.duration(days=col)).alias(name)
        # ms por defecto (heurística simple; pasar timestamp_unit='s' si aplica)
        return pl.from_epoch(col, time_unit=(timestamp_unit or "ms")).alias(name)
    # Texto -> datetime (si date_format es None, Polars infiere)
    return col.str.to_datetime(format=date_format, strict=False).alias(name)


def format_datetime(df: pl.DataFrame, columns: list[str],
                    date_format: str | None = None,
                    timestamp_unit: TimestampUnit | None = None) -> pl.DataFrame:
    """Convierte columnas a fecha y hora, **conservando la hora**."""
    exprs = [_a_datetime(c, df.schema[c], date_format, timestamp_unit)
             for c in columns if c in df.columns]
    return df.with_columns(exprs) if exprs else df


def format_dates(df: pl.DataFrame, columns: list[str],
                 date_format: str | None = None,
                 timestamp_unit: TimestampUnit | None = None) -> pl.DataFrame:
    """Convierte columnas a fecha, **descartando la hora** (queda solo la fecha)."""
    exprs = [_a_datetime(c, df.schema[c], date_format, timestamp_unit).dt.date().alias(c)
             for c in columns if c in df.columns]
    return df.with_columns(exprs) if exprs else df


def format_int(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Convierte columnas a entero (`Int64`, nullable de forma nativa)."""
    return df.with_columns(
        [pl.col(c).cast(pl.Int64, strict=False) for c in columns if c in df.columns]
    )


def format_flt(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Convierte columnas a decimal (`Float64`)."""
    return df.with_columns(
        [pl.col(c).cast(pl.Float64, strict=False) for c in columns if c in df.columns]
    )
