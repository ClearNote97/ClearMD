# ADR-0006: Conversores propios — .tex, .odt y HTML modo artículo

- **Estado:** aceptada
- **Fecha:** 2026-10-24

## Contexto

markitdown no convierte LaTeX ni OpenDocument, y su conversión de HTML incluye todo el contenido de la página
(menús, pies, anuncios). Son los huecos donde ClearMD puede aportar algo propio (ADR-0004).

## Decisión

### `.tex` (LaTeX) — la funcionalidad principal

- Parser: **`pylatexenc`** (MIT, 2.11) construye el árbol del documento; un *visitor* propio lo recorre y emite
  Markdown.
- Las matemáticas **se conservan tal cual** (`$...$`, `$$...$$`; `\[...\]` y `equation` pasan a `$$...$$`):
  GitHub, Obsidian y VS Code ya las renderizan en Markdown.
- Se convierte la estructura: secciones, énfasis, listas, enlaces, bloques de código (`verbatim`,
  `lstlisting`), citas (`\cite{x}` → `[@x]`) y tablas simples.
- LaTeX es un lenguaje de macros Turing-completo: nunca habrá conversión al 100%. La spec de la feature define
  el **subconjunto soportado**; lo desconocido se deja tal cual y se reporta.

### `.odt` (OpenDocument / LibreOffice)

- Solo librería estándar: `zipfile` + `xml.etree.ElementTree` sobre `content.xml`. **Cero dependencias.**
- Relevante en Latinoamérica, donde LibreOffice es común en el sector público y la educación.

### HTML "modo artículo"

- Segunda estrategia para el mismo formato: **`trafilatura`** (Apache-2.0, 2.3.1) extrae solo el contenido
  principal. El usuario elige entre "página completa" (markitdown) y "solo el artículo".
- Muestra el patrón Strategy: mismo formato de entrada, dos estrategias intercambiables.

## Consecuencias

- **Se gana:** un diferencial real (LaTeX → Markdown sin pandoc); un conversor sin dependencias que demuestra
  el puerto; un ejemplo claro de estrategias intercambiables.
- **Se paga:** el conversor `.tex` necesita una spec cuidadosa y muchos fixtures; `trafilatura` trae varias
  dependencias (lxml, entre otras).

## Alternativas consideradas

- **Pandoc para `.tex`:** convierte mejor, pero es un binario Haskell con licencia GPL de ~100 MB. Rompe el
  "full Python", engorda el ejecutable y complica la licencia de la distribución. Descartada.
- **`TexSoup` como parser:** viable (BSD), pero `pylatexenc` está más mantenido.
- **`odfpy` para `.odt`:** su última versión es de 2020 y no declara licencia en PyPI. Descartada.
- **Un HTML propio que repita lo de markitdown:** sin valor agregado. Descartada.
