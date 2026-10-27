<div align="center">

# 📝 ClearMD

**Convierte tus documentos a Markdown — 100% local: ClearMD nunca usa internet.**

_PDF, Word, OpenDocument, PowerPoint, Excel, HTML, CSV, EPUB, notebooks y LaTeX (con sus ecuaciones) → Markdown limpio, una
carpeta entera de una vez,
pensado primero para quienes nunca abren una terminal._

![Python](https://img.shields.io/badge/Python-3.12%E2%80%933.14-3776AB?logo=python&logoColor=white)
![markitdown](https://img.shields.io/badge/markitdown-0.1.9-0078D4?logo=microsoft&logoColor=white)
![uv](https://img.shields.io/badge/uv-gestionado-DE5FE9?logo=uv&logoColor=white)
![Dev Container](https://img.shields.io/badge/Dev-Container-2496ED?logo=docker&logoColor=white)
![Spec-Driven](https://img.shields.io/badge/Spec--Driven-Development-6E40C9)
![hecho con Claude Code](https://img.shields.io/badge/hecho%20con-Claude%20Code-D97757?logo=anthropic&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Estado](https://img.shields.io/badge/estado-en%20construcci%C3%B3n-orange)

[Read in English](./README.md)

</div>

> 👋 **¿Quieres conocer mis otros proyectos?** → **[github.com/ClearNote97](https://github.com/ClearNote97)**

---

## 🧩 El problema

> **El contenido útil está atrapado en formatos pesados, y las herramientas para liberarlo no son para todos.**

Notas para Obsidian, documentación para GitHub, contexto para un LLM: todo eso pide Markdown, mientras el
contenido vive en PDFs, Word y hojas de cálculo. Las respuestas que existen son librerías de línea de comandos,
servicios web que te obligan a **subir tus documentos**, o conversores de un solo formato. Ninguna está hecha para
alguien que nunca ha abierto una terminal — y los documentos privados (contratos, historias clínicas, tesis sin
publicar) nunca deberían tener que salir de la máquina.

---

## 🧠 Cómo lo resolví

El valor está en el método — un producto pequeño construido como uno serio:

1. **Primero las decisiones, por escrito.** Cada decisión no trivial es un ADR en
   [`docs/decisions/`](./docs/decisions/) (23 hasta hoy), con las alternativas descartadas y su costo: por qué
   PySide6 y no PyQt6, por qué sin pandoc, por qué sin base de datos, por qué un proceso aparte.
2. **La spec antes que el código.** Con **Spec-Driven Development**, [`spec/`](./spec/) dice lo que *debe* ser
   verdad: la feature 001 tiene 44 criterios de aceptación y la 002 tiene 22, y un test falla si algún criterio de
   cualquier feature queda sin su test.
3. **Un núcleo que no sabe nada de afuera.** Arquitectura hexagonal organizada con las carpetas `backend/` y
   `frontend/` de mi plantilla: los casos de uso solo importan la librería estándar; markitdown y magika viven
   detrás de puertos y corren **solo en un proceso aparte**.
4. **Archivos no confiables, tratados como tales.** Las bombas ZIP se detectan desde el índice antes de
   descomprimir nada; nunca se siguen enlaces; cada archivo corre con límite de tiempo y de memoria (con tope duro
   del sistema operativo); un enlace plantado en la carpeta de salida no puede desviar una escritura; Ctrl+C
   detiene al instante. Una tesis en LaTeX se sigue solo dentro de su carpeta y sus macros se expanden con un
   presupuesto (una bomba de macros se detiene), y el Markdown nunca trae HTML, una imagen remota ni un enlace
   que el documento no escribió como LaTeX — lo comprueban en la suite un parser CommonMark y un fuzz. Un `.odt`
   se lee con un lector XML propio de ClearMD (sin `DOCTYPE`, con límites de tamaño y profundidad), con la misma
   garantía y un presupuesto para que ningún archivo pequeño se multiplique en un Markdown enorme.
5. **Medido, no adivinado.** Los benchmarks ([001](./docs/benchmarks/001-conversion-limits.md),
   [002](./docs/benchmarks/002-tex-converter.md), [003](./docs/benchmarks/003-odt-converter.md)) fijaron los
   límites y la velocidad de cada formato: el PDF es el cuello de botella por tiempo (~10 páginas/s), el xlsx por
   memoria, una tesis de 300 páginas en LaTeX tarda ~3 s y un informe `.odt` de 300 páginas, menos de un
   segundo. Los
   archivos se convierten del más liviano al más pesado, y el tiempo restante se estima con la velocidad real del
   lote.
6. **Revisado por ojos independientes.** Una revisión de código, una auditoría de seguridad y una verificación
   adversarial de los arreglos — que encontró huecos reales en la primera ronda, cerrados antes de publicar. Para los
   conversores de LaTeX y de OpenDocument hicieron falta tres rondas en cada uno: todas están en el historial,
   con el test que reproduce cada hallazgo.

> 🤖 Trabajé esto con un agente de IA (**Claude Code**): yo dirijo — defino el problema, decido el diseño y
> reviso cada paso; el agente ejecuta y deja todo trazado.

---

## 👀 Un vistazo

Una carpeta mixta, con un PDF protegido con contraseña, un documento sin extensión, dos archivos que quedarían
con el mismo nombre y una bomba ZIP disfrazada de Word:

```text
$ clearmd Tesis/ --lang es
– factura.docx — este archivo parece dañado o inseguro
[1/5] escaneado
[2/5] Informe.docx · faltan menos de un minuto
[3/5] informe.pdf · faltan menos de un minuto
[4/5] datos.xlsx · faltan menos de un minuto
[5/5] contrato.pdf · faltan menos de un minuto
✗ contrato.pdf — Este archivo está protegido con contraseña. Quítale la contraseña e inténtalo de nuevo.
4 convertidos · 1 omitidos · 1 con error
Resultados: ClearMD_Output
```

Y el `Resumen_ClearMD.md` que deja junto a los resultados:

| Origen | Resultado | Formato | Tiempo |
|---|---|---|---|
| `Tesis/escaneado` | `OutputMD/Tesis/escaneado.md` | DOCX, detectado por su contenido | <1 s |
| `Tesis/Informe.docx` | `OutputMD/Tesis/Informe (docx).md` | DOCX | <1 s |
| `Tesis/informe.pdf` | `OutputMD/Tesis/informe (pdf).md` | PDF | <1 s |
| `Tesis/capitulos/datos.xlsx` | `OutputMD/Tesis/capitulos/datos.md` | XLSX | <1 s |

_Además, los archivos con error y omitidos con su razón en palabras sencillas, y el historial de lotes
anteriores._

---

## 🚧 Estado

| Feature | | |
|---|---|---|
| **001** Conversión por lotes — backend + CLI | ✅ lista | 512 tests · revisada |
| **002** Conversor de `.tex` (con ecuaciones, sin pandoc) | ✅ lista | 807 tests en total · revisada |
| **003** Conversor de `.odt` (solo librería estándar) | ✅ lista | 1085 tests en total · revisada |
| **004** Modo artículo para HTML | ⏳ | |
| **005** Primera app de escritorio (ttkbootstrap) | ⏳ | |
| **006** CI + ejecutables para Windows y Linux | ⏳ | |
| **007–008** Apps en PySide6 y flet | ⏳ | |

El plan completo está en el [roadmap](./spec/roadmap.md). Hoy ClearMD es una **herramienta de línea de comandos**;
las apps de escritorio vienen después.

---

## ▶️ Cómo correr

**Desde el repositorio** (aún no está en PyPI):

```bash
uv tool install git+https://github.com/ClearNote97/ClearMD   # recomendado: la misma herramienta del stack
# o: pip install git+https://github.com/ClearNote97/ClearMD  (Python 3.12–3.14)

clearmd informe.pdf notas.docx               # archivos
clearmd ~/Documentos/proyecto                # una carpeta completa, con subcarpetas
clearmd tesis/ --output-root ~/Escritorio    # resultados en ~/Escritorio/ClearMD_Output
clearmd proyecto/ --dry-run                  # ver el plan sin escribir nada
clearmd informe.pdf --lang es                # mensajes en español
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

**Códigos de salida:** `0` todo convertido · `1` algún archivo falló o se detuvo · `2` error de uso o ninguna
entrada válida · `3` hay resultados existentes y nadie puede responder · `130` cancelado. **Configuración**
(opcional): `settings.toml` en tu carpeta de configuración de usuario (en Linux `~/.config/ClearMD/`) —
`language = "es"`, `on_existing_output = "skip"`, `recursive = false`…

> 🔒 ClearMD nunca usa internet. Si guardas los resultados en una carpeta de OneDrive, Google Drive o Dropbox,
> esa aplicación sí puede subirlos a la nube — eso lo hace la app de sincronización, no ClearMD.

---

## 📦 Qué produce

```
ClearMD_Output/          junto a lo que elegiste (o en --output-root)
  Resumen_ClearMD.md     qué se convirtió (nombre original → nuevo, formato, tiempo), se detuvo, falló o se
                         omitió, y el historial de lotes anteriores
  OutputMD/              los Markdown, con la misma estructura de tus carpetas
```

---

## 🗂️ Estructura

```
.
├── src/clearmd/
│   ├── backend/
│   │   ├── api/         # la fachada que usan todas las interfaces + el composition root
│   │   ├── schemas/     # datos inmutables: planes, reportes, límites, códigos de error (solo stdlib)
│   │   ├── use_cases/   # escanear → planear → ordenar → ejecutar → reportar, y los puertos (solo stdlib)
│   │   └── services/    # proceso worker, adaptadores de markitdown y magika, resumen, configuración
│   ├── frontend/cli/    # la línea de comandos (las GUIs llegan aquí, una carpeta cada una)
│   └── i18n/            # catálogos de mensajes EN/ES
├── spec/                # ★ Spec-Driven Development: constitución, roadmap, specs, contrato de UX
├── docs/                # arquitectura, 25 ADRs, benchmarks
├── tests/               # unit (espejo de src) · aceptación (uno por criterio) · fixtures · benchmark
└── .devcontainer/       # entorno reproducible (sin root, uv)
```

---

## 🛠️ Stack

**Python 3.12–3.14** · **[markitdown](https://github.com/microsoft/markitdown)** (conversión) ·
**[magika](https://github.com/google/magika)** (detección por contenido) · **psutil** (límites del worker) ·
**platformdirs** · **pytest · ruff · mypy --strict** · **uv** · **Dev Container + Docker**.

**Plantilla base:** [ClearNote_Dev](https://github.com/ClearNote97/ClearNote_Dev) — mi plantilla insignia de
desarrollo en Python bajo Spec-Driven Development. ClearMD nació de ella y se podó: sin base de datos, sin backend
web — una herramienta de escritorio ([ADR-0009](./docs/decisions/0009-template-pruning.md)).

**Desarrollo:** abre la carpeta en VS Code → *Reopen in Container*; luego `uv run pytest`,
`uv run ruff check .`, `uv run mypy`. La colaboración con agentes de IA sigue [`README_AGENTS.md`](./README_AGENTS.md).

---

## 🙏 Créditos

- **Autor:** MSc. Nicolás Enrique Valencia Santiago.
- **Par de trabajo:** agente de IA (Claude / Claude Code, en el marco [Helix](https://github.com/ftuga/helix_asisten)
  de [ftuga](https://github.com/ftuga)).
- **Conversión:** [markitdown](https://github.com/microsoft/markitdown) (MIT) · **Detección:**
  [magika](https://github.com/google/magika) (Apache-2.0).

## ⚖️ Licencia

[MIT](./LICENSE) © 2026 Nicolás Enrique Valencia Santiago.
