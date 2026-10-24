# 🏛️ ClearNote_Dev — Plantilla para desarrollo de aplicaciones (Spec-Driven)

Plantilla **insignia** para construir **aplicaciones full-stack en Python** de forma reproducible y portable
(**VS Code + Dev Containers + Docker + `uv`**), siguiendo **Spec-Driven Development (SDD)**: el diseño y la
documentación guían el código, no al revés.

> **¿Cómo se colabora con un agente de IA en este repo?** El agente entra por **`AGENTS.md`** (que auto-lee) y
> desde ahí llega al contrato **`README_AGENTS.md`** (agnóstico de herramienta). Este archivo es *qué es el
> proyecto y cómo está organizado*.

---

## ✅ Prerequisitos (en el host / WSL)

Todo el entorno de dev vive en contenedores, así que en tu máquina solo necesitas **Docker + Docker Compose v2**
y **VS Code con Dev Containers**. *(Nada de Python/uv en el host — eso va dentro del contenedor.)*

| Requisito | Verifica | Si falta |
|---|---|---|
| **WSL 2** (Ubuntu) | `wsl -l -v` (en PowerShell) | `wsl --install -d Ubuntu` |
| **Docker Engine** (en WSL) | `docker --version` | ↓ *Docker en WSL* |
| **Docker Compose v2** | `docker compose version` → `v2.x+` | ↓ *Compose v2* |
| **VS Code + Dev Containers** | extensión instalada | instala `ms-vscode-remote.remote-containers` |
| **git** | `git --version` | `sudo apt-get install -y git` |

> Alternativa: **Docker Desktop (Windows)** con integración WSL ya trae Docker + Compose v2; en ese caso salta los dos bloques de abajo.

### Docker en WSL (Ubuntu, sin Docker Desktop)
```bash
sudo apt-get update && sudo apt-get install -y docker.io
sudo usermod -aG docker "$USER"   # usar docker sin sudo (reabre la terminal después)
sudo service docker start          # arranca el daemon (WSL no trae systemd por defecto)
docker run --rm hello-world        # verificación
```

### Docker Compose v2 (plugin) — user-space, sin sudo
```bash
mkdir -p ~/.docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
docker compose version             # debe responder v2.x+
```
> Alternativa con apt: `sudo apt-get install -y docker-compose-v2`.

---

## 🚀 Puesta en marcha (Quickstart)

> Requiere los **Prerequisitos** de arriba (Docker + Compose v2 + Dev Containers).

### 1. Clona la plantilla

**Por HTTPS:**
```bash
git clone https://github.com/ClearNote97/ClearNote_Dev.git
cd ClearNote_Dev
```

**Por SSH:**
```bash
git clone git@github.com:ClearNote97/ClearNote_Dev.git
cd ClearNote_Dev
```

### 2. Elimina el historial de la plantilla

Esto es una **plantilla, no un proyecto en sí**: soltar el historial git que trae es **obligatorio**.
```bash
rm -rf .git
```

### 3. Renombra la carpeta

Ponle el nombre de tu proyecto (reemplaza `mi-proyecto`, en minúsculas-con-guiones):
```bash
cd ..
mv ClearNote_Dev mi-proyecto
cd mi-proyecto
```
> 💡 **Ese nombre es tu `APP_NAME`.** Al hacer _Reopen in Container_, el `initializeCommand` lo toma automáticamente
> del nombre de la carpeta y lo escribe en `.env` — así el mount (`${APP_NAME}`) y el workspace nunca divergen.

### 4. Inicializa tu propio repositorio *(opcional)*
```bash
git init
git add .
git commit -m "Proyecto inicial basado en la plantilla ClearNote_Dev"
```
Y, si quieres conectarlo a un remoto:
```bash
git remote add origin https://github.com/tu_usuario/tu_repositorio.git
git push -u origin main
```

### 5. Prepara entorno y secreto *(una sola vez, en el host)*
```bash
cp -n .env.example .env
[ -s secrets/db_password.txt ] || openssl rand -base64 24 > secrets/db_password.txt
```

### 6. Arranca

Ambos caminos corren `init.sh` (que **autodetecta** el contexto): build/DB → gobernanza → deps `uv` → migraciones.

- **Dev (recomendado) — _Reopen in Container_:** el `postCreateCommand` ejecuta **`init.sh` solo**. La DB ya está
  arriba (por `depends_on`), así que aplica gobernanza + deps + migraciones. **No tienes que pegar nada.**
- **Desde el host — un comando:**
  ```bash
  ./init.sh
  ```

Al terminar verás **`✅ ... listo`**.

**Antes de un proyecto real, ajusta en `.env`** (secciones `[ PROYECTO NUEVO ]`): `APP_NAME`, `DB_NAME`, `DB_USER`.
La contraseña vive en `secrets/db_password.txt` (nunca se versiona) — reemplázala por la tuya.

> **`APP_ENV` es el interruptor maestro** (`development` por defecto). En **dev** (devcontainer) `init.sh` corre solo. En
> **prod**, el despliegue lo hace tu orquestador y la gobernanza se aplica con
> `APP_ENV=prod ./src/database/admin/run-admin.sh` (el secreto se lee de `/run/secrets/`). Ver `docs/architecture/gobernanza-db.md`.

> **¿Proyecto SIN base de datos?** (p. ej. una CLI/tool). Un **único interruptor** en `.env`: deja
> **`COMPOSE_PROFILES=`** vacío. El servicio `db` no se crea (compose no da *"no such service"*), `app-dev`
> arranca solo, e `init.sh` **detecta que no hay DB** y omite gobernanza + migraciones. No hay que comentar nada
> en `docker-compose.yml` ni en `devcontainer.json`. Para reactivarla: `COMPOSE_PROFILES=db`.

> **Estado 0 → N:** en un proyecto recién nacido, `init.sh` **genera** `pyproject.toml` + `uv.lock` (consolidan el
> entorno reproducible: **commitéalos**). Detalle en el contrato `README_AGENTS.md` §9.

---

## 🧭 Filosofía: Spec-Driven Development

**Invariante raíz:** el *spec* es la **fuente de verdad**; el código es su **implementación**. Nada se construye
sin spec; nada está "hecho" hasta que cumple su spec y pasa sus criterios de aceptación. El flujo es
**unidireccional hacia abajo** — si algo cambia, entra por el spec.

**Los 5 niveles** (cada uno con su *gate* de aprobación antes de bajar al siguiente):

| # | Nivel | Responde | Vive en |
|---|---|---|---|
| 1 | **Constitución** | ¿quiénes somos, qué no se negocia? | `spec/constitution/` |
| 2 | **Especificación** | el **QUÉ** y el **PORQUÉ** (criterios de aceptación) | `spec/features/` |
| 3 | **Plan** | el **CÓMO** (arquitectura, modelo de datos, contratos) | `spec/` |
| 4 | **Tareas** | descomposición accionable y testeable | `spec/features/NNN/` |
| 5 | **Implementación** | construir + **verificar contra el spec** | `src/` + `tests/` |

**`spec/` vs `docs/`** — la distinción clave:

- **`spec/` = lo que DEBE ser verdad** (prescriptivo, precede al código; el **código** se verifica contra él).
- **`docs/` = cómo y por qué es así** (descriptivo, narra lo construido; los **docs** se corrigen contra la realidad).
- Si `spec ≠ código` → el código está mal. Si `docs ≠ realidad` → los docs están mal.

---

## 📂 Estructura del proyecto

```
ClearNote_Dev/
├── spec/                        # 📜 lo que DEBE ser verdad (prescriptivo)
│   ├── constitution/            #   Nivel 1 — la capa que gobierna todo
│   │   ├── 00_purpose.md        #     por qué existe (misión + problema + para quién)
│   │   ├── 01_principles.md     #     lo NO-negociable (spec-first, test-first, repro, seguridad, modularidad…)
│   │   ├── 02_scope.md          #     qué está dentro y qué NO
│   │   └── 03_stack.md          #     fundación técnica y restricciones
│   ├── roadmap.md               #   hacia dónde va (planificación viva)
│   ├── contracts/               #   contratos TRANSVERSALES del sistema (OpenAPI, esquemas compartidos)
│   └── features/                #   Niveles 2-4 — una carpeta por feature
│       └── NNN_nombre/
│           ├── spec.md          #     Nivel 2 — el QUÉ + criterios de aceptación
│           ├── plan.md          #     Nivel 3 — el CÓMO
│           └── tasks.md         #     Nivel 4 — descomposición
│
├── docs/                        # 📖 cómo y por qué es así (descriptivo)
│   ├── architecture/            #   el sistema ensamblado, narrado (incluye doc del esquema DB)
│   ├── decisions/               #   ADRs (un archivo por decisión) + maestro consolidado a futuro
│   ├── business/                #   dominio: glosario, reglas de negocio explicadas
│   ├── audit/                   #   revisiones de seguridad/dependencias, cumplimiento
│   └── data-dictionary/         #   índice maestro + 1 archivo por tabla (subcarpeta por schema)
│
├── src/                         # ⚙️ Nivel 5 — implementación (cumple el spec)
│   ├── backend/                 #   api (entrada) · schemas (DTOs) · use_cases (operación de negocio) · services (reutilizable)
│   ├── database/                #   admin (SQL gobernanza) · app/{models,repositories} · analytics · migrations · connection · session
│   ├── frontend/                #   views · components · state · layout · services · visuals
│   ├── analytics/               #   ml · statistics · tracking
│   └── utils/                   #   helpers genéricos y portables
│
├── tests/                       # ✅ verifica el spec
│   ├── backend/ … database/ … frontend/ … analytics/ … utils/   (unit — espejo de src/)
│   └── acceptance/              #   "prueba de fuego" por feature (traza a spec/features/NNN)
│
├── data/                        # 📦 datos (contenido no versionado): seeds · storage/{raw,processed,exports,mlmodels} · tests
├── notebooks/                   # 🔬 exploración interactiva (se promueve a src/ o tests/)
├── scripts/                     # 🔧 operación del proyecto (incluye nginx/)
├── infra/                       # 🏗️ infraestructura: db/ (imagen Postgres 18 + pgaudit/pg_cron)
├── secrets/                     # 🔐 secretos de desarrollo (contenido en .gitignore)
│
├── spec_agents/                 # 🤖 roster de agentes (spec agnóstico) → se materializa a .claude/ o .opencode
├── init.sh                      # 🚀 un comando: build+up+wait → gobernanza → deps → migraciones
├── docker-compose.yml           # db (imagen propia) + app-dev + servicios opcionales comentados
├── AGENTS.md · CLAUDE.md        # entrada para agentes de IA → apuntan al contrato
└── README_AGENTS.md             # contrato de colaboración (agnóstico de herramienta)
```

### La lógica en una frase

**Constitución** gobierna → **Spec** define el *qué* → **Plan** el *cómo* → **Tareas** descomponen →
**`src/`** implementa → **`tests/`** verifica contra los criterios → **`docs/`** explica lo construido.

### Un patrón que se repite: *granular + maestro*

Todo lo que crece en cantidad usa la misma forma: **muchos archivos pequeños y enfocados + un maestro que los
indexa**. Aplica a las **decisiones** (ADRs + maestro) y a los **diccionarios de datos** (uno por tabla + índice maestro).

### Arquitectura limpia (el viaje de una petición)

```
Frontend → api/ → schemas/ → use_cases/ → repositories/ → models/ + DB
            (entrada) (valida)  (orquesta)   (persiste)     (tablas)
                                    ↑
                               services/  (lógica reutilizable propia de la app)
```

Las **reglas de negocio** se aplican en 3 capas: el **modelo** (reglas de forma de un registro) → los
**`use_cases`/`services`** (reglas reales, de proceso) → la **DB** (`CHECK`/RLS/triggers, como red de seguridad).

---

## 🤖 Roster de agentes de IA (`spec_agents/`)

Además del contrato de colaboración (`README_AGENTS.md`), la plantilla declara **qué agentes especialistas
necesita**, de forma **agnóstica de herramienta**, en [`spec_agents/`](./spec_agents/) — es *SDD aplicado a los
agentes*. El agente en sesión (Claude Code / Helix **o** OpenCode) **materializa** ese spec a su formato nativo
(`.claude/agents/*.md` o `.opencode/agent/*.yaml`), reutilizando lo que el harness ya traiga.

Tres familias, alineadas con los tipos de trabajo del contrato (§2):

- **Núcleo (app):** `lead-architect` (coordina y decide el roster activo), `spec-author`, `backend-builder`,
  `frontend-builder`, `migration-writer`, `test-writer`, `code-reviewer`, `security-auditor`, `db-governance-reviewer`, `doc-writer`.
- **Datos / analítica (opt-in):** pipeline `analytics-lead` → `data-ingestor` → `data-cleaner` → `sql-analyst` →
  `stats-analyst` / `ml-engineer` → `viz-specialist` → `insight-reporter`.
- **Investigación (opt-in):** `literature-reviewer` + `academic-writer`.

Se activan **bajo demanda** (lo decide `lead-architect`), nunca todos por defecto, y cada uno hereda guardrails
universales (anti-sobrediseño, no-asumir, cero-secretos). Detalle: [`spec_agents/README.md`](./spec_agents/README.md).

---

## ⚖️ Licencia

Distribuido bajo licencia [MIT](https://opensource.org/license/MIT).

## ✍️ Autor

**MSc. Nicolás Enrique Valencia Santiago**

## 🙏 Agradecimientos

Plantilla enriquecida con la asistencia de [Helix — agente de IA](https://github.com/ftuga/helix_asisten) de [ftuga](https://github.com/ftuga).
