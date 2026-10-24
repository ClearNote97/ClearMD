# ADR-0001: Núcleo puro con puertos y adaptadores

- **Estado:** aceptada
- **Fecha:** 2026-10-24

## Contexto

ClearMD tiene un objetivo de producto (convertir documentos a Markdown) y uno de aprendizaje: construir
**la misma app con tres toolkits de GUI** (ttkbootstrap, PySide6 y flet) además de una CLI. Si la lógica de
conversión viviera dentro de cada GUI, habría tres copias del mismo comportamiento, imposibles de mantener
iguales y difíciles de testear sin abrir ventanas.

Además, convertir un PDF o una carpeta entera puede tardar segundos o minutos, y cada toolkit maneja la
concurrencia de forma distinta: tkinter no es thread-safe (hilo de trabajo + cola + `after()`), Qt usa
`QThreadPool` con señales y flet es asíncrono.

## Decisión

Arquitectura hexagonal (puertos y adaptadores):

- **`clearmd.core`** — el dominio. Define los puertos (`DocumentConverter`, `FormatDetector`), los modelos
  y los casos de uso. No importa ninguna GUI ni ninguna librería de conversión.
- **`clearmd.converters`** — adaptadores que implementan `DocumentConverter` (markitdown y conversores propios).
- **`clearmd.presenter`** — capa MVP con la lógica de interacción compartida (qué se muestra, qué se habilita,
  cómo se reportan progreso y errores). Las GUIs son vistas delgadas sobre ella.
- **`clearmd.cli`** y una GUI por subpaquete — adaptadores de entrada.

Las dependencias apuntan siempre hacia el núcleo. El núcleo ofrece una **API síncrona con callback de progreso
y token de cancelación**; cada adaptador decide cómo ejecutarla fuera de su hilo de interfaz.

## Excepción a la doctrina de la plantilla

El principio 7 de la constitución y `03_stack.md` piden **un solo framework de UI activo a la vez**. ClearMD
tiene tres a propósito, porque compararlas es parte del objetivo del proyecto. La excepción se acota así:

- cada GUI vive en su propio subpaquete y se instala con su propio extra;
- cada ejecutable empaqueta **una sola** GUI;
- ninguna GUI importa a otra; solo comparten `core` y `presenter`.

## Consecuencias

- **Se gana:** un solo lugar para la lógica, testeable sin GUI; agregar una interfaz no toca el núcleo;
  la comparación entre toolkits es justa porque todas usan el mismo motor.
- **Se paga:** más capas y más indirección que una app de un solo archivo; el contrato del presenter tiene
  que diseñarse con cuidado para que sirva a tres modelos de concurrencia distintos.

## Alternativas consideradas

- **Tres apps independientes:** descartada por triplicar lógica y tests.
- **Núcleo sin presenter:** descartada; cada GUI reimplementaría la lógica de interacción y el problema de
  concurrencia quedaría disperso.
