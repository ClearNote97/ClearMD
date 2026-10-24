# data/ — Datos del proyecto (fuera del código)

Datos que el proyecto consume o produce. **El contenido pesado no se versiona** (ver `.gitignore`);
sí viajan las carpetas y sus README.

| Carpeta | Rol |
|---|---|
| `seeds/` | Datos semilla para inicializar/poblar la DB (pequeños, versionables). |
| `storage/` | Almacenamiento de trabajo: crudos, procesados, modelos, exports. |
| `tests/` | Datasets pequeños y fijos usados por los tests (fixtures de datos). |
