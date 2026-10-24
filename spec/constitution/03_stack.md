<!--
====================================================================
 03 — STACK  ·  Nivel 1 (Constitución)
--------------------------------------------------------------------
 Lo único CONSTITUCIONAL aquí es el lenguaje: Python. Todo lo demás
 (motor de datos, base de datos, ORM, UI…) es el STACK POR DEFECTO
 recomendado de la plantilla: un punto de partida sólido, pero
 AJUSTABLE según la necesidad del proyecto. Cambiar un default se
 documenta con un ADR (docs/decisions/); cambiar el lenguaje ya no
 sería un proyecto ClearNote_Dev.
====================================================================
-->

# 03 — Stack

## El invariante

**Python-first.** Python es el piso y la primera opción de esta plantilla — un solo lenguaje de front a
back reduce fricción y contexto. Todo lo que sigue es *default*, no *ley*.

**Otros lenguajes NO están descartados**, pero viven en los **bordes** y con justificación (ADR): p. ej. un
front web en TypeScript, SQL, o un binario en Rust/Go. El núcleo sigue siendo Python; el borde poliglota se
decide en la **conversación de arranque** (abajo) y se registra. La **modularidad** (principio 8) es lo que
hace barato ese borde: añadir/cambiar un lenguaje en una zona no debe arrastrar al resto.

## Stack por defecto (recomendado — ajustable por proyecto)

Es lo que trae la plantilla lista para funcionar. Sirve tal cual para la mayoría de los casos; si un
proyecto necesita otra cosa, se cambia y se registra el porqué en un ADR.

| Capa | Default | Por qué es el default |
|---|---|---|
| Gestor de paquetes | **`uv`** | Rápido, `uv.lock` reproducible; reemplaza pip/venv/pip-tools. |
| DataFrames | **Polars** | Rápido y eficiente en memoria; API expresiva e inmutable. |
| Interop de datos | **PyArrow**, `fastexcel`, `xlsxwriter` | Parquet/Arrow y Excel sin arrastrar pandas. |
| Base de datos | **PostgreSQL 18** | OLTP+OLAP maduro; RLS, particiones, extensiones, bitemporalidad. |
| ORM / modelos | **SQLModel** sobre **SQLAlchemy 2** | Tipado Pydantic + potencia de SQLAlchemy; una sola definición. |
| Driver | **psycopg2** | Driver sincrónico estable para Postgres. |
| Migraciones | **Alembic** | Historial versionado del esquema; `--autogenerate` desde `SQLModel.metadata`. |
| Entorno | **Docker + Dev Containers** | Reproducibilidad (principio 3); "reopen in container" y listo. |

> Un proyecto puede ser **solo Python** (scripts, análisis, librería) y no usar DB, ORM ni Docker.
> Esas capas se activan cuando el proyecto las necesita, no por venir en la plantilla.

## Menú opcional (activar solo cuando el proyecto lo pida)

Se activan descomentando en `requirements.txt` / `docker-compose.yml`. **Nunca** activar los que compiten entre sí.

| Necesidad | Opción(es) | Regla |
|---|---|---|
| API independiente | **FastAPI** + Uvicorn | Solo si hay front separado o terceros consumen la API. |
| Interfaz | Cualquier **framework de UI en Python**: Reflex/NiceGUI (web), Flet (desktop/móvil), PyQt/PySide, ttkbootstrap/Tkinter (desktop), Textual (TUI)… | **Elegir UNO** según el tipo de app (se decide en el arranque); nunca dos a la vez. |
| API GraphQL | Strawberry | En lugar de, o junto a, REST — con criterio. |
| Analítica / ML | scikit-learn, xgboost, statsmodels, **MLflow** | Según complejidad; artefactos a `data/storage/mlmodels/`. |
| Orquestación | **Prefect** | Para pipelines con reintentos/monitoreo. |
| Series de tiempo | **TimescaleDB** | Servicio aparte en compose; activar solo si hay series. |
| Reverse proxy | **Nginx** | Config en `scripts/nginx/`; revisar TLS antes de producción. |
| pandas (legacy) | pandas, numpy, xlrd | **Solo compatibilidad**; nunca como motor principal junto a Polars. |

## Preguntas de arranque del stack (conversación de sesión 1)

En la **primera sesión** de un proyecto se resuelve —en conversación, no por defecto silencioso— el stack.
Python-first es el punto de partida; cada respuesta se **registra aquí**. Preguntas:

1. **Tipo de interfaz** → define el framework de UI: ¿web, escritorio, móvil, TUI, API sin UI, o notebook/script?
2. **¿Solo Python, o habrá otros lenguajes en algún borde?** (front web en TS, SQL, binario en Rust/Go). Si sí: ¿en qué zona y por qué?
3. **Datos:** ¿hay base de datos? ¿Postgres (default) u otra? ¿ORM (SQLModel default)? ¿series de tiempo?
4. **Analítica / ML:** ¿el proyecto la necesita (`src/analytics/`)? ¿qué librerías?
5. **Integraciones / API:** ¿expone API (FastAPI / GraphQL)? ¿consume terceros?
6. **Ejecución / despliegue:** ¿basta dev local con Docker, o hay orquestación (Prefect) / reverse proxy / deploy?

> El agente en sesión **dispara** esta conversación en el arranque (Estado 0) y **no asume**: pregunta y, al
> decidir, actualiza este archivo. El ritual está en `README_AGENTS.md` §9.
>
> *(Opcional, según el harness: para conducir bien esta interrogación puedes apoyarte en una skill de
> levantamiento de requisitos — p. ej. `grill-me` en Helix. Es un mecanismo del harness, no una dependencia
> de la plantilla: las preguntas de arriba son la fuente agnóstica.)*

## Reglas que se mantienen (mientras se use el stack por defecto)

Estas no dependen del gusto sino de los principios (01); aplican en cuanto la capa correspondiente está en juego:

- **Secretos por archivo** (`*_FILE`), nunca en claro en el repo. _(Vale siempre: es seguridad, principio 4.)_
- **`uv.lock` se versiona**; tras tocar dependencias: `uv lock && uv sync`. _(Vale siempre que haya Python con uv.)_
- **Un** motor de DataFrames como estándar y **un** framework de UI activos a la vez. _(Si se usan.)_
- El esquema de la DB cambia **solo vía Alembic**; la gobernanza se aplica con el SQL idempotente de
  `src/database/admin/` (ver `docs/architecture/gobernanza-db.md`). _(Si el proyecto usa Postgres.)_
- Si el proyecto incorpora **Node.js/TypeScript**, el gestor es **pnpm** con las defensas de supply-chain del contrato.

---

> El stack sirve al propósito (00) dentro del alcance (02) y bajo los principios (01).
> Python es el piso; el resto es andamiaje que se adapta —y se justifica— proyecto a proyecto.
