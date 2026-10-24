# docs/architecture — Diseño del sistema y gobernanza

El *cómo y por qué* de la arquitectura. Documentos clave:

- **`gobernanza-db.md`** — diseño completo de gobernanza de datos: roles (least-privilege),
  schemas (medallion), extensiones, grants, RLS, trío de auditoría, mantenimiento.
- **`multi-tenancy.md`** — multi-tenancy jerárquico (árbol de tenants, política de subárbol, `ltree`).

> Léelos **antes** de tocar la base de datos. Las políticas RLS por tabla nacen en su migración.
