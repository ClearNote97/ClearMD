# ADR-0010: Conversión por lote, autodetección de formato y carpeta `ClearMD_Output`

- **Estado:** aceptada (las reglas finas se fijan en la spec de la feature 001)
- **Fecha:** 2026-10-24

## Contexto

El caso de uso real no es "un archivo", sino "estos archivos" o "esta carpeta". El usuario necesita saber
**dónde quedó el resultado** sin elegir una ubicación cada vez, y la app no puede confiar en que la extensión
de un archivo diga la verdad.

## Decisión

### Entrada

- Uno o varios archivos y/o carpetas. Las carpetas se recorren **de forma recursiva** por defecto
  (`--no-recursive` en la CLI para desactivarlo).
- En las GUIs, dos acciones separadas ("Agregar archivos" y "Agregar carpeta"), porque los diálogos nativos de
  Windows, Linux y macOS no permiten elegir archivos y carpetas en la misma ventana. Arrastrar y soltar donde el
  toolkit lo permita.

### Autodetección

Puerto `FormatDetector` con detectores encadenados, del más barato al más caro:

1. extensión del archivo;
2. firma interna (por ejemplo, el archivo `mimetype` dentro del zip de un `.odt`);
3. `magika` (ya incluido con markitdown), que detecta el tipo por contenido;
4. heurística para `.tex` (`\documentclass`, `\begin{document}`), que no tiene firma binaria.

Lo que no se reconoce se omite y se reporta; no detiene el lote.

### Salida

- Archivo `D/informe.pdf` → `D/ClearMD_Output/informe.md`.
- Carpeta `P/proyecto/` → `P/ClearMD_Output/proyecto/…`, con la misma estructura de subcarpetas.
- Si dos entradas **del mismo lote** producen el mismo nombre, ambas llevan un sufijo:
  `informe (pdf).md`, `informe (docx).md`. Los destinos se calculan todos antes de escribir, para que el
  resultado no dependa del orden de procesamiento.
- Si una salida ya existe **de una corrida anterior**, se pregunta. Patrón **planear → confirmar → ejecutar**:
  el núcleo arma el plan del lote (destinos, conflictos, omitidos), la GUI lo muestra y el usuario decide una
  vez (sobrescribir todo, omitir todo o caso por caso). En la CLI: `--overwrite` o `--skip`. Sin terminal
  interactiva y sin bandera, la CLI termina con un error: **nunca sobrescribe en silencio**.

### Reglas de seguridad y robustez

- Cualquier carpeta `ClearMD_Output` se excluye del escaneo, para no reconvertir resultados.
- No se siguen enlaces simbólicos; se ignoran archivos ocultos; hay un límite de tamaño por archivo.
- Sin permiso de escritura junto a la entrada: se avisa y se ofrece otra ubicación.
- Un archivo que falla no detiene el lote; cada lote deja un **reporte** en `ClearMD_Output`.

## Consecuencias

- **Se gana:** el resultado aparece junto al original; el cálculo de destinos es una función pura y fácil de
  testear; el plan previo sirve como vista previa y evita sobrescrituras accidentales.
- **Se paga:** más lógica en el núcleo (planificación, colisiones, reporte) que una conversión archivo por
  archivo.
