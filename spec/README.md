# spec/ — Lo que DEBE ser verdad (prescriptivo)

El **contrato del sistema**. Si el código no coincide con lo que aquí se declara, **el código está mal**.
Sigue el flujo SDD: **Constitución → Spec → Plan → Tareas**.

| Carpeta / archivo | Nivel SDD | Qué contiene |
|---|---|---|
| `constitution/` | 1 | Principios inmutables del proyecto (propósito, principios, alcance, stack). |
| `roadmap.md` | — | Qué se construye y en qué orden (por-proyecto; **no** es constitución). |
| `features/` | 2–4 | Una carpeta por feature: `spec.md` (qué), `plan.md` (cómo), `tasks.md` (pasos). |
| `contracts/` | — | Contratos **transversales**: OpenAPI, esquemas compartidos, eventos. |

> `docs/` responde *cómo y por qué quedó así*; `spec/` responde *qué debe ser verdad*. **Fallan distinto.**
