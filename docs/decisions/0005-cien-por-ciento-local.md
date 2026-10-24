# ADR-0005: 100% local — los documentos nunca salen de la máquina

- **Estado:** aceptada
- **Fecha:** 2026-10-24

## Contexto

Los documentos que la gente convierte suelen ser privados: contratos, historias clínicas, informes internos,
tesis sin publicar. markitdown incluye conversores que dependen de servicios en red:

- `audio-transcription` (transcripción de audio), `youtube-transcription`;
- `az-doc-intel` y `az-content-understanding` (Azure);
- descripción de imágenes con un LLM;
- conversores de Wikipedia y resultados de Bing, que trabajan sobre URLs.

## Decisión

ClearMD funciona **sin red**:

- no se instalan los extras de markitdown que usan servicios externos;
- ningún conversor propio hace peticiones de red;
- la entrada son archivos y carpetas locales; no se aceptan URLs.

"Tus documentos nunca salen de tu máquina" es una característica del producto y se declara en el README.

## Consecuencias

- **Se gana:** privacidad verificable; funciona sin conexión; sin claves de API ni costos por uso.
- **Se paga:** no hay OCR con IA, ni transcripción de audio, ni conversión de páginas web por URL. Si alguna
  vez se agrega, será opcional, desactivada por defecto y con un ADR nuevo.

## Alternativas consideradas

- **Local por defecto, con red opcional desde ya:** descartada por ahora; agrega superficie y configuración
  sin una necesidad concreta.
