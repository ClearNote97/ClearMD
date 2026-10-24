# src/ — Implementación (núcleo + adaptadores)

El paquete `clearmd` (layout `src/`, ADR-0007). Las dependencias apuntan **hacia el núcleo**, nunca al revés
(ADR-0001). Cada subpaquete documenta su rol en el docstring de su `__init__.py`.

| Carpeta | Rol |
|---|---|
| `clearmd/core/` | Dominio: puertos (`DocumentConverter`, `FormatDetector`), modelos y casos de uso. No importa ninguna GUI ni librería de conversión. |
| `clearmd/converters/` | Adaptadores de conversión: el envoltorio de markitdown y los conversores propios (.tex, .odt, HTML modo artículo). |
| `clearmd/presenter/` | Lógica de interacción compartida por todas las GUIs (patrón MVP). |
| `clearmd/cli/` | Adaptador de línea de comandos: la primera interfaz y la que usan los tests de aceptación. |

Las GUIs (`ttk`, `qt`, `flet`) se agregan como subpaquetes en su fase (ver `spec/roadmap.md`).
