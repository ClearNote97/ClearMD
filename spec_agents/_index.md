# Roster de agentes — índice maestro

Roster que este proyecto necesita. El *cómo* del formato y la materialización está en [`README.md`](./README.md).

## Coordinación / coherencia

| Agente | Propósito | `model_hint` | Herramientas |
|---|---|---|---|
| [`lead-architect`](./lead-architect.yaml) | Custodia la coherencia del conjunto: nada se contradice y todo traza al spec. Compuerta de cierre. | `frontier` | read, grep, glob |

## Especificar · construir · verificar (ciclo SDD)

| Agente | Propósito | `model_hint` | Herramientas |
|---|---|---|---|
| [`spec-author`](./spec-author.yaml) | Redactar/refinar `spec.md` · `plan.md` · `tasks.md` de una feature. | `frontier` | read, grep, glob, write, edit |
| [`backend-builder`](./backend-builder.yaml) | Implementar API/services/use_cases desde el plan. | `balanced` | read, grep, glob, edit, write, bash |
| [`frontend-builder`](./frontend-builder.yaml) | Construir la UI (Reflex/Flet): views, components, state. | `balanced` | read, grep, glob, edit, write |
| [`migration-writer`](./migration-writer.yaml) | Migraciones Alembic desde cambios de modelo, gobernanza-aware. | `balanced` | read, grep, edit, write, bash |
| [`test-writer`](./test-writer.yaml) | Tests unit + acceptance (test-first), contra el spec. | `balanced` | read, grep, glob, write, edit, bash |

## Revisión / calidad / seguridad

| Agente | Propósito | `model_hint` | Herramientas |
|---|---|---|---|
| [`code-reviewer`](./code-reviewer.yaml) | Calidad, bugs, performance — gate pre-cierre. | `balanced` | read, grep, glob |
| [`security-auditor`](./security-auditor.yaml) | Auth, endpoints, OWASP, secretos. | `frontier` | read, grep, glob |
| [`db-governance-reviewer`](./db-governance-reviewer.yaml) | Revisar (solo lectura) `admin/*.sql`, RLS y audit; regla de 2-aprobadores. | `balanced` | read, grep, glob |

## Documentación

| Agente | Propósito | `model_hint` | Herramientas |
|---|---|---|---|
| [`doc-writer`](./doc-writer.yaml) | Mantener `docs/` y `data-dictionary/` en sync con el código. | `balanced` | read, grep, glob, edit, write |

## Familia de datos / analítica (opt-in) — pipeline por fases

Coordina `analytics-lead`; cada fase la hace un especialista. Flujo: **ingesta → limpieza → consulta → stats/ML → visualización → reporte.**

| Agente | Fase / rol | `model_hint` | Herramientas |
|---|---|---|---|
| [`analytics-lead`](./analytics-lead.yaml) | Coordina el pipeline y enmarca la pregunta analítica. | `frontier` | read, grep, glob |
| [`data-ingestor`](./data-ingestor.yaml) | Adquiere datos a la capa cruda (raw/bronze, inmutable). | `balanced` | read, grep, glob, edit, write, bash, web |
| [`data-cleaner`](./data-cleaner.yaml) | Limpia/normaliza/valida (Polars; `src/utils`). | `balanced` | read, grep, glob, edit, write, bash |
| [`sql-analyst`](./sql-analyst.yaml) | Escribe y optimiza SQL (consultas, datasets/vistas). | `balanced` | read, grep, glob, edit, write, bash |
| [`stats-analyst`](./stats-analyst.yaml) | EDA, métricas y pruebas estadísticas, con rigor. | `frontier` | read, grep, glob, edit, write, bash |
| [`ml-engineer`](./ml-engineer.yaml) | Modelado ML reproducible, sin leakage. | `frontier` | read, grep, glob, edit, write, bash |
| [`viz-specialist`](./viz-specialist.yaml) | Visuales analíticos claros, accesibles y honestos. | `balanced` | read, grep, glob, edit, write, bash |
| [`insight-reporter`](./insight-reporter.yaml) | Traduce resultados a hallazgos accionables (negocio). | `balanced` | read, grep, glob, write, edit |

## Investigación académica (opt-in)

| Agente | Propósito | `model_hint` | Herramientas |
|---|---|---|---|
| [`literature-reviewer`](./literature-reviewer.yaml) | Buscar, leer y sintetizar fuentes con citas trazables. | `frontier` | read, grep, glob, web |
| [`academic-writer`](./academic-writer.yaml) | Redactar el manuscrito y la investigación en `docs/`. | `frontier` | read, grep, glob, write, edit |

> Activa estas dos familias solo cuando el proyecto haga **analítica/datos** o **investigación**
> (flag de investigación, §2 del contrato). El resto del roster aplica a cualquier app.
> Son las que más peso tendrán al **propagar** a las plantillas de datos (`Py_DA`, `Py_DA_SQL`).

---

> **Roles genéricos declarados a propósito** (`code-reviewer`, `security-auditor`): un harness pelado (p. ej.
> OpenCode) no los trae, así que el spec los incluye para ser **portable**. Si tu harness **ya** tiene uno
> equivalente (p. ej. Helix), la **regla de conflicto** del protocolo lo reutiliza en vez de duplicarlo.
