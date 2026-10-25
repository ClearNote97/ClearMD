# ClearMD

[Read in English](./README.md)

**Convierte tus documentos a Markdown. 100% local: ClearMD nunca usa internet.**

> Si guardas los resultados en una carpeta de OneDrive, Google Drive o Dropbox, esa aplicación sí puede
> subirlos a la nube — eso lo hace la app de sincronización, no ClearMD.

> 🚧 **Estado: la línea de comandos funciona (feature 001).** Convierte archivos y carpetas a través de un
> proceso aparte, con límites, un resumen y mensajes en inglés y español. Las apps de escritorio vienen después
> (ver el [roadmap](./spec/roadmap.md)).

## Qué hará

- Convertir **PDF, Word, PowerPoint, Excel, HTML, CSV, EPUB y notebooks** a Markdown.
- Convertir **LaTeX (`.tex`)** conservando las ecuaciones (`$...$`), sin pandoc.
- Convertir **LibreOffice (`.odt`)** sin dependencias externas.
- Extraer **solo el artículo** de una página web guardada.
- Procesar **muchos archivos o carpetas enteras** de una vez, detectando el formato de cada archivo.
- Dejar el resultado en una carpeta **`ClearMD_Output`** junto a lo que elegiste (o en la carpeta que escojas),
  con un `Resumen_ClearMD.md` que lista cada archivo, su nombre nuevo y el historial de lotes anteriores.
- Responder bien con archivos pesados o dañados: primero los más livianos, un límite de tiempo y de memoria por
  archivo, y un Cancelar que funciona al instante.
- Hablar **inglés y español** (inglés por defecto; se cambia en la configuración), con ventana de ayuda,
  bienvenida inicial y progreso claro: pensada para personas que nunca abren una terminal.
- Ofrecer la misma funcionalidad como **línea de comandos** y como **tres apps de escritorio** (ttkbootstrap,
  PySide6 y flet), con ejecutables descargables para Windows y Linux.

## Cómo está construido

Un backend con casos de uso puros rodeado de adaptadores intercambiables: conversores por un lado,
interfaces por el otro, organizado con las carpetas `backend/` y `frontend/` de la plantilla ClearNote_Dev.
Las cuatro interfaces comparten exactamente la misma lógica, y las conversiones corren en un proceso aparte.

```
 frontend: CLI · ttkbootstrap · PySide6 · flet  →  backend: api → use_cases ← services → worker
                                                                     (markitdown · tex · odt · html-artículo)
```

Detalle en [`docs/architecture/`](./docs/architecture/) (en inglés).

## Decisiones de diseño

Cada decisión no trivial tiene su ADR en [`docs/decisions/`](./docs/decisions/) (en inglés), con contexto,
alternativas descartadas y consecuencias. Algunas:

- [Núcleo puro con puertos y adaptadores](./docs/decisions/0001-core-and-adapters.md)
- [PySide6 en vez de PyQt6, por licencia](./docs/decisions/0003-pyside6-over-pyqt6.md)
- [markitdown detrás de un puerto + conversores propios](./docs/decisions/0004-hybrid-engine-with-markitdown.md)
- [100% local](./docs/decisions/0005-fully-local.md)
- [LaTeX sin pandoc](./docs/decisions/0006-own-converters.md)
- [Poda de la plantilla de partida](./docs/decisions/0009-template-pruning.md)
- [Pensada primero para usuarios no técnicos](./docs/decisions/0013-non-technical-users-first.md)
- [Conversiones en un proceso aparte, primero los archivos livianos](./docs/decisions/0015-conversion-worker-process.md)

## Uso (línea de comandos)

```bash
clearmd informe.pdf notas.docx               # archivos
clearmd ~/Documentos/proyecto                # una carpeta completa, con subcarpetas
clearmd tesis/ --output-root ~/Escritorio    # resultados en ~/Escritorio/ClearMD_Output
clearmd proyecto/ --dry-run                  # ver el plan sin escribir nada
clearmd informe.pdf --lang es                # mensajes en español
```

Los resultados quedan en una carpeta `ClearMD_Output` junto a lo que elegiste:

```
ClearMD_Output/
  Resumen_ClearMD.md   qué se convirtió (nombre original → nuevo, tiempo), omitió, detuvo o falló, y el historial
  OutputMD/            los Markdown, con la misma estructura de tus carpetas
```

| Opción | Qué hace |
|---|---|
| `--overwrite` / `--skip` | Qué hacer con resultados que ya existen. Sin ninguna, ClearMD pregunta una vez. |
| `--recursive` / `--no-recursive` | Incluir subcarpetas o no (por defecto: sí). |
| `--output-root DIR` | Crear `ClearMD_Output` dentro de `DIR`. |
| `--dry-run` | Mostrar qué pasaría, sin escribir nada. |
| `--open` | Abrir la carpeta de resultados al terminar. |
| `--lang {en,es}` | Idioma de esta ejecución. |
| `-q`, `--quiet` | Solo el resumen y los errores. |

- **Seguro con cualquier archivo:** nunca sigue enlaces simbólicos; omite ocultos, archivos de bloqueo de Office y
  ZIP; los archivos dañados o sospechosos (bombas ZIP) se reportan sin abrirlos a ciegas; cada archivo tiene
  límite de tiempo y de memoria, y **Ctrl+C** detiene al instante.
- **Códigos de salida:** `0` todo convertido · `1` algún archivo falló o se detuvo · `2` error de uso o ninguna
  entrada válida · `3` hay resultados existentes y nadie puede responder (usa `--overwrite` o `--skip`) ·
  `130` cancelado.
- **Configuración:** un `settings.toml` opcional en tu carpeta de configuración de usuario (en Linux
  `~/.config/ClearMD/settings.toml`) guarda `language = "es"`, `on_existing_output = "skip"`, `recursive = false`…
  Los flags mandan sobre él en una ejecución.

## Instalación

> Aún no está publicada en PyPI: se instala desde el repositorio.

1. **Ejecutables (sin instalar Python)** — para Windows y Linux, desde
   [GitHub Releases](https://github.com/ClearNote97/ClearMD/releases) (feature 006). Lo recomendado para la
   mayoría.
2. **Con `uv`** — lo recomendado para desarrolladores, la misma herramienta del stack de desarrollo:

   ```bash
   uv tool install git+https://github.com/ClearNote97/ClearMD
   clearmd --help
   ```

3. **Con `pip`** (Python 3.12–3.14):

   ```bash
   pip install git+https://github.com/ClearNote97/ClearMD
   clearmd --help
   ```

La publicación en PyPI llega al final del roadmap (ADR-0018).

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
