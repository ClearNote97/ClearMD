# src/database/app — Schema transaccional `app` (OLTP)

Modelos de datos de la aplicación y su acceso.

- `models/` — modelos **SQLModel** (tablas del schema `app`). Aquí se decide bitemporalidad, PII y RLS por tabla.
- `repositories/` — acceso a datos: consultas y persistencia por agregado.
