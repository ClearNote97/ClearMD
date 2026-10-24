# src/database/app/models — Modelos SQLModel (schema `app`)

Una clase por tabla. Al crear una tabla de estado/referencia, decidir: **¿bitemporal?**, **¿PII?**
(tratamiento omit/mask/hash), **¿tenant-scoped?** (RLS). Documentar en el diccionario de datos.
Los cambios de esquema se materializan con **migraciones Alembic**, no a mano.
