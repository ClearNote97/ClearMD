"""Consolidación de identificadores únicos entre varios DataFrames de Polars.

Nota: reescrito a Polars (la plantilla es Polars-first). A diferencia de pandas, Polars
NO tiene índice, así que se eliminó el parámetro `set_index`. Validar en el contenedor.
"""

from typing import Literal

import polars as pl


def consolidar_ids_unicos(
    dataframes: list[pl.DataFrame],
    col_id: str = "ID",
    return_as: Literal["dataframe", "list", "set"] = "dataframe",
) -> pl.DataFrame | list | set:
    """Consolida los IDs únicos presentes en varios DataFrames.

    Parameters
    ----------
    dataframes : list of pl.DataFrame
        DataFrames a consolidar.
    col_id : str, default 'ID'
        Nombre de la columna con el identificador único.
    return_as : {'dataframe', 'list', 'set'}, default 'dataframe'
        - 'dataframe': DataFrame de una columna (`col_id`).
        - 'list': lista ordenada de IDs únicos.
        - 'set': conjunto de IDs únicos.

    Raises
    ------
    ValueError
        Si `dataframes` está vacío o `return_as` no es válido.
    KeyError
        Si algún DataFrame no tiene la columna `col_id`.
    """
    if not dataframes:
        raise ValueError("La lista de DataFrames está vacía")

    unique_ids: set = set()
    for df in dataframes:
        if col_id not in df.columns:
            raise KeyError(f"La columna '{col_id}' no existe en uno de los DataFrames")
        unique_ids |= set(df.get_column(col_id).drop_nulls().unique().to_list())

    print(f"✅ Total de IDs únicos consolidados: {len(unique_ids)}")

    if return_as == "set":
        return unique_ids
    if return_as == "list":
        return sorted(unique_ids)
    if return_as == "dataframe":
        return pl.DataFrame({col_id: sorted(unique_ids)})

    raise ValueError("return_as debe ser 'dataframe', 'list' o 'set'")
