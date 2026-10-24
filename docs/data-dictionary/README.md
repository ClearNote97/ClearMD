# docs/data-dictionary — Diccionario de datos (índice maestro)

Qué significa cada **tabla y columna**, organizado **por schema** (espeja la arquitectura medallion +
gobernanza). Este archivo es el **índice**; el detalle vive en cada subcarpeta.

| Schema | Carpeta | Rol |
|---|---|---|
| `app` | [`app/`](./app/) | Datos transaccionales de la aplicación (OLTP). |
| `gold` | [`gold/`](./gold/) | Productos de analítica listos para consumo (OLAP). |
| `admin` | — | Gobernanza (audit_log, governance_registry, pii_columns). Ver `docs/architecture/`. |

> _bronze/silver_ se documentan aquí cuando se activen (hoy comentados en `admin/02_create_schemas.sql`).
> Convención por tabla: **nombre · propósito · ¿bitemporal? · ¿PII? · ¿tenant-scoped? · columnas**.
