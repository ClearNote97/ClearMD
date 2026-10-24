# infra/db — Imagen del servicio `db`

Imagen propia de **PostgreSQL 18** que extiende la oficial para incluir las extensiones de
gobernanza que no vienen de fábrica: **pgaudit** y **pg_cron** (`pg_stat_statements` ya viene incluida).

## Por qué existe

`src/database/admin/00_create_extensions.sql` hace `CREATE EXTENSION pgaudit` y `pg_cron`. Eso falla
sobre la imagen oficial por dos razones, que esta pieza resuelve en dos lugares distintos:

| Requisito | Dónde se resuelve |
|---|---|
| El paquete de la extensión debe estar instalado | **Aquí** (`Dockerfile`: `postgresql-18-pgaudit`, `postgresql-18-cron`). |
| Debe precargarse antes de aceptar conexiones (`shared_preload_libraries`) | `docker-compose.yml` → `db.command`. |
| Debe activarse en la DB (`CREATE EXTENSION`) | `src/database/admin/00_create_extensions.sql`. |

## Cómo se usa

El servicio `db` del `docker-compose.yml` la construye (`build: { context: ./infra/db }`). No hay que
correr nada a mano: `docker compose up` la construye la primera vez.

> Para cambiar la versión de Postgres, edita el `FROM` de aquí **y** el paquete `postgresql-NN-*`.
> Si activas TimescaleDB en su lugar, replica este patrón sobre la imagen de Timescale.
