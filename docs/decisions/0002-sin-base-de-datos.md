# ADR-0002: Sin base de datos

- **Estado:** aceptada
- **Fecha:** 2026-10-24

## Contexto

La plantilla ClearNote_Dev trae PostgreSQL 18 con gobernanza completa (roles, RLS, pgaudit, pg_cron),
SQLModel y Alembic. ClearMD es una app de escritorio que lee archivos y escribe archivos: no tiene usuarios,
tenants ni datos que consultar. El único estado persistente que necesita son las preferencias del usuario
(tema, opciones por defecto).

## Decisión

- No hay base de datos: ni servidor Postgres, ni ORM, ni migraciones.
- Las preferencias se guardan en un archivo TOML dentro del directorio de configuración del usuario de cada
  sistema operativo, resuelto con `platformdirs`.
- El reporte de cada lote de conversión se escribe como archivo dentro de `ClearMD_Output` (ADR-0010), no en
  una base de datos.

## Excepciones a la doctrina de la plantilla

Los siguientes puntos de `spec/constitution/01_principles.md` **no aplican** a ClearMD por no existir base de
datos; los principios se mantienen intactos como doctrina de la plantilla:

- principio 3: "los cambios de esquema se materializan con migraciones Alembic";
- principio 4: least-privilege en la DB, RLS y la regla de dos aprobadores para RLS/auditoría;
- principio 5: gobernanza de datos (bitemporalidad, PII por tabla, identidad de actores);
- principio 6: diccionario de datos.

Los enlaces de esos principios a `docs/architecture/gobernanza-db.md` y `multi-tenancy.md` quedan sin destino
en este repo: esos documentos se eliminaron en la poda (ADR-0009).

## Consecuencias

- **Se gana:** cero servicios que levantar; el ejecutable funciona sin instalar nada más; la imagen de
  desarrollo deja de necesitar la de Postgres (625 MB).
- **Se paga:** si en el futuro se quiere un historial consultable de conversiones, habrá que reabrir esta
  decisión. Para un historial local, SQLite (embebido, sin servidor) sería la opción natural.

## Alternativas consideradas

- **Mantener Postgres "por si acaso":** descartada (principio 7, simplicidad).
- **SQLite desde el inicio:** descartada por ahora; no hay ninguna funcionalidad que lo necesite.
