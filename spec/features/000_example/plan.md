# Plan — Feature 000 (ejemplo)

> El **CÓMO**. Debe poder leerse y ejecutarse sin adivinar. Enlaza al `spec.md`.

## Arquitectura
_Componentes tocados (frontend / backend / database / analytics) y cómo se conectan._

## Modelo de datos
- Tablas nuevas/modificadas: …
- ¿Bitemporal? ¿RLS (tenant)? ¿Auditada? → enlaza a `docs/architecture/gobernanza-db.md`.
- Migración Alembic prevista: …

## Contratos
_Endpoints / esquemas / eventos. Si es transversal, va también en `spec/contracts/`._

## Estrategia de pruebas
- Unit (espejo de `src/`): …
- Acceptance (contra el `spec.md`): `tests/acceptance/…`
