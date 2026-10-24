# ADR-0004: Motor híbrido — markitdown detrás de un puerto + conversores propios

- **Estado:** aceptada
- **Fecha:** 2026-10-24

## Contexto

Microsoft publica `markitdown` (MIT), que convierte a Markdown muchos formatos: PDF, docx, pptx, xlsx, HTML,
CSV, EPUB, notebooks de Jupyter, correos de Outlook (`.msg`), ZIP, RSS y texto plano. Escribir todo eso desde
cero sería reinventar una librería madura. Pero depender de ella directamente también tiene riesgos:

- está en versión **0.1.9** (antes de 1.0): su API puede cambiar entre versiones menores;
- exige Python `<3.15`;
- su núcleo siempre trae `magika` (detección de tipo por contenido), que a su vez trae `onnxruntime`;
- **no** cubre `.tex`, OpenDocument (`.odt`), `.rtf`, `.eml` ni subtítulos;
- algunos de sus extras envían datos a la nube (ver ADR-0005).

## Decisión

- El núcleo define su propio puerto, `DocumentConverter`. Ningún módulo fuera de `clearmd.converters`
  importa markitdown.
- `markitdown[pdf,docx,pptx,xlsx]==0.1.9` se usa como adaptador para los formatos que ya resuelve bien. Se
  fija la **versión exacta**: actualizarla es un cambio deliberado, con tests.
- ClearMD aporta **conversores propios** para lo que markitdown no cubre o cubre a medias: `.tex`, `.odt` y
  HTML en "modo artículo" (detalle en ADR-0006).

## Consecuencias

- **Se gana:** amplia cobertura de formatos desde el día uno; la dependencia queda aislada y se puede
  reemplazar sin tocar el núcleo; los conversores propios aportan valor donde no hay alternativa.
- **Se paga:** `magika` + `onnxruntime` suman peso a todos los ejecutables; hay que vigilar el tamaño en CI.
  La versión fija exige revisar las actualizaciones a mano.

## Alternativas consideradas

- **Todo desde cero:** descartada; meses de trabajo para igualar formatos que markitdown ya resuelve.
- **Solo markitdown, sin puerto ni conversores propios:** descartada; acopla el núcleo a una API pre-1.0 y no
  aporta nada más allá de la librería.
