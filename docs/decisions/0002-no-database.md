# ADR-0002: No database

- **Status:** accepted
- **Date:** 2026-10-24

## Context

The ClearNote_Dev template ships PostgreSQL 18 with full governance (roles, RLS, pgaudit, pg_cron),
SQLModel and Alembic. ClearMD is a desktop app that reads files and writes files: it has no users,
tenants or data to query. The only persistent state it needs is the user's preferences
(theme, default options).

## Decision

- There is no database: no Postgres server, no ORM, no migrations.
- Preferences are stored in a TOML file inside the user configuration directory of each
  operating system, resolved with `platformdirs`.
- The report of each conversion batch is written as a file inside `ClearMD_Output` (ADR-0010), not to
  a database.

## Exceptions to the template doctrine

The following points of `spec/constitution/01_principles.md` **do not apply** to ClearMD because there is no
database; the principles remain intact as template doctrine:

- principle 3: "schema changes are materialized with Alembic migrations";
- principle 4: least-privilege in the DB, RLS and the two-approver rule for RLS/auditing;
- principle 5: data governance (bitemporality, PII per table, actor identity);
- principle 6: data dictionary.

The links from those principles to `docs/architecture/gobernanza-db.md` and `multi-tenancy.md` have no target
in this repo: those documents were deleted in the pruning (ADR-0009).

## Consequences

- **Gains:** zero services to start; the executable works without installing anything else; the
  development image no longer needs the Postgres one (625 MB).
- **Costs:** if a queryable conversion history is wanted in the future, this decision will have to be
  reopened. For a local history, SQLite (embedded, serverless) would be the natural choice.

## Alternatives considered

- **Keep Postgres "just in case":** rejected (principle 7, simplicity).
- **SQLite from the start:** rejected for now; no feature needs it.
