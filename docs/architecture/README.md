# docs/architecture — Diseño del sistema

ClearMD sigue una arquitectura de **puertos y adaptadores** (ADR-0001): un núcleo que no conoce ni las GUIs
ni las librerías de conversión, rodeado de adaptadores intercambiables.

```
            Adaptadores de entrada                               Adaptadores de conversión
   ┌──────────────────────────────────┐                   ┌──────────────────────────────────┐
   │ cli   ttk   qt   flet            │                   │ markitdown (pdf, docx, pptx,     │
   │   (cada GUI es una vista)        │                   │   xlsx, html, csv, epub, ipynb)  │
   └───────────────┬──────────────────┘                   │ tex  (pylatexenc + visitor)      │
                   │                                      │ odt  (stdlib)                    │
           ┌───────▼────────┐                             │ html modo artículo (trafilatura) │
           │   presenter    │  lógica de interacción       └───────────────▲──────────────────┘
           │     (MVP)      │  compartida por las GUIs                     │ implementan
           └───────┬────────┘                                              │ DocumentConverter
                   │                                                       │
           ┌───────▼───────────────────────────────────────────────────────┴───┐
           │ core: puertos (DocumentConverter, FormatDetector), modelos y      │
           │ casos de uso (planear lote → confirmar → ejecutar, ADR-0010)      │
           └───────────────────────────────────────────────────────────────────┘
```

**Regla de dependencias:** todo apunta hacia `core`. `core` no importa nada de afuera.

## Flujo de una conversión por lote (ADR-0010)

1. El adaptador de entrada recibe archivos y/o carpetas.
2. `core` escanea, detecta el formato de cada archivo y calcula los destinos en `ClearMD_Output`
   (resolviendo colisiones) → **plan del lote**.
3. El adaptador muestra el plan; si hay salidas existentes, el usuario decide.
4. `core` ejecuta: por cada archivo elige el conversor, escribe el Markdown, informa progreso y respeta la
   cancelación. Un fallo no detiene el lote.
5. Se escribe el reporte del lote en `ClearMD_Output`.

> Este documento describe la arquitectura objetivo de la Fase 0. Se actualiza a medida que cada feature la
> construye.
