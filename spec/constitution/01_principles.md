<!--
====================================================================
 01 — PRINCIPIOS  ·  Nivel 1 (Constitución)
--------------------------------------------------------------------
 CONTENIDO FIJO de ClearNote_Dev: estos principios rigen para TODO
 proyecto nacido de esta plantilla. Se tocan poco y con intención;
 cambiarlos es cambiar la doctrina, no configurar un proyecto.
 Si un principio choca con un proyecto puntual, se documenta la
 excepción en un ADR (docs/decisions/), no se borra el principio.
====================================================================
-->

# 01 — Principios (lo no-negociable)

Estos son los principios que **no se negocian** por conveniencia de una entrega. Cuando haya duda
sobre cómo actuar, se resuelve a favor de estos principios. El orden es de prioridad: si dos
principios chocan, gana el de arriba.

## 1. Spec-first (el spec manda)

Nada se construye sin que antes exista lo que **debe ser verdad**. El flujo es
`Constitución → Spec → Plan → Tareas → Implementación`, y la jerarquía de verdad es
`Constitución > Spec de feature > Plan/Contratos > Tareas > Código`.

- **`spec/` es prescriptivo** (lo que debe ser verdad); **`docs/` es descriptivo** (cómo y por qué quedó así).
  Fallan distinto: si el código ≠ spec, **el código está mal**; si los docs ≠ realidad, **los docs están mal**.
- No se abre código de una feature sin su `spec.md` (qué + criterios de aceptación).

## 2. Test-first (el gate)

Nada se da por bueno sin pasar por `tests/`. La verificación es la frontera entre "lo intenté" y "funciona".

- Todo **bug** corregido lleva **primero** un test que lo reproduce, y luego el fix.
- Cobertura mínima por unidad: **happy path + edge cases + estado vacío**.
- Los tests de **aceptación** (`tests/acceptance/`) validan la feature contra su `spec.md`.

## 3. Reproducibilidad (nada "funciona en mi máquina")

El entorno es parte del entregable. Cualquiera —humano o agente— debe poder levantar y reproducir.

- Se trabaja **dentro del contenedor** (Docker + Dev Containers); `uv.lock` **se versiona**.
- Los cambios de esquema se materializan con **migraciones Alembic**, nunca a mano sobre la DB.
- Determinismo: sin datos aleatorios ni rutas absolutas en el código.

## 4. Seguridad por defecto

La opción segura es la que viene de fábrica; relajarla es una decisión explícita y trazable.

- **Cero credenciales en el repo.** Secretos por archivo (`*_FILE` / Docker secrets); `.env` en `.gitignore`;
  placeholders en `.env.example`.
- **Least-privilege** en la base de datos: roles acotados, `REVOKE public`, RLS activo (ver `docs/architecture/gobernanza-db.md`).
- ⭐ **Regla de dos aprobadores:** cualquier cambio que **desactive o altere RLS o auditoría** exige
  **dos revisores humanos** (branch protection + CODEOWNERS). No hay atajo de una sola persona.
- Las **acciones destructivas** se confirman antes de ejecutarse. Endpoints de test/debug no llegan a producción.

## 5. Gobernanza de datos explícita

Los datos no se guardan "y ya": cada tabla declara su naturaleza al nacer.

- Al crear una tabla de estado/referencia se decide y documenta: **¿bitemporal?**, **¿PII?**
  (tratamiento omit/mask/hash), **¿tenant-scoped (RLS)?**.
- La **identidad de los actores** se modela con surrogate (`person_id`) + documentos versionados, para permitir anonimización.
- La **auditoría** cubre todas las capas con granularidad adecuada (fila / job / bitemporal de gobernanza).

## 6. Documentación como parte del trabajo (no un extra)

Un cambio no está terminado hasta que es entendible por tu yo futuro y por cualquier agente en una sesión nueva.

- El **README de cada carpeta** explica por qué existe; se mantiene vivo.
- El **diccionario de datos** (`docs/data-dictionary/`) se actualiza cuando cambia el esquema.
- Las **decisiones no triviales** se registran como ADR (`docs/decisions/`).

## 7. Simplicidad — no sobrediseñar

La complejidad se paga siempre; se agrega solo cuando el problema la exige, no "por si acaso".

- Los opcionales del stack (frameworks, orquestadores) se **activan cuando se necesitan**, no antes.
- **Un** framework por rol (una UI, un ORM). No mezclar motores que compiten (ver `03_stack`).
- Preferir lo explícito y legible sobre lo ingenioso.
- **Anti-atasco:** si la complejidad crece sin resolver (2+ intentos fallidos), **parar y replantear** desde
  otra perspectiva, o pedir conversación. Amontonar complejidad no es progreso.

## 8. Modularidad

Cada pieza hace una cosa y se puede cambiar sin arrastrar a las demás. La estructura de `src/` **no es
decorativa: son fronteras.**

- **Respeta las capas de `src/`:** backend (`api` → `use_cases` → `services`), frontend
  (`components`/`views`/`state`), database (`models`/`repositories`). No se cruzan.
- **Depende de interfaces, no de implementaciones:** cambiar el framework de UI o el motor de datos debe
  tocar **una zona, no todo**. Ese desacople es lo que hace viable el Python-first *abierto* (ver `03_stack`).
- **Acopla por contrato** (esquemas, `services`), nunca alcanzando "hacia adentro" de otro módulo.

---

> Estos principios son el "cómo" permanente. El "qué" (00_purpose), el "hasta dónde" (02_scope)
> y el "con qué" (03_stack) se leen a su luz.
