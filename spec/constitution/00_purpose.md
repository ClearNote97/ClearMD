<!--
====================================================================
 00 — PROPÓSITO  ·  Nivel 1 (Constitución)
--------------------------------------------------------------------
 POR-PROYECTO. Fija el terreno contra el que se justifican el alcance (02),
 los principios (01) y el stack (03).
 Estado: BORRADOR 2026-10-24, redactado a partir de la conversación de
 arranque. Pendiente de validación del autor (sobre todo "Para quién" y
 "Métricas de éxito").
====================================================================
-->

# 00 — Propósito

## Misión

Que cualquier persona pueda convertir sus documentos a Markdown limpio **sin subirlos a ningún servicio**,
con una app de escritorio que se descarga y funciona.

## Problema

- El contenido útil vive atrapado en formatos pesados (PDF, Word, PowerPoint, LaTeX, LibreOffice), y hoy se
  necesita en Markdown: para notas (Obsidian, wikis), para documentación en GitHub y como contexto para LLMs.
- Las herramientas existentes son librerías de línea de comandos (markitdown, pandoc), servicios web que piden
  subir el documento, o conversores de un solo formato.
- LaTeX en particular no tiene una conversión a Markdown en Python puro: la opción habitual es pandoc, un
  binario externo.

## Para quién

- **Usa:** estudiantes y académicos (tesis y papers en LaTeX), profesionales que documentan en Markdown y
  quienes preparan documentos como contexto para un LLM. Personas que no necesariamente usan la terminal.
- **Decide y mantiene:** el autor (proyecto personal y de portafolio público).
- **Paga:** nadie; es software libre (MIT).

Sin multi-tenancy ni cuentas de usuario.

## Métricas de éxito

- Convierte una carpeta mixta (pdf, docx, pptx, xlsx, tex, odt, html) en un solo paso y deja el resultado en
  `ClearMD_Output`, con un reporte de lo convertido, lo omitido y lo fallido.
- Ejecutables descargables para Windows y Linux, publicados desde CI en GitHub Releases.
- La misma funcionalidad en CLI, ttkbootstrap, PySide6 y flet, sobre un único núcleo.
- Cada decisión no trivial está registrada como ADR.

---

> `02_scope` traza las fronteras de este propósito, `01_principles` fija cómo se persigue y `03_stack` con qué.
