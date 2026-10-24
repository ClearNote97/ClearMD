<!--
====================================================================
 ROADMAP  ·  spec/ (fuera de la Constitución)
--------------------------------------------------------------------
 Cambia con frecuencia; el propósito, los principios y el stack no.
 Ordena las features (spec/features/NNN_...) en el tiempo.
====================================================================
-->

# Roadmap

El orden sigue un esqueleto que funcione de punta a punta con la interfaz más barata primero: cada GUI nueva
reutiliza el núcleo y el presenter ya probados (ADR-0001).

## Ahora (en curso)

- [x] **Fase 0:** poda de la plantilla, paquete `clearmd`, ADRs 0001–0010, contenedor de desarrollo limpio.
- [ ] **001 — Núcleo + CLI:** puertos, detección de formato, plan del lote → confirmar → ejecutar,
      `ClearMD_Output`, reporte; adaptador markitdown; CLI completa (ADR-0010).

## Siguiente

- [ ] **002 — Conversor `.tex`** (subconjunto definido en su spec; matemáticas preservadas).
- [ ] **003 — Conversor `.odt`** (solo librería estándar).
- [ ] **004 — HTML modo artículo** (segunda estrategia para `.html`).
- [ ] **005 — Presenter (MVP)** + GUI **ttkbootstrap**.
- [ ] **006 — CI:** tests + ejecutables Windows/Linux en GitHub Releases; tamaño del ejecutable como métrica.

## Después (backlog priorizado)

- [ ] **007 — GUI PySide6-Essentials** (distribución *onedir* por LGPL, ADR-0003).
- [ ] **008 — GUI flet.**
- [ ] Modo incremental: omitir archivos sin cambios desde la última corrida.
- [ ] Formatos menores: `.eml`, `.rtf`, subtítulos.

## Fuera por ahora

Ver `spec/constitution/02_scope.md` → Fuera: red/nube, OCR, conversión inversa, base de datos, macOS.
