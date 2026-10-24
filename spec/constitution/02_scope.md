<!--
====================================================================
 02 — ALCANCE  ·  Nivel 1 (Constitución)
--------------------------------------------------------------------
 POR-PROYECTO. Lo más valioso aquí NO es lo que entra, sino lo que se
 decide dejar FUERA a propósito.
 Estado: BORRADOR 2026-10-24, pendiente de validación del autor.
====================================================================
-->

# 02 — Alcance

## Dentro (in-scope)

- **Convertir a Markdown** archivos PDF, docx, pptx, xlsx, HTML, CSV, EPUB y notebooks de Jupyter (vía
  markitdown, ADR-0004).
- **Convertir LaTeX (`.tex`)** conservando las matemáticas, sobre un subconjunto definido en su spec (ADR-0006).
- **Convertir OpenDocument (`.odt`)** sin dependencias externas (ADR-0006).
- **Extraer solo el artículo** de un HTML como estrategia alternativa a la página completa (ADR-0006).
- **Convertir por lote:** varios archivos y/o carpetas completas, de forma recursiva (ADR-0010).
- **Detectar el formato** de cada archivo aunque la extensión falte o engañe (ADR-0010).
- **Escribir el resultado en `ClearMD_Output`** junto a la entrada, con un reporte por lote (ADR-0010).
- **Ofrecer cuatro interfaces** sobre el mismo núcleo: CLI, ttkbootstrap, PySide6 y flet (ADR-0001).
- **Distribuir ejecutables** para Windows y Linux desde GitHub Actions (ADR-0008).

## Fuera (out-of-scope) — explícito

- **Cualquier funcionalidad con red o nube:** URLs, transcripción de audio, YouTube, Azure, descripción de
  imágenes con LLM. Va contra la promesa de privacidad (ADR-0005).
- **OCR de PDFs escaneados:** requiere modelos o servicios pesados; quizás en el futuro, como opción local.
- **Conversión inversa** (Markdown → docx/pdf): es otro producto.
- **Edición del Markdown resultante dentro de la app:** para eso existen los editores.
- **Base de datos e historial consultable** (ADR-0002).
- **Ejecutable para macOS:** la notarización exige una cuenta de Apple Developer de pago (ADR-0008).
- **Formatos menores** (`.rtf`, `.eml`, subtítulos): quedan en el roadmap, no en la v1.
- **Extracción de imágenes incrustadas** en los documentos: la v1 convierte texto y estructura.

## Supuestos

- Los documentos de entrada caben en la memoria de un equipo de escritorio normal.
- markitdown seguirá siendo mantenido; si no, el puerto `DocumentConverter` permite reemplazarlo.

## Restricciones

- **Privacidad:** ningún documento ni metadato sale de la máquina del usuario.
- **Licencias:** todas las dependencias deben ser compatibles con distribuir una app MIT (ADR-0003).
- **Presupuesto:** cero. Sin servicios pagos, sin firma de código pagada (por ahora).

## Fronteras del sistema

- **Sistema de archivos local:** única entrada y salida. ClearMD solo escribe dentro de `ClearMD_Output` y en
  su archivo de preferencias.
- **markitdown:** dependencia externa encapsulada detrás de `DocumentConverter`.
- **GitHub Actions / Releases:** solo para construir y publicar ejecutables; la app no se comunica con GitHub.
