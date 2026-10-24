# ClearMD

**Convierte documentos a Markdown. 100% local: tus archivos nunca salen de tu máquina.**

> 🚧 **Estado: Fase 0.** El repositorio tiene la arquitectura, las decisiones y el entorno de desarrollo listos;
> la conversión se construye en la feature 001 (ver [roadmap](./spec/roadmap.md)). Hoy `clearmd` solo responde
> `--version`.

## Qué hará

- Convertir **PDF, Word, PowerPoint, Excel, HTML, CSV, EPUB y notebooks** a Markdown.
- Convertir **LaTeX (`.tex`)** conservando las ecuaciones (`$...$`), sin pandoc.
- Convertir **LibreOffice (`.odt`)** sin dependencias externas.
- Extraer **solo el artículo** de una página HTML guardada.
- Procesar **varios archivos o carpetas enteras** de una vez, detectando el formato de cada archivo.
- Dejar el resultado en una carpeta **`ClearMD_Output`** junto a lo que elegiste, con un reporte del lote.
- Ofrecer la misma funcionalidad en **línea de comandos** y en **tres interfaces gráficas** (ttkbootstrap,
  PySide6 y flet), con ejecutables descargables para Windows y Linux.

## Cómo está construido

Un núcleo puro (puertos y casos de uso) rodeado de adaptadores intercambiables: conversores por un lado,
interfaces por el otro. Así las cuatro interfaces comparten exactamente la misma lógica.

```
 CLI · ttkbootstrap · PySide6 · flet  →  presenter  →  core  ←  markitdown · tex · odt · html-artículo
```

Detalle en [`docs/architecture/`](./docs/architecture/).

## Decisiones de diseño

Cada decisión no trivial tiene su ADR en [`docs/decisions/`](./docs/decisions/), con contexto, alternativas
descartadas y consecuencias. Algunas:

- [Núcleo puro con puertos y adaptadores](./docs/decisions/0001-nucleo-y-adaptadores.md)
- [PySide6 en vez de PyQt6, por licencia](./docs/decisions/0003-pyside6-en-vez-de-pyqt6.md)
- [markitdown detrás de un puerto + conversores propios](./docs/decisions/0004-motor-hibrido-con-markitdown.md)
- [100% local](./docs/decisions/0005-cien-por-ciento-local.md)
- [LaTeX sin pandoc](./docs/decisions/0006-conversores-propios.md)
- [Poda de la plantilla de partida](./docs/decisions/0009-poda-de-la-plantilla.md)

## Desarrollo

Requisitos en el host: **Docker + Docker Compose v2** y **VS Code con Dev Containers** (en Windows, dentro de
WSL 2). Nada de Python en el host.

1. Abre la carpeta en VS Code → **Reopen in Container**.
2. El contenedor instala las dependencias con `uv` automáticamente.
3. Dentro del contenedor:

```bash
uv run pytest                                   # tests
uv run ruff check . && uv run ruff format --check .
uv run mypy                                     # tipos (strict)
uv run clearmd --version
```

El proyecto sigue **Spec-Driven Development**: [`spec/`](./spec/) define lo que debe ser verdad;
[`docs/`](./docs/) explica cómo y por qué quedó así. La colaboración con agentes de IA se rige por
[`README_AGENTS.md`](./README_AGENTS.md).

## Licencia

[MIT](./LICENSE) © 2026 Nicolás Enrique Valencia Santiago
