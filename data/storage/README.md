# data/storage — Almacenamiento de trabajo (no versionado)

Casa de los datos que se mueven. Su **contenido está en `.gitignore`**; solo viajan las carpetas.

| Subcarpeta | Rol |
|---|---|
| `raw/` | Datos crudos tal cual llegan (bronze). Inmutables. |
| `processed/` | Datos limpios/transformados (silver). |
| `exports/` | Salidas para consumo externo (CSV/Parquet, reportes). |
| `mlmodels/` | Artefactos de modelos entrenados. |
