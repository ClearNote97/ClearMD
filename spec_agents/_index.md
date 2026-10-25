# Roster de agentes — índice maestro (ClearMD)

Roster que este proyecto necesita. El *cómo* del formato y la materialización está en [`README.md`](./README.md).
Recortado desde la plantilla: se quitaron las familias de datos/analítica, investigación y base de datos,
que ClearMD no usa (ADR-0009). Los roles que quedan están adaptados a ClearMD (ADR-0014).

## Coordinación / coherencia

| Agente | Propósito | `model_hint` | Herramientas |
|---|---|---|---|
| [`lead-architect`](./lead-architect.yaml) | Custodia la coherencia del conjunto: nada se contradice y todo traza al spec. Compuerta de cierre. | `frontier` | read, grep, glob |

## Especificar · construir · verificar (ciclo SDD)

| Agente | Propósito | `model_hint` | Herramientas |
|---|---|---|---|
| [`spec-author`](./spec-author.yaml) | Redactar/refinar `spec.md` · `plan.md` · `tasks.md` de una feature. | `frontier` | read, grep, glob, write, edit |
| [`backend-builder`](./backend-builder.yaml) | Implementar el backend (casos de uso, servicios, worker) y la CLI desde el plan. | `balanced` | read, grep, glob, edit, write, bash |
| [`frontend-builder`](./frontend-builder.yaml) | Construir las GUIs (ttkbootstrap, PySide6, flet) sobre el presenter. | `balanced` | read, grep, glob, edit, write |
| [`test-writer`](./test-writer.yaml) | Tests unit + acceptance (test-first), contra el spec. | `balanced` | read, grep, glob, write, edit, bash |

## Revisión / calidad / seguridad

| Agente | Propósito | `model_hint` | Herramientas |
|---|---|---|---|
| [`code-reviewer`](./code-reviewer.yaml) | Calidad, bugs, performance — gate pre-cierre. | `balanced` | read, grep, glob |
| [`security-auditor`](./security-auditor.yaml) | Entradas no confiables (documentos, rutas, archivos comprimidos), el worker, dependencias, red. | `frontier` | read, grep, glob |

## Documentación

| Agente | Propósito | `model_hint` | Herramientas |
|---|---|---|---|
| [`doc-writer`](./doc-writer.yaml) | Mantener `docs/` (ADRs, arquitectura) en sync con el código. | `balanced` | read, grep, glob, edit, write |

---

> **Roles genéricos declarados a propósito** (`code-reviewer`, `security-auditor`): un harness pelado (p. ej.
> OpenCode) no los trae, así que el spec los incluye para ser **portable**. Si tu harness **ya** tiene uno
> equivalente (p. ej. Helix), la **regla de conflicto** del protocolo lo reutiliza en vez de duplicarlo.
