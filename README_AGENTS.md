# 🤝 README_AGENTS — Dinámica de trabajo con agentes de IA + ClearNote

> **Qué es este archivo.** El contrato de trabajo entre **tu metodología** (Dev Containers desechables, `uv`, Python, datos y —cuando aplique— bases de datos SQL) y **el agente de IA con el que trabajes** — por ejemplo **Claude Code**, **OpenCode** o **[Helix](https://github.com/ftuga/helix_asisten)**. Es un recordatorio para los dos: para ti, para arrancar cada sesión; para el agente, para saber cómo operar en este proyecto. A lo largo del texto, **"yo" = el agente** que estés usando.
>
> **Cópialo tal cual en la raíz de cada proyecto que hagamos juntos.** Es **agnóstico a propósito**: no nombra ningún cliente ni proyecto concreto. Lo que cambia de un repo a otro es el **contexto** (§2), no el contrato.

---

## Índice

1. [El modelo mental: dos mundos separados](#1-el-modelo-mental-dos-mundos-separados)
2. [Los dos ejes de contexto (tipo de trabajo · SQL o no)](#2-los-dos-ejes-de-contexto-tipo-de-trabajo--sql-o-no)
3. [Ritual de arranque de cada sesión](#3-ritual-de-arranque-de-cada-sesión)
4. [Cómo nos conectamos (`docker exec`, sin puertos)](#4-cómo-nos-conectamos-sin-puertos-sin-instalarme-en-el-contenedor)
5. [La dinámica en paralelo](#5-la-dinámica-en-paralelo)
6. [Convención de carpetas (`sandbox/` → `tests/` → `output/`)](#6-convención-de-carpetas-proteger-el-entregable)
7. [Estándar de documentación (cuatro capas)](#7-estándar-de-documentación-cuatro-capas)
8. [Mejores prácticas: transversales + por tipo de trabajo](#8-mejores-prácticas-transversales--por-tipo-de-trabajo)
9. [Los dos estados del proyecto (Estado 0 vs Estado N)](#9-los-dos-estados-del-proyecto)
10. [Recordatorios firmes](#10-recordatorios-firmes-para-los-dos)
11. [Estándar de conexión a SQL desde Python](#11-estándar-de-conexión-a-sql-desde-python-mío)
12. [Tratamiento de las tablas materializadas — bitácora de jobs (estándar pendiente)](#12-tratamiento-de-las-tablas-materializadas--bitácora-de-ejecución-de-jobs-estándar-pendiente)
13. [Acelerador opcional: mapa de código para agentes (`graft`)](#13-acelerador-opcional-mapa-de-código-para-agentes-graft)

> **Secciones 1–10:** la **dinámica de trabajo** (agente ⇄ Dev Container). **Sección 11:** mi **estándar de código** para SQL. **Sección 12:** tratamiento de tablas materializadas. Las secciones 11–12 solo aplican cuando el proyecto se conecta a SQL (ver Eje 2 en §2).

---

## 1. El modelo mental: dos mundos separados

Cuando abres el proyecto con **Reopen in Container**, existen dos entornos que **no se mezclan**:

| | **Host (tu WSL)** | **Contenedor (Dev Container)** |
|---|---|---|
| Qué vive ahí | El **agente de IA** (Claude Code / OpenCode / [Helix](https://github.com/ftuga/helix_asisten)) + su contexto: memoria, skills, hooks | El **runtime real**: Python, `uv`, drivers de BD, conexión a la base de datos |
| Rol | El **cerebro** — proceso, criterio, metodología | Las **manos** — ejecución y verificación real |
| ¿Se desecha? | **No.** Es tu base permanente, como VS Code | **Sí.** Lo botas al terminar; el host queda limpio |

**Regla de oro:** lo que no quieres instalar en el host es el *toolchain del proyecto* — y ese ya vive en el contenedor. El **agente** en el host **no es basura de proyecto**, es tu herramienta permanente.

---

## 2. Los dos ejes de contexto (tipo de trabajo · SQL o no)

Antes de trabajar, yo (el agente) me sitúo con **dos ejes independientes**. Esto es **contexto de arranque**, no un cambio de motor: mi forma de operar es la misma; lo que cambia es que **entro sabiendo dónde estoy parado**.

**Eje 1 — Tipo de trabajo.** Define *dónde pongo el peso* (ver §8):

| Familia | Incluye |
|---|---|
| **Desarrollo de Aplicaciones** | Apps, sistemas, código de producto |
| **Trabajo con datos** | Analítica · Ciencia de Datos · Investigación Académica |

> Los tres trabajos con datos son la **misma base**. La **investigación académica** es un **flag** encima de "trabajo con datos": enciende una capa extra de rigor (trazabilidad de fuentes, control de alucinaciones, revisión de literatura) y hace aparecer la subestructura de `docs/` del artículo (§7). No es un tercer tipo.

**Eje 2 — ¿SQL o no?** Independiente del anterior. Hay plantillas pensadas para **conectarse a bases SQL** y plantillas que **no**. Lo detecto **mirando las carpetas** (`data/sql/`, `src/config/`, prefijos `PG_`/`MSSQL_` en `.env`); si hay duda, **te pregunto**. Si el proyecto es SQL, aplican las §11–12.

---

## 3. Ritual de arranque de cada sesión

El arranque tiene **dos manos**: lo que haces **tú** (setup físico) y lo que hago **yo** (el agente). Primero lo **cognitivo** (entender *qué* vamos a hacer), después lo **físico** (confirmar que las manos están listas).

### Lo que hago yo (el agente), apenas veo este README en el repo

```
1. TIPO DE TRABAJO (Eje 1) — infiero-y-confirmo.
   Deduzco del repo y te pido confirmación explícita:
   "Veo que es un proyecto de datos con SQL, ¿vamos hoy por analítica?"
   Siempre hay un momento de confirmación. Si es investigación, lo marco como flag.

2. SQL (Eje 2) — lo detecto de las carpetas; si hay duda, te pregunto.

3. MEMORIA del proyecto — la cargo si existe. Si es la primera vez, la creo con esta dinámica
   (scope de proyecto, no global) y la apunto a la fuente de verdad en docs/ (§7).

4. FRESCURA (staleness) — si hay commits más nuevos que la memoria, te aviso ANTES de operar.

5. PUENTE de ejecución — docker ps. Si el contenedor no está arriba, te lo pido
   (no corro en el host). Distingo Estado 0 vs Estado N (§9).

6. OBJETIVO concreto de la sesión — lo confirmamos y arrancamos.
```

### Lo que haces tú (setup físico)

```
□ Abriste el proyecto en VS Code → Reopen in Container (Ctrl+Shift+P).
□ Esperaste a que el postCreateCommand termine (uv sync o uv init según el estado, §9).
□ ¿Es Estado 0? → definimos objetivo, poblamos .env, confirmamos sandbox/ + tests/ + output/,
  commiteamos pyproject.toml + uv.lock.
□ ¿Es Estado N? → verificas que .env exista y que el contenedor esté arriba.
□ Lanzaste el agente (Claude Code / OpenCode / [Helix](https://github.com/ftuga/helix_asisten)) desde una terminal WSL del host (no la integrada del contenedor).
□ Confirmamos el puente: docker ps → docker exec ... python --version (llega al runtime real).
```

---

## 4. Cómo nos conectamos (sin puertos, sin instalarme en el contenedor)

**No me instalas dentro del contenedor.** Sumaría peso a cada imagen sin necesidad. En vez de eso:

- Yo corro en el **host** (el agente, vivo al 100%).
- Los archivos se comparten solos por el **bind-mount** del workspace: yo edito en el host, tú lo ves en VS Code al instante, y al revés.
- Para **ejecutar y comprobar** dentro del runtime real, uso el canal nativo de Docker — **`docker exec`**, no un puerto de red:

```bash
docker ps                                          # descubro el contenedor que VS Code levantó
docker exec -w /workspaces/<NOMBRE-DEL-PROYECTO> <ID> \
    uv run python scripts/run_pipeline.py           # corro DENTRO del contenedor, sin instalar nada ahí
```

> `<NOMBRE-DEL-PROYECTO>` = el nombre de la carpeta (VS Code monta el workspace en `/workspaces/<carpeta>`).
> `<ID>` = el id/nombre que aparece en `docker ps`.

**Costo en disco de tenerme:** cero. Nunca toco el interior del contenedor; solo ejecuto a través de él.

---

## 5. La dinámica en paralelo

Con el contenedor activo, trabajamos a la vez:

- **Tú** editas/revisas en VS Code (dentro del contenedor) y das dirección.
- **Yo** (desde una terminal WSL del host) edito código, y cuando toca **verificar** ejecuto vía `docker exec` y **leo la salida real** (stdout, stderr, exit code) — no supongo que funciona: lo compruebo.

Me entero de lo que pasa por **dos vías**:
1. **`docker exec`** → para *ejecutar* y capturar comportamiento vivo (una query, un traceback, un `df.shape`).
2. **Lectura de archivos** → todo el workspace lo leo directo desde el host (no necesito `docker exec` para leer, solo para correr).

---

## 6. Convención de carpetas: proteger el entregable

La convención **depende del tipo de trabajo** (Eje 1, §2). Dos variantes, un mismo principio: **separar el tanteo de lo verificado y proteger el entregable.**

### Variante A — Trabajo con datos (analítica / DS / investigación)

```
sandbox/    → experimentos desechables. Su CONTENIDO no se versiona; aquí se rompe sin miedo.
tests/      → verificación formal (pytest): happy path + edge + caso vacío. El gate.
output/     → SOLO resultados finales, ya verificados. El entregable real.
```
**Flujo:** `sandbox/` → `tests/` → `output/`. Nada llega a `output/` sin pasar el gate.

### Variante B — Desarrollo de aplicaciones (Spec-Driven Development)

```
spec/       → lo que DEBE ser verdad (constitución, features, plan, contratos). Prescriptivo.
src/        → la implementación (arquitectura limpia).
tests/      → verificación: unit (espejo de src) + acceptance (por feature, contra el spec).
docs/       → cómo y por qué es así lo construido. Descriptivo.
sandbox/    → OPCIONAL (experimentos sueltos).
```
**Sin `output/`:** el entregable es el código / la app corriendo. Los outputs de analítica van a su casa
(la DB `gold`, `data/storage/`), **nunca** a una carpeta única ni dentro de `src/`.

**Universal en ambas variantes:** `tests/` siempre, `docs/` siempre, `README.md` por carpeta, y el patrón de placeholders.

### La estructura viaja; el contenido depende de su sensibilidad

Las **carpetas** existen desde el nacimiento del repo (para que la estructura viaje con la plantilla), aunque estén vacías. Cada carpeta lleva un **`README.md`** que cumple **doble función**: sostiene la carpeta en git (git no versiona carpetas vacías) **y** la documenta en 2–3 líneas (un mini-README que explica *por qué existe*). No usamos `.gitkeep` (es oculto y por convención va vacío).

En `sandbox/`, ignoramos el **contenido** pero conservamos su `README.md`. En el `.gitignore`:

```gitignore
sandbox/*
!sandbox/README.md
```

Así la **carpeta y su explicación viajan** con la plantilla, pero **la basura de experimentos nunca se commitea**. `tests/` y `output/` se versionan completos.

---

## 7. Estándar de documentación (cuatro capas)

La documentación debe ser **fácil de entender para tus yos futuros y para mí en sesiones nuevas**. Por eso cada pieza tiene **dueño y audiencia claros**:

| Capa | Archivo(s) | Qué contiene | Audiencia |
|---|---|---|---|
| **1. Cómo trabajamos** | `README_AGENTS.md` | El contrato agente ⇄ tú (este archivo; genérico, igual en cada repo) | Tú + yo |
| **2. Qué es el proyecto** | `README.md` (raíz) | Objetivo, qué ingiere/produce, cómo se corre, stack (único por repo) — **documento vivo** | Todos |
| **3. Por qué se decidió** | Bitácora de decisiones en `docs/` | Decisiones de diseño no triviales + su *por qué* | Tú + yo (futuro) |
| **4. Qué hace cada carpeta** | `README.md` por carpeta | Los mini-READMEs de §6 | Quien entra a la carpeta |

**Reglas del estándar:**

- **`README_AGENTS.md` y `README.md` son documentos separados** (uno es *cómo trabajamos*, el otro *qué es este proyecto*). No se fusionan.
- **Descubrimiento por el agente:** este contrato es la **fuente de verdad**. Los agentes lo encuentran vía **`AGENTS.md`**
  (entrada estándar que auto-leen: apunta aquí + lleva lo específico del proyecto) y **`CLAUDE.md`** (puntero fino → `AGENTS.md`, para Claude Code).
- **El `README.md` de proyecto es un documento VIVO.** En la plantilla trae una **línea base** (instalación + especificaciones técnicas), pensada para quien clona el repo. Cuando el requerimiento del proyecto queda **planificado**, esa línea base **no se amplía: se elimina y el `README.md` se reescribe desde cero** como el README real del proyecto (objetivo, qué ingiere/produce, cómo se corre). A partir de ahí **se actualiza a medida que el trabajo avanza**.
- **Fuente única de verdad de las decisiones = un archivo humano-legible en `docs/`.** La bitácora de decisiones vive ordenada **ahí**, para que un humano la lea. La memoria del agente (p. ej. `.claude/memory/` en Claude Code) **apunta a ese archivo**, no guarda una copia divergente. Se sincronizan; **`docs/` manda**.
- **El set completo de documentación va en TODAS las plantillas**, no solo en las más grandes.

### `docs/` cuando es investigación académica

Con el flag de investigación encendido (§2), en `docs/` vive **todo lo que se escribe del artículo**: el manuscrito (fuente), las referencias/bibliografía, notas de lectura, revisión de literatura. Esta subestructura **no existe a priori**: se materializa solo cuando defino que es investigación.

### Proceso ↔ entregable (dónde vive cada cosa)

`docs/` responde *"¿cómo y por qué?"* (conocimiento en construcción, iterativo, legible). `output/` responde *"¿cuál es el entregable final y verificado?"*.

| Cosa | Dónde | Por qué |
|---|---|---|
| Manuscrito (fuente), bibliografía, notas de lectura | **`docs/`** | Escritura viva, se edita mil veces |
| Paper final compilado (PDF), figuras/tablas finales | **`output/`** | Entregable cerrado que pasó revisión |
| Presentaciones (deck exportado que muestras) | **`output/presentaciones/`** | Entregable de comunicación; la fuente puede vivir en `docs/presentaciones/` mientras se arma |

> **El *gate* de `output/` también aplica a la escritura y lo visual — pero se verifica distinto.** Para entregables **computacionales**, el gate es un test (pytest, `df.shape`). Para entregables de **escritura o visuales** (paper, presentación), el gate es **tu revisión y aprobación**. Mismo principio en ambos: *nada llega a `output/` sin verificar*.

---

## 8. Mejores prácticas: transversales + por tipo de trabajo

### Transversales (aplican a TODO tipo de trabajo)

- **Reproducibilidad** — estándar universal, no exclusivo de datos: `uv.lock` versionado, semillas fijas, entorno determinista. Si `uv.lock` cambia, se commitea.
- **Tests** — SIEMPRE fundamentales para la rigurosidad, en las tres ramas. Todo bug corregido lleva un **test que lo reproduce antes del fix**; cubrir happy path + edge case + caso vacío.

### Énfasis por tipo de trabajo (solo contexto: *dónde pongo el peso*)

| Rama | Énfasis específico | Entregable típico |
|---|---|---|
| **Desarrollo de apps** | Arquitectura limpia, `code-review` antes de dar por completo, seguridad en auth/endpoints | Código de producto |
| **Trabajo con datos** (analítica/DS) | Gate `sandbox→tests→output`, procedencia del dato, estándar SQL cuando aplica (§11–12) | Dataset / reporte / figuras en `output/` |
| **+ Flag investigación** | Sobre datos: rigor de citas y trazabilidad de fuentes, revisión de literatura, manuscrito en `docs/`, y una capa de skills propias del énfasis (control de alucinaciones) | Paper en `output/`, manuscrito en `docs/` |

> **No enumero agentes ni skills concretos aquí**: los uso según se van necesitando. El contrato debe ser estable y legible, no un catálogo que envejece. El detalle vive en la memoria del agente del proyecto.

---

## 9. Los dos estados del proyecto

Esta es la diferencia clave al arrancar. **El comportamiento del `postCreateCommand` cambia según en qué estado estés.**

### 🟢 Estado 0 — Proyecto recién nacido (antes del primer `uv`)

**Cómo se reconoce:** solo existe `requirements.txt`. No hay `pyproject.toml`, ni `uv.lock`, ni `.venv`. El contenedor nunca se ha construido.

> La plantilla se entrega **a propósito** en Estado 0: `requirements.txt` es la **única** fuente de dependencias. `pyproject.toml` y `uv.lock` **no faltan** — se generan al construir el contenedor (abajo). No hay que crearlos a mano ni "arreglar" su ausencia.

**Qué pasa al hacer Reopen in Container (primera vez):**
- El `postCreateCommand` detecta que solo hay `requirements.txt` y ejecuta:
  `uv init --no-package --no-workspace .` → elimina el `main.py` por defecto → `uv add -r requirements.txt`.
- **Resultado:** se generan `pyproject.toml` y `uv.lock` por primera vez. **Esto es un cambio que hay que commitear** (consolida el entorno reproducible).

**Qué hacemos juntos en esta primera sesión:**
1. Definir el **objetivo concreto** del proyecto (qué ingiere, qué produce).
2. **Conversación seria del stack.** Python-first es el punto de partida, pero **no se asume**: se resuelven las
   *preguntas de arranque* (tipo de interfaz y framework; ¿solo Python u otros lenguajes en algún borde?; DB/ORM;
   analítica; API; despliegue). En apps SDD las preguntas viven en `spec/constitution/03_stack.md` y se registran ahí;
   en plantillas de datos, el eje SQL/no-SQL (§2). *(Opcional: para conducir la interrogación puedes usar una skill
   de este tipo — p. ej. `grill-me` en Helix.)*
3. Poblar el `.env` con las credenciales reales (nunca se versiona; ya está en `.gitignore`).
4. Confirmar la convención de carpetas (§6): `sandbox/`, `tests/`, `output/` con su `README.md`, y `sandbox/*` ignorado salvo su README.
5. (Opcional, según el agente) Sentar la **memoria del proyecto** (contexto persistente entre sesiones) — p. ej. en **[Helix](https://github.com/ftuga/helix_asisten)**, con `/helix-analiza`.
6. Commitear `pyproject.toml` + `uv.lock` recién generados.

### 🔵 Estado N — Sesiones siguientes (ya funcionando)

**Cómo se reconoce:** ya existen `pyproject.toml` **y** `uv.lock`. El `.env`, `tests/`, `sandbox/` y la memoria del agente ya están.

**Qué pasa al hacer Reopen in Container:**
- El `postCreateCommand` ve el `uv.lock` y ejecuta `uv sync --locked` → entorno **idéntico y reproducible**, rápido, sin regenerar nada.

**Qué hacemos juntos:**
1. Arrancas el contenedor; yo lo detecto con `docker ps`.
2. Retomamos contexto (el agente carga la memoria del proyecto; si hay commits nuevos, lo advierto — §3, paso 4).
3. Trabajo normal: edito en el host → verifico con `docker exec` en `sandbox/` + `tests/` → solo lo comprobado pasa a `output/` o al código real.

> **Regla:** si algún día `uv.lock` cambia (agregamos/actualizamos dependencias), ese cambio **se commitea**. El lockfile es la garantía de reproducibilidad.

---

## 10. Recordatorios firmes (para los dos)

- **No me instales dentro del contenedor.** Vivo en el host; ejecuto vía `docker exec`. Peso en la imagen: cero.
- **Ejecución = contenedor. Criterio = host.** Yo no doy algo por bueno "porque se ve bien"; lo corro y leo la salida real.
- **`output/` es sagrado.** Nada entra ahí sin pasar por `sandbox/` (tanteo) y el gate (`tests/` para lo computacional, tu revisión para lo escrito/visual).
- **Tests siempre.** Un bug sin test que lo reproduzca no está cerrado.
- **Reproducibilidad siempre.** `uv.lock` se versiona; el `.env` nunca.
- **El `.env` nunca se versiona.** Credenciales solo en local; `.env.example` con placeholders.
- **Una sola fuente de verdad para las decisiones** (`docs/`); mi memoria apunta a ella.
- **Al terminar, botas contenedor + imagen.** El host (WSL + tu agente) queda intacto y limpio para la próxima.
- Siempre trabajamos desde **WSL**.

---

## 11. Estándar de conexión a SQL desde Python (mío)

> _Esto es mi **estándar de código** para conectar a SQL, independiente del contenedor. Complementa la dinámica de trabajo de las secciones 1–10. **Solo aplica si el proyecto es SQL** (Eje 2, §2)._

Mi forma de trabajar SQL desde Python es siempre la misma, **solo con SQLAlchemy** (sin ORM, sin drivers manuales por fuera):

1. **Credenciales en `.env`** → las lee `src/config/config.py` con `python-dotenv` (`load_dotenv()` + `os.getenv`), expuestas como constantes de módulo.
2. **Fábrica de engine en `src/db/connection.py`** → una función `get_engine…()` arma la URL con `sqlalchemy.engine.URL.create()` y devuelve `create_engine(url)`. Un motor por origen de datos. El código de conexión es **código**, por eso vive en `src/`, **no** en `data/`.
3. **Las consultas viven en archivos `.sql`** (en `data/sql/`), nunca embebidas en el código Python. `data/sql/` contiene **solo `.sql`** (dato), nunca módulos Python.
4. **Ejecución con pandas** → `pd.read_sql(query, engine)`.

### Credenciales separadas por motor

**Cada motor de base de datos tiene su propio grupo de variables en el `.env`, con un prefijo que lo nombra directamente** — nunca genéricas ni compartidas entre motores, y **nunca un prefijo genérico tipo `DB_`**. Así dos motores conviven sin pisarse y cada engine lee solo lo suyo:

| Motor | Prefijo | Variables |
|---|---|---|
| PostgreSQL | `PG_` | `PG_HOST`, `PG_PORT`, `PG_NAME`, `PG_USER`, `PG_PASSWORD` |
| SQL Server | `MSSQL_` | `MSSQL_HOST`, `MSSQL_PORT`, `MSSQL_NAME`, `MSSQL_USER`, `MSSQL_PASSWORD` |
| Túnel SSH | `SSH_` | `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_PASSWORD` — grupo aparte, solo cuando el motor va por túnel |

Y en `src/db/connection.py`, **un engine por motor con nombre propio**: `get_engine_postgres()`, `get_engine_mssql()`, etc. Nunca un `get_engine()` genérico que mezcle orígenes.

> **`NAME` y `PORT` son opcionales.** `PORT` vacío → `URL.create()` lo omite. Con `NAME` vacío (típico contra un
> **DataWarehouse** sin fijar una base) hay un matiz en `mssql+pyodbc`: pasar `database=None` cae en la heurística
> DSN del conector, descarta el `DRIVER=` y falla con **`IM002`**. Por eso, en SQL Server, pasa **`database=config.MSSQL_NAME or ""`**
> (la cadena vacía fuerza el modo host y `Database=` vacío = base por defecto del login). En PostgreSQL/Oracle no aplica: `None` se omite limpio.

### Dialecto y driver por motor

| Motor | Dialecto SQLAlchemy | Paquete (`uv add` / `requirements.txt`) | System deps (Dockerfile) |
|---|---|---|---|
| **SQL Server** | `mssql+pyodbc` | `pyodbc` | `unixodbc-dev` + `msodbcsql17` (repo Microsoft, vía keyring en Debian 12) |
| **PostgreSQL** | `postgresql+psycopg` | `psycopg[binary]` | ninguna con `[binary]`; `libpq-dev` solo si compila de fuente |
| **Oracle** | `oracle+oracledb` | `oracledb` | ninguna en modo *thin*; Oracle Instant Client (+`libaio1`) en modo *thick* |

> La plantilla SQL trae **SQL Server activo** como ejemplo; PostgreSQL y Oracle van **comentados** en `src/db/connection.py`, `requirements.txt`, `.env.example` y el `Dockerfile`. Para cambiar de motor: descomentar su función, su driver, su grupo de variables y (si aplica) sus system deps.

### Dos casos de conexión

**Caso A — Conexión directa.** El motor es alcanzable directamente (SQL Server en la red, o un Postgres sin túnel). El engine se arma con **`URL.create()`**, que **escapa solo** usuario, contraseña y parámetros — sin `quote_plus` manual ni `odbc_connect`, y omitiendo `PORT` cuando es `None`.
```python
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# SQL Server (pyodbc). PORT opcional: si es None, URL.create lo omite.
url = URL.create(
    "mssql+pyodbc",
    username=config.MSSQL_USER,
    password=config.MSSQL_PASSWORD,   # el escaping lo hace URL.create
    host=config.MSSQL_HOST,
    port=config.MSSQL_PORT,           # None si no se define
    # database="" a propósito (NO None): con host + database=None, el conector cae en la
    # heurística DSN de pyodbc, descarta el DRIVER y falla con IM002. "" fuerza modo host
    # y `Database=` vacío = base por defecto del login.
    database=config.MSSQL_NAME or "",
    query={"driver": config.MSSQL_DRIVER},   # "ODBC Driver 17 for SQL Server"
)
engine = create_engine(url)

# Postgres directo: mismo patrón con "postgresql+psycopg" y sin el query del driver.
```

**Caso B — Conexión vía túnel SSH.** El motor solo es alcanzable a través de un servidor puente. Se agrega el grupo `SSH_*` y la fábrica **abre el túnel** antes de crear el engine, que apunta a `127.0.0.1:<puerto_local>`. Devuelve **`(engine, tunnel)`**: el túnel debe seguir abierto mientras uses el engine y se cierra con `tunnel.stop()` al final.
```python
engine, tunnel = get_engine_postgres()   # abre túnel SSH + crea el engine
query = open("../data/sql/mi_consulta.sql", encoding="utf-8").read()
df = pd.read_sql(query, engine)
tunnel.stop()   # cerrar el túnel al terminar
```

**Dependencia y build del Caso B (frágil — deuda conocida):**
- Requiere `sshtunnel` (que arrastra `paramiko`, `cryptography`, `cffi`). Si el build falla por falta de wheels (p. ej. Python muy nuevo como 3.14), agregar al Dockerfile: `libffi-dev`, `libssl-dev`, y si `cryptography` compila desde fuente, `rustc`/`cargo`.
- **Shim de compatibilidad obligatorio:** `sshtunnel 0.4.0` referencia `paramiko.DSSKey`, eliminado en `paramiko` 3.x → `AttributeError`. Antes de crear el túnel, en `src/db/connection.py`:
  ```python
  import paramiko
  if not hasattr(paramiko, "DSSKey"):
      paramiko.DSSKey = paramiko.RSAKey   # inocuo: auth por contraseña, no DSA
  ```
  y pasar `allow_agent=False` al `SSHTunnelForwarder` (auth solo-password, determinista).
- ⚠️ **DEUDA CONOCIDA:** `sshtunnel` está **sin mantenimiento activo** y por eso arrastra estos parches. Es una dependencia **candidata a reemplazar** por una alternativa mantenida. **Pendiente de resolver** — cuando se decida abordarlo, se investiga el reemplazo y se actualiza esta sección.

### Dos maneras de llamar el `.sql`

**Modo A — SQL crudo (sin tocar):** leo el archivo y lo ejecuto tal cual, sin modificar nada.
```python
query = open("../data/sql/mi_consulta.sql", encoding="utf-8").read()
df = pd.read_sql(query, engine)
```

**Modo B — SQL parametrizado:** el `.sql` trae un marcador fijo que **reemplazo** por una **variable** o una **lista** definida en Python, antes de ejecutar.
```python
# Con una variable escalar (p. ej. filtrar por periodo), vía .format():
query = (
    open("../data/sql/mi_consulta.sql", encoding="utf-8")
    .read()
    .format(ano_reporte=2026, mes_reporte=8)
)

# Con una lista (p. ej. inyectar un IN (...)), vía .replace():
ids = [101, 102, 103]
query = (
    open("../data/sql/mi_consulta.sql", encoding="utf-8")
    .read()
    .replace("{lista_ids}", ",".join(map(str, ids)))
)

df = pd.read_sql(query, engine)
```

### Catálogo de consultas: un `.sql` por propósito

Toda consulta vive en `data/sql/` como archivo `.sql` independiente, **nunca embebida en Python** (ni f-strings, ni triple-quoted). El SQL es *dato*, no código incrustado: Python solo lo lee, lo ejecuta con `pd.read_sql` y mueve el resultado.

1. **Fuente única.** Toda consulta en `data/sql/*.sql`. Cero SQL embebido en `.py`.
2. **Un archivo, un propósito.** Cada `.sql` resuelve **una** intención completa. Dos intenciones → dos archivos; nada de un mega-`.sql` con todo.
3. **Nombre autodescriptivo.** El nombre dice **qué hace** (acción + objeto), no el nombre de una tabla ni un correlativo opaco. `snake_case`, minúsculas, `.sql` (ej: `listar_vistas_y_esquemas.sql`). Listar `data/sql/` revela el repertorio completo **sin abrir un solo archivo**.
4. **Parámetros por marcador.** Si la consulta varía, marcador fijo (`{ano}`, `{lista_ids}`) reemplazado desde Python (Modo B), nunca concatenación ad-hoc.
5. **UTF-8 y un statement por archivo** (salvo que el propósito mismo sea un lote).
6. **(Opcional, al crecer)** agrupar por fase en subcarpetas: `data/sql/descubrimiento/`, `data/sql/extraccion/`.
7. **Consistencia de idioma en los nombres:** elegir un idioma para el catálogo y sostenerlo (no mezclar `listar_vistas` con `extract_views`).

**Por qué:** trazabilidad y revisión por *diff*, reutilización, separación limpia criterio↔ejecución, y —clave en migraciones— **el `.sql` ES el entregable repunteable**: se cambia la fuente dentro del archivo sin tocar Python.

---

## 12. Tratamiento de las tablas materializadas — bitácora de ejecución de jobs (estándar pendiente)

> _Solo aplica en proyectos SQL con tablas materializadas pobladas por jobs programados._

Las **tablas materializadas** no se resuelven al consultarse como las vistas: las puebla un **job programado** (p. ej. un SQL Agent job) que ejecuta su procedimiento de carga (TRUNCATE + INSERT dentro de `TRY/TRANSACTION`). Para operar y monitorear esas cargas adoptamos un estándar de **Ingeniería de Datos**:

- **Bitácora en tabla administrativa (capa Bronze/Silver):** se mantiene una tabla donde se escribe, por cada corrida de job, la **configuración del job**, la **fecha de ejecución**, la **hora de inicio** y la **hora de finalización**. Estándar **para todos los proyectos**, a implementar **cuando terminen todas las migraciones**.
- **Cada procedimiento de carga registra su corrida:** una fila al **iniciar** (estado `EN_CURSO`) y otra al **finalizar** (hora fin, filas afectadas, estado `EXITO`/`FALLO`), idealmente en `TRY/CATCH` para capturar también los fallos.
- **Por qué en la BD de negocio y no en el historial nativo del scheduler:** el historial nativo del Agent (`msdb`) suele exigir roles elevados (`SQLAgentReaderRole`/sysadmin) y **está restringido** para un login analítico (error 229 *EXECUTE denied*). Una bitácora en la propia capa de negocio la deja **legible por el login analítico**, sin depender del DBA.

> Definición formal y esquema/nombre a fijar en la documentación del proyecto (`docs/`), enlazando con la doctrina de jobs y de nombres de procedimientos.

---

## 13. Acelerador opcional: mapa de código para agentes (`graft`)

> _**OPCIONAL** — recomendación de optimización del trabajo con agentes de IA. **NO** forma parte de la plantilla:
> no viene preinstalado, no es dependencia del proyecto, y cada quien decide si lo usa. Es herramienta **del desarrollador**._

**El problema:** cada sesión, el agente arranca ciego y **re-explora** el repo antes de tocar nada — reads exploratorios que cuestan tiempo y tokens (justo lo que la doctrina de *brief antes de spawn* busca evitar).

**Qué hace [`graft`](https://github.com/trailhq/graft):** construye **una vez** un grafo del código y lo escribe como **markdown enlazado** (un nodo por sistema/API/concepto). El agente **lee ese mapa** en vez de redescubrir. Es documentación **descriptiva auto-generada y siempre fresca** → complementa tu `docs/` (§7); **no** sustituye tus especificaciones prescriptivas ni este contrato.

### Dónde corre — en el HOST, no en el contenedor
`graft` es una herramienta de **archivos** (parsea con tree-sitter), no de runtime: no necesita Python, ni la DB, ni el contenedor. Como el workspace está **bind-mounted** en el contenedor (los ficheros son los mismos bytes en host y contenedor), el `graft/` que genera es visible **desde ambos lados a la vez**. Córrelo en **WSL, contra la raíz del repo** — sin `docker exec`.

### Instalación — elige una (el dev decide)
```bash
# A) Temporal, sin instalación global (respeta la doctrina npm: nada global persistente):
DO_NOT_TRACK=1 npx @nanonets/graft@<versión-fijada> init

# B) Global, si lo usas a diario:
npm install -g @nanonets/graft@<versión-fijada>
DO_NOT_TRACK=1 graft init
```
> Fija la versión (`@x.y.z`), revisa su *release age* y verifica el publisher (`@nanonets`) antes de instalar.
> Instálalo **fuera** del manifiesto del proyecto (es tooling del dev, no dependencia de la app).

### Endurecimiento (seguridad)
- **Default seguro = Pass 1** (estructural, tree-sitter): **sin LLM, sin API key, sin egress de código.** Cubre la mayor parte del valor.
- **Pass 2** (resúmenes conceptuales) **envía código a un LLM** → úsalo **solo con decisión explícita**: modelo **local** preferido; con proveedor cloud, **solo con consentimiento del cliente** (en proyectos con confidencialidad, el código sale del entorno).
- **Telemetría off:** `DO_NOT_TRACK=1` o `graft telemetry disable`.

### Versionado del grafo
Por defecto `graft` ignora `graft/`. Recomiendo lo contrario para conocimiento de equipo: **versiona los nodos** `graft/*.md` (viajan en el clone → el agente los lee al instante) y deja en `.gitignore` **solo el caché** `graft/.graph/`.

---

> **Nota para el agente que lea este archivo:** si estoy en un proyecto con este README, mi runtime de ejecución es el Dev Container vía `docker exec`, no el host. Al arrancar sigo el ritual de §3: **infiero-y-confirmo el tipo de trabajo** (Eje 1) y detecto si es SQL (Eje 2); cargo la memoria del proyecto y aviso si está desactualizada; confirmo el puente con `docker ps` antes de ejecutar (si el contenedor no está arriba, se lo pido al usuario en vez de correr en el host); distingo Estado 0 (solo `requirements.txt`) de Estado N (`pyproject.toml` + `uv.lock`).
>
> **Instrucción de persistencia:** la primera vez que encuentre este README en un proyecto, guardo esta dinámica en la **memoria del agente de ESE proyecto** (scope de proyecto, no global) y la cargo al inicio de cada sesión, para no depender de releer este archivo cada vez. La **fuente de verdad de las decisiones** vive en `docs/` (§7); mi memoria **apunta a ella**, no guarda copia divergente. Si la memoria ya existe, la respeto y la actualizo solo si la dinámica cambia.
