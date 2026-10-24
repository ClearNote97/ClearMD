# docs/decisions — ADRs (Architecture Decision Records)

Un archivo por decisión no trivial: `NNNN-titulo-corto.md`. Formato mínimo:

```
# ADR-0001: <título>
- Estado: propuesta | aceptada | reemplazada por ADR-XXXX
- Fecha: AAAA-MM-DD
- Contexto: qué problema/fuerzas motivan la decisión
- Decisión: qué se decidió
- Consecuencias: qué se gana y qué se paga
```

Opcional: **Alternativas consideradas** (qué se descartó y por qué).
Un ADR aceptado no se reescribe para cambiar la decisión: se escribe uno nuevo que lo reemplaza.

## Índice

| ADR | Decisión | Estado |
|---|---|---|
| [0001](./0001-nucleo-y-adaptadores.md) | Núcleo puro con puertos y adaptadores (CLI + 3 GUIs + presenter) | aceptada |
| [0002](./0002-sin-base-de-datos.md) | Sin base de datos; preferencias en TOML | aceptada |
| [0003](./0003-pyside6-en-vez-de-pyqt6.md) | PySide6-Essentials en vez de PyQt6 (licencia) | aceptada |
| [0004](./0004-motor-hibrido-con-markitdown.md) | Motor híbrido: markitdown detrás de un puerto + conversores propios | aceptada |
| [0005](./0005-cien-por-ciento-local.md) | 100% local: los documentos nunca salen de la máquina | aceptada |
| [0006](./0006-conversores-propios.md) | Conversores propios: .tex, .odt y HTML modo artículo | aceptada |
| [0007](./0007-paquete-real-con-layout-src.md) | Paquete real con layout `src/` | aceptada |
| [0008](./0008-contenedor-solo-para-desarrollo.md) | Contenedor para desarrollo; ejecutables desde CI | aceptada |
| [0009](./0009-poda-de-la-plantilla.md) | Poda de la plantilla ClearNote_Dev | aceptada |
| [0010](./0010-lote-autodeteccion-y-clearmd-output.md) | Lote, autodetección y carpeta `ClearMD_Output` | aceptada |
