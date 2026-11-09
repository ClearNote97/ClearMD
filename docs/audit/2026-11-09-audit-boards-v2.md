# Juntas de Auditoría de ClearMD 2.10.0 (Versión 2)

> **Fecha:** 2026-11-09 · **Versión auditada:** 2.10.0 · **Para:** el dueño del producto.
> Segunda auditoría: agentes nuevos desde cero, con las lecciones de la [primera](./2026-11-08-audit-boards.md) aplicadas.
> Documento en español por excepción a ADR-0011: está escrito para que el dueño decida.
> Presentación ejecutiva: <https://claude.ai/artifact/GG1NF4S8bJFh6xkjJmXzxv> (privada: solo la ve el dueño).
> Datos completos de las tres rondas: [`2026-11-09-audit-boards-v2.json`](./2026-11-09-audit-boards-v2.json).

## Cómo leer este documento

- **Si tienes 5 minutos:** lee el resumen ejecutivo (sección 1) y las diez mejoras recomendadas (sección 4).
- **Para decidir:** las secciones 5 (lo que no conviene hacer) y 6 (desacuerdos abiertos).
- **Para el detalle:** la sección 8 trae cada hallazgo verificado: qué siente la persona, qué se recomienda y
  qué comprobó la junta conciliadora. La sección 9 trae el informe de cada auditor.
- Las referencias técnicas (archivo:línea) quedan para quien implemente; no hace falta entenderlas para decidir.

## 1. Resumen ejecutivo

**Veredicto de la junta conciliadora: 7 de 10** (la primera auditoría dio 6,5). ClearMD 2.10.0 cuida
bien los archivos de la persona:

- nunca deja resultados a medias ni pisa trabajo anterior;
- nunca modifica los originales;
- explica casi todos los errores con una acción concreta;
- su lector de PDF es rápido de verdad.

**De las diez mejoras de la primera auditoría:**

- 5 quedaron resueltas del todo: no perder trabajo, señales honestas, la Ayuda, la lista de la
  ventana clásica y la primera experiencia (el instalador liviano pesa 37,9 MB en lugar de 176).
- 5 quedaron en parte.
- Los dos huecos que había encontrado la conciliadora también están resueltos: la app abre en el
  idioma del instalador, y los Office antiguos dicen qué hacer.
- Ninguna empeoró.

**El reto ya no es "no perder trabajo"; es "no decir algo falso".** La conciliadora comprobó en
el código y en el contenedor los casos en que ClearMD da por buena una salida que no lo es:

- Un texto guardado en Windows "a la antigua" sale con "ańo" y "Núńez", marcado como convertido
  y sin ninguna nota.
- "Dividir en 3 partes" puede entregar una sola parte.
- "Copiar Detalles" promete ocultar los nombres de los archivos, pero deja pasar un nombre entre
  comillas.
- Un PDF vacío se reporta como "dañado".
- Cancelar en el último paso de Unir termina en "error inesperado".
- En PDF reales, algunas tablas parten un registro en varias filas y algunas ecuaciones salen mal
  sin aviso.

**La buena noticia:** de las diez mejoras nuevas, cinco son de esfuerzo pequeño y ninguna exige
rediseñar.

**Sobre tu pregunta del tiempo:**

- Que una publicación tarde entre 6 y 9 minutos es normal: arma 4 ejecutables y 3 instaladores, y
  los prueba.
- Que la CI tarde de 20 a 24 minutos no lo es. La conciliadora lo midió: una limpieza de memoria
  que corre después de *cada* prueba la vuelve unas 3,5 veces más lenta de lo necesario. Limitarla
  a las pruebas de ventana debería dejarla en menos de la mitad, sin quitar ninguna garantía.
- Lo que sí nota la persona es que la App Clásica instalada se desempaca cada vez que se abre:
  unos 5 segundos en Windows.

### Lo que tienes que decidir

1. **Si te acoges a las diez mejoras nuevas** (sección 4). Recomendación: sí, empezando por las
   cinco pequeñas (1, 2, 3, 7 y 8), que atacan justamente "no decir algo falso".
2. **Qué hacer con los desacuerdos abiertos** (sección 6).
3. **Si confirmas la lista de lo que no conviene hacer** (sección 5).

## 2. Qué se hizo

Se convocaron **tres juntas**, todas con la frase **"Claridad es cariño"** como criterio, pensando en una
persona del público general que nunca ha abierto una terminal:

| Junta | Integrantes | Qué miró |
| --- | --- | --- |
| **Backend** | 4 auditores | Lógica · Eficiencia · Lo que entrega (Markdown, resumen, carpetas, terminal) · Claridad es cariño |
| **Frontend** | 4 auditores | Lógica · Eficiencia · Estilo visual UI/UX · Claridad es cariño |
| **Conciliadora** | 1 auditora | Verificó en el código lo que dijeron las otras dos, resolvió desacuerdos y ordenó por valor para el cliente final |

**Tres rondas:**

1. **Revisión independiente.** Cada auditor revisó por su cuenta y reprodujo lo que pudo con la app real en el
   contenedor de desarrollo. Resultado: 69 hallazgos.
2. **Debate.** Cada auditor leyó los ocho informes, de las dos juntas, y apoyó, cuestionó, matizó o amplió los
   hallazgos de los demás. Fueron 99 intervenciones. Después corrigió su propio
   informe: 72 hallazgos tras el debate.
3. **Conciliación.** La junta conciliadora volvió al código y a las capturas, unió los duplicados y quedó con
   **27 hallazgos verificados**.

**Lecciones de la primera auditoría, aplicadas como reglas** (`docs/lessons-learned.md`, IX.16):

- Cada auditor leyó los ADR antes de recomendar algo que los contradijera, y lo citó.
- Cada hallazgo dice si su evidencia la comprobó el propio auditor.
- En el debate, subir una gravedad exigía volver a comprobarla en el código (`reverified`).
- La ronda 2 debía listar todo hallazgo propio que retiraba y por qué; la conciliadora comparó las dos rondas.
- Las juntas no leyeron la primera auditoría; solo la conciliadora, para decir qué se resolvió.
- Ningún informe nombra los documentos privados del dueño, y antes de publicar se revisó que así fuera.

**Comprobación de lo retirado:** Comparé la ronda 1 con la ronda 2 lente por lente: B1 8→8, B2 7→9 (+B2-08 y B2-09, adoptados de F2-02 y B1-08), B3 10→10, B4 10→10, F1 8→8, F2 7→8 (+F2-08), F3 9→9 (−F3-08 y +F3-10), F4 10→10 (F4-06 se reformuló sin perder la parte de jerga). Solo se retiraron dos cosas, y las dos con razón:
- F3-08 (Title Case en español), por la doctrina del dueño (ADR-0041).
- La segunda mitad de F4-01 (sacar Resumen e Imágenes del paso 1), por la spec 009 AC-10. Lo verifiqué en spec/features/009.

No restauro ningún hallazgo. Sí dejo una nota: F4-06 de la ronda 1 incluía «issue» y la cuenta de GitHub como barrera; eso sigue vivo dentro del hallazgo fusionado B4-01/F4-06/B4-05.

Severidades que subieron sin reverified=true y que revisé yo:
- B2-05: el mecanismo lo confirmé en el spec y en el .iss; lo dejo en media.
- B1-06, propuesto como media: lo reproduje y lo dejo en baja.

**Notas por lente (de 0 a 10, tras el debate):**

| Lente | Nota | Hallazgos | Intervenciones en el debate |
| --- | --- | --- | --- |
| Backend · Lógica | 7 | 8 | 14 |
| Backend · Eficiencia | 6,5 | 9 | 9 |
| Backend · Experiencia de lo que entrega | 6 | 10 | 13 |
| Backend · Claridad es cariño | 7 | 10 | 18 |
| Frontend · Lógica | 7,5 | 8 | 11 |
| Frontend · Eficiencia | 6,5 | 8 | 9 |
| Frontend · Estilo visual UI/UX | 7 | 9 | 10 |
| Frontend · Claridad es cariño | 7,5 | 10 | 15 |

## 2b. Qué se resolvió desde la primera auditoría

| Estado | Mejora de la primera auditoría | Nota de la conciliadora |
| --- | --- | --- |
| ✅ Resuelto | 1. Nunca perder ni pisar trabajo anterior (partes en temporal, sufijo (2) en uniones) | PartStage (part_stage.py) y free_target en merging._write están activos; ningún auditor encontró que se pise trabajo. |
| ◐ Parcial | 2. Que Unir siempre deje resumen y motivo, y exija dos documentos desde el paso 1 | La ventana avisa desde Revisar (primary.py). La CLI decide NOTHING_TO_MERGE al final (merging.py:167) sin imprimir el motivo, y una cancelación durante merge_pdfs se escapa sin resumen (B1-03). |
| ◐ Parcial | 3. Cerrar los defectos de contenido silencioso (duplicados carpeta+archivo, CSV con punto y coma, imágenes rotas al dividir o unir) | El separador del CSV (csv_dialect.py) y los duplicados (scanning.first_time) están resueltos. Las imágenes siguen rotas en la CLI (api/__init__.py:145), y apareció un defecto silencioso nuevo: cp1252. |
| ✅ Resuelto | 4. Una señal honesta: notas informativas sin ⚠️ y lo conservado fuera de «atención» | 035 AC-01 y AC-02: notas en dos niveles y una sección «Conservados» aparte (writer.py:113). Queda el titular «Ninguno se pudo convertir» cuando hay conservados (B4-08). |
| ✅ Resuelto | 5. Reescribir la Ayuda por herramienta y explicar en una frase qué es Markdown | 035 AC-04 y la explicación de Markdown en [gui.help]. Lo que falta es solo llevar esa frase al Inicio y a la bienvenida (F4-02). |
| ◐ Parcial | 6. Ver el motivo completo en Revisar y la ruta exacta en Resultados | 035 AC-05 y AC-06: el motivo completo de la fila seleccionada aparece debajo de la lista, y la ruta como texto. Las columnas de la lista siguen truncadas (F3-01) y las rutas no se pueden pulsar. |
| ✅ Resuelto | 7. Arreglar la lista de la ventana clásica: barra visible e imágenes en caché | ttk/components/file_list.py:65 tiene Scrollbar, y el dibujo se limita a las filas visibles (035 AC-07). |
| ◐ Parcial | 8. Mensajes de error que no engañan ni usan jerga | 036 AC-01 a AC-04: terminal separada, Office cifrado, error inesperado sin nombres técnicos. Siguen el archivo vacío como «dañado», la acción de dividir sin importar el formato, y una promesa de privacidad que no se cumple. |
| ✅ Resuelto | 9. Una primera experiencia amable: instalador liviano, app en el idioma del instalador, accesos sin nombres técnicos | 037 (instalador liviano), clearmd.iss:508-515 escribe language="es", y accesos «App Moderna» y «App Estilo Móvil» (iss:150-154). Nuevo: el arranque lento de la Clásica de un solo archivo. |
| ◐ Parcial | 10. Estimaciones creíbles y control de memoria también al dividir Excel | 036 AC-05 y AC-06: «Página N de M» y Excel estimado como Excel. Los PDF siguen estimándose por bytes (limits.py: 15 s/MiB y 16 MiB/MiB), con errores de 15 a 300 veces (B2-01). |
| ✅ Resuelto | C-1. La ventana abre en inglés aunque se instaló en español | clearmd.iss:508-515 escribe language = "es" en la primera instalación cuando el asistente corrió en español (036 AC-07). |
| ✅ Resuelto | C-2. Word, Excel y PowerPoint antiguos con un genérico «formato no soportado» | es.toml:78 y :104 dan un motivo propio y la acción «guárdalo como .docx, .xlsx o .pptx» (036 AC-03). |

## 3. Lo que hay que proteger

Las fortalezas que ninguna mejora debe romper:

- Escrituras atómicas, PartStage y free_target «(2)»: nunca se pisa ni se deja a medias el trabajo.
- Los originales nunca se modifican, y la app lo repite donde importa.
- Un solo presentador para las tres ventanas, con descarte por generación y pausa del botón principal.
- Cada error con mensaje y acción en los dos idiomas, sin trazas técnicas, y catálogos separados para ventana y terminal.
- El lector de PDF propio, rápido y liviano con documentos reales.
- El resumen con titular humano, «Dónde Están Tus Archivos» y la separación entre «Necesita Tu Atención» y «Lo que ClearMD Limpió».
- El instalador liviano, la app en el idioma del instalador y los nombres de app pensados para el público (junta de dudas D1-D2).
- La vigilancia de dependencias pesadas y de tamaño en los ejecutables de la CI.
- Las capturas automáticas en los dos temas y los dos idiomas.

## 4. Las diez mejoras recomendadas

Ordenadas por valor para el cliente final frente al esfuerzo. Marca tu decisión en la última columna.

| # | Mejora | Por qué le importa a la persona | Esfuerzo | ¿Me acojo? |
| --- | --- | --- | --- | --- |
| 1 | **Que el texto entregado sea fiel: un solo decodificador para Convertir, Unir y Dividir, con la nota de codificación en lenguaje llano** | El público hispano recibe hoy actas y listas con «ańo» y «Núńez» reportadas como éxito. | pequeño | ☐ Sí ☐ No |
| 2 | **Cumplir la promesa de privacidad al reportar un fallo y dar un canal claro para hacerlo** | Evita que un nombre de paciente o de cliente termine en una página pública por confiar en el texto. | pequeño | ☐ Sí ☐ No |
| 3 | **Que «Dividir en N partes» entregue N partes o diga por qué no** | Es el propósito mismo de Dividir para una IA. | pequeño | ☐ Sí ☐ No |
| 4 | **La cancelación nunca es un «error inesperado», y un error real conserva la carpeta y la deja abrir** | Quien cancela o sufre un fallo sigue viendo dónde está lo ya hecho. | medio | ☐ Sí ☐ No |
| 5 | **Tablas y ecuaciones de PDF: unir las filas de continuación, marcar como dudosas las ecuaciones incoherentes y avisarlo en el resumen** | Son datos que la IA usará como verdaderos; ADR-0034 y ADR-0036 ya lo prometen. | medio | ☐ Sí ☐ No |
| 6 | **Estimar los PDF por páginas y no por bytes** | Se acaban los avisos falsos de «26 min», las ofertas de partir sin motivo y los escaneados omitidos en equipos de 4 GB. | medio | ☐ Sí ☐ No |
| 7 | **Acelerar la CI: limitar el gc.collect a las pruebas de ventana, y solo después paralelizar** | Responde a la pregunta del dueño. Cada arreglo llega antes a la gente: la CI debería bajar a menos de la mitad sin perder garantías. | pequeño | ☐ Sí ☐ No |
| 8 | **Mensajes que se pueden cumplir y que no se contradicen: acción de dividir según el formato, archivo vacío, subtítulo según el estado, botones reales, nota del Inicio, unión fallida en la CLI** | Cada mensaje falso hace dudar de todos los demás. | pequeño | ☐ Sí ☐ No |
| 9 | **Nombres de resultados estables y regla de imágenes en el backend** | La carpeta para la IA no se llena de duplicados ni de enlaces rotos. | medio | ☐ Sí ☐ No |
| 10 | **Arranque rápido: App Clásica en modo carpeta en el instalador, importaciones diferidas y tiempo de arranque medido en la CI** | La app recomendada abre en un segundo y no invita al doble clic. | medio | ☐ Sí ☐ No |

Los códigos de cada mejora (por ejemplo, B1-01) llevan a los hallazgos de la sección 8:

- **1.** B1-01, F4-07
- **2.** B4-01, F4-06, B4-05
- **3.** B1-02
- **4.** B1-03, F1-02
- **5.** B3-01, B3-02, B3-03
- **6.** B2-01
- **7.** B2-02, F2-07
- **8.** B4-02, B1-06, F1-07, F4-05, F4-04, F4-03, B3-05
- **9.** B1-05, B3-04, B1-04
- **10.** F2-01, B2-05, B2-04, F2-04, F2-02, B2-08

## 5. Lo que no conviene hacer

Propuestas que surgieron en las juntas y que, según la conciliadora, **añadirían complejidad o romperían algo**:

- No reabrir Title Case en español: es doctrina del dueño (ADR-0041), y F3-08 se retiró con razón.
- No sacar Resumen ni Imágenes del paso 1: lo fijan la spec 009 AC-10 y la 012. Basta cambiar la etiqueta.
- No agregar pytest-xdist antes de quitar el gc por prueba: reparte el costo y arriesga fallos intermitentes con Tk.
- No mantener vivo el proceso de conversión entre lotes: son ~107 MiB ociosos en equipos de 4 GB. Precalentar y cerrar.
- No retirar ni dejar «una versión atrás» a ninguna de las tres ventanas sin un ADR nuevo del dueño (ADR-0052).
- No borrar los marcadores del historial del resumen al limpiar el HTML (ADR-0016).
- No cambiar el resumen por defecto a PDF solo para esconder el HTML: suma un archivo y no arregla el Markdown.
- No pedir confirmación en cada Cancelar: basta confirmar el cierre con la X durante un lote.
- No usar documentos privados como pruebas fijas: usar PDF sintéticos o realistas.

## 6. Desacuerdos que quedan abiertos

- Severidad de la App Clásica en modo de un solo archivo: el debate la subió a alta y yo la dejo en media, porque ADR-0028 aceptó el costo, hay pantalla de carga y la cifra de 5 s viene de un registro que no revisé. Sigue siendo una recomendación clara para el instalador.
- B3-06: las mesas oscilan entre poner el PDF por defecto y dejar un Markdown puro. Ninguna advirtió que los marcadores del historial son funcionales (ADR-0016). Mi postura: quitar <details> y conservar o reemplazar los marcadores.
- F1-01: F1 pide confirmar al cerrar y también al cancelar; B4, F2 y F4 solo al cerrar. Me quedo con confirmar solo el cierre con la X durante un lote.
- «Resumen» frente a «Informe»: cambiar solo la etiqueta crea un desajuste con el archivo Resumen_ClearMD.md (B4). Propongo «Resumen del Proceso», que mantiene la palabra y quita la ambigüedad.
- F2-03, severidad de la lista de flet: F2 la pone en media y F1 en baja. Me quedo con baja hasta medir un lote realista en Flutter.
- B1-06: B4 pide media; la dejo en baja porque es poco frecuente, aunque el arreglo es trivial y debe ir en la misma tanda.

## 7. Cómo trabajaron las juntas

La conciliadora también auditó a las juntas y a su debate:

### Mesa Backend (B1 Lógica, B2 Eficiencia, B3 Experiencia de lo que entrega, B4 Claridad es cariño) — rigor 8,5/10

- **Lo que hizo bien:** Reprodujo casi todo con la CLI y con mediciones reales: cp1252, el reparto en N partes, los enlaces de imágenes rotos, los nombres que cambian con el idioma y el gc por prueba. Dos lentes llegaron por separado al mismo hallazgo y lo confirmaron (B1-01 y B3; B4-01 y F4). Cita los ADR y no los contradice sin explicar por qué. Fue la única mesa que miró la fidelidad del contenido entregado (tablas, ecuaciones, títulos) en documentos reales.
- **Lo que no vio:** Ninguna lente comprobó que la nota encoding_guessed nunca sale en el camino de Convertir (yo vi 0 notas en el resumen). B3-06 propone «Markdown puro, sin HTML» sin advertir que los marcadores <!-- clearmd:history --> son funcionales (writer.py:20-21, ADR-0016) y no se pueden quitar sin más. La parte de B3-08 sobre «faltan menos de un minuto» es débil: es un uso coloquial aceptado.
- **Donde se excedió:** B2-03 propone mantener vivo el proceso de conversión entre lotes, lo que deja ~107 MiB ociosos en equipos de 4 GB; la versión de F2-08 (precalentar al entrar en Revisar y cerrar después) es mejor. B3-06 propone el PDF por defecto, que suma un archivo más a cada carpeta. B3-09 propone una opción de marcas de página, que agrega un ajuste más para el público general.

### Mesa Frontend (F1 Lógica, F2 Eficiencia, F3 Estilo visual, F4 Claridad es cariño) — rigor 7,5/10

- **Lo que hizo bien:** Sondeó el presentador con una vista y un backend falsos (F1-02 y F1-06), sacó del registro de la CI el tiempo real de arranque en Windows (F2-01), calculó contrastes con la paleta real (F3-06) y revisó cada captura. Encontró promesas de texto que la pantalla contradice («Nada se escribe…», «Convierte más»).
- **Lo que no vio:** No conectó el error inesperado con la cancelación en Unir hasta la ronda 2. No probó qué ve la persona en la ventana con un archivo vacío ni con un texto en cp1252. F3-02 (foco en flet) no se vio renderizado: lo confirmé en el código (look.py no define FOCUSED), pero falta una captura. En F2-03 no se midió el lado de Flutter.
- **Donde se excedió:** F2-05 propone una ventana de referencia con las otras «una versión detrás», lo que reabre la decisión del dueño (ADR-0052) y crea versiones desiguales. F3-05 y la primera versión de F4-01 proponen sacar opciones del paso 1, contra la spec 009 AC-10 y la 012. F1-01 propone pedir confirmación también en el botón Cancelar, lo que añade fricción a un gesto deliberado. F3-08 proponía reabrir Title Case; se retiró bien.

### Debate (ronda 2, las dos mesas) — rigor 8/10

- **Lo que hizo bien:** Fusionó bien los duplicados (B2-05 con F2-01, B2-04 con F2-04, B2-02 con F2-07, F1-07 con F4-05, B1-05 con B3-04). Corrigió una causa mal atribuida (paralelismo frente a gc) con una medición nueva. Retiró F3-08 por la doctrina del dueño y la mitad de F4-01 por la spec 009 AC-10. No hizo desaparecer ningún hallazgo real.
- **Lo que no vio:** Algunas severidades subieron sin reverificar: B2-05 pasó a alta con reverified=false (el mecanismo lo confirmé; la cifra de 5 s viene de un registro que no revisé), y B1-06 se propuso como media sin un argumento nuevo. Nadie respondió de frente «cómo vamos y qué falta» frente a la primera auditoría.
- **Donde se excedió:** Una tendencia a sumar controles nuevos (confirmaciones, deshacer, «Más opciones», marcas de página, enlaces por carpeta) que, todos juntos, cargan la interfaz. Conviene priorizar las correcciones de verdad antes que los controles nuevos.

## 8. Hallazgos verificados

Son 27 hallazgos, ordenados por gravedad. **Veredicto:** ✅ confirmada · ◐ parcialmente cierta · ✖ refutada.

| Gravedad | Valor para el usuario | Esfuerzo | Veredicto | Hallazgo |
| --- | --- | --- | --- | --- |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [1. Un texto o CSV guardado en Windows (cp1252) pierde la «ñ» al Convertir o Unir, sin aviso](#h1) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [2. «Copiar Detalles» promete ocultar los nombres de los archivos y no lo cumple; además se pide adjuntar el resumen (que trae nombres) y abrir un «issue» con cuenta de GitHub](#h2) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [3. «Dividir en N partes» puede entregar una sola parte y reportarlo como éxito](#h3) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [4. En las tablas de un PDF, una celda escrita en varias líneas se parte en varias filas](#h4) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [5. Algunas ecuaciones de un PDF salen mal escritas y el resumen no avisa](#h5) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [6. La estimación de tiempo y memoria de los PDF, hecha por el tamaño en bytes, se equivoca muchísimo con PDF escaneados](#h6) |
| 🟠 Media | alto | medio | ✅ Confirmada | [7. Un error inesperado (también al cancelar mientras se arma el PDF unido) deja la pantalla vacía, sin resumen y sin carpeta que abrir](#h7) |
| 🟠 Media | alto | pequeño | ✅ Confirmada | [8. Varios errores mandan a «Dividir» archivos que Dividir no acepta](#h8) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [9. La CI tarda 20–24 min sobre todo por un gc.collect() que corre después de cada prueba (respuesta a la pregunta del dueño)](#h9) |
| 🟠 Media | medio | medio | ✅ Confirmada | [10. La App Clásica instalada se desempaca en cada apertura, y nadie mide el tiempo de arranque](#h10) |
| 🟠 Media | medio | medio | ✅ Confirmada | [11. Los nombres de los resultados no son estables: dependen del lote y del idioma, y dejan duplicados](#h11) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [12. En la CLI, Unir y Dividir con --images dejan enlaces a imágenes que no existen](#h12) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [13. Una unión fallida en la CLI no dice por qué y marca como fallido un archivo sano](#h13) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [14. Mientras convierte, el subtítulo sigue diciendo «Nada se escribe hasta que pulses Convertir»](#h14) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [15. Textos que nombran botones que no existen y una nota del Inicio que inquieta](#h15) |
| 🟠 Media | medio | medio | ✅ Confirmada | [16. «Dividir los PDF grandes» reemplaza la lista y guarda en silencio los ajustes de Dividir](#h16) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [17. Controles que no se ven como lo que son: Ajustes e Inicio parecen activos en flet mientras trabaja, y «Quitar Todo» se ve tan inofensivo como «Deseleccionar Todo»](#h17) |
| 🟠 Media | medio | medio | ◐ Parcial | [18. Las listas cortan el motivo de cada archivo y el final de la carpeta](#h18) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [19. La ventana y la CLI cargan al abrir las bibliotecas de PDF y Excel que solo usa el proceso de conversión](#h19) |
| 🟠 Media | medio | pequeño | ◐ Parcial | [20. El resumen en Markdown se ve con HTML (<details>, comentarios) si se abre en el Bloc de notas](#h20) |
| ⚪ Baja | bajo | medio | ◐ Parcial | [21. Espera fija de unos 1,4 s al pulsar Convertir porque el proceso de conversión arranca de cero](#h21) |
| ⚪ Baja | medio | pequeño | ✅ Confirmada | [22. Un archivo vacío se reporta como «dañado» (o como convertido y vacío)](#h22) |
| ⚪ Baja | medio | pequeño | ✅ Confirmada | [23. Jerga y plurales «(s)» en notas y en la terminal](#h23) |
| ⚪ Baja | medio | pequeño | ✅ Confirmada | [24. Documentación y ayuda de la terminal desactualizadas: README sin «clearmd-cli», ayuda a medias en español](#h24) |
| ⚪ Baja | medio | pequeño | ◐ Parcial | [25. Foco del teclado poco visible (flet sin estado de foco, ttk de 1 px) y colores derivados sin prueba de contraste](#h25) |
| ⚪ Baja | medio | pequeño | ◐ Parcial | [26. El paso 1 junta muchas decisiones y la etiqueta «Resumen» se confunde con resumir el documento](#h26) |
| ⚪ Baja | bajo | medio | ◐ Parcial | [27. Hallazgos menores y de pulido](#h27) |

<a id="h1"></a>

### 8.1 Un texto o CSV guardado en Windows (cp1252) pierde la «ñ» al Convertir o Unir, sin aviso

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B1-01, B3 debate, F4-07 (nota)*

- **Lo que siente la persona:** Le pasa a la IA un acta o una lista con «ańo», «seńores» o «Núńez», y el resumen le dice que todo salió bien. Dividir el mismo archivo da el texto correcto.
- **Recomendación:** Usar un solo decodificador (decode_source de Dividir) también para Convertir y Unir, antes de markitdown. Si el texto no es UTF-8, probar primero cp1252. Emitir la nota de codificación deducida en lenguaje llano («revisa que tildes y eñes se vean bien»). Agregar una prueba fija con un .txt y un .csv en cp1252.
- **Comprobación de la conciliadora:** Lo reproduje en el contenedor: un .txt en cp1252 dio «El ańo pasado los seńores Núńez y Peńa…», sin ninguna nota en Resumen_ClearMD.md. csv_dialect.py:18-22 usa from_bytes(data).best() sin preferencias.

<a id="h2"></a>

### 8.2 «Copiar Detalles» promete ocultar los nombres de los archivos y no lo cumple; además se pide adjuntar el resumen (que trae nombres) y abrir un «issue» con cuenta de GitHub

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B4-01, F4-06, B4-05*

- **Lo que siente la persona:** Confía en la promesa y publica en una página pública el nombre de un paciente o de un cliente. Si no sabe qué es un «issue», no reporta nada.
- **Recomendación:** Que el texto diga «Intentamos ocultar los nombres de tus archivos; revisa antes de enviarlo», como ya dice la terminal. Ocultar también los nombres de los archivos del lote, que el presenter conoce, y rutas con espacios hasta la comilla o el final de la línea. Una sola clave de catálogo «cómo reportar»: dónde reportar, copiar solo la línea técnica y nunca el resumen, con palabras simples. Pruebas con nombre suelto, nombre entre comillas y carpeta con espacios.
- **Comprobación de la conciliadora:** Ejecuté without_paths en el contenedor: «KeyError: 'Historia clinica Ana.pdf'» queda intacto y «D:\Clientes\Ana Ruiz\ClearMD_Output» queda como «<archivo> Ruiz\ClearMD_Output». La promesa está en es.toml:472 y «avísanos y adjunta el resumen» en es.toml:17.

<a id="h3"></a>

### 8.3 «Dividir en N partes» puede entregar una sola parte y reportarlo como éxito

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B1-02*

- **Lo que siente la persona:** Pide 3 partes para que el texto quepa en una IA y recibe el archivo entero, como «parte 1 de 1», sin ninguna advertencia.
- **Recomendación:** Garantizar N partes cuando hay al menos N unidades: forzar cortes o bajar a párrafos cuando una sección pesa más que su parte. Si de verdad no se puede, decirlo en el resumen. Agregar pruebas con el peso al principio y al final.
- **Comprobación de la conciliadora:** Ejecuté balanced_cuts([5,5,10000],3) en el contenedor: devuelve []. El reparto voraz de text_cut.py:32-41 solo corta al alcanzar el objetivo proporcional.

<a id="h4"></a>

### 8.4 En las tablas de un PDF, una celda escrita en varias líneas se parte en varias filas

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B3-01*

- **Lo que siente la persona:** La tabla se ve bien, pero un registro aparece repartido en 5 a 8 filas, y ni la persona ni la IA saben qué dato va con cuál.
- **Recomendación:** Unir a la fila anterior las filas de continuación (primera celda vacía que sigue el texto de arriba). Agregar una prueba fija con un PDF sintético de celdas de varias líneas, no con un documento privado.
- **Comprobación de la conciliadora:** Conté sin leer el contenido: las salidas de dos PDF reales tienen 84 y 60 filas que empiezan con la primera celda vacía. Eso contradice ADR-0034:25. Algunas de esas filas podrían ser celdas combinadas legítimas, pero el volumen confirma el patrón.

<a id="h5"></a>

### 8.5 Algunas ecuaciones de un PDF salen mal escritas y el resumen no avisa

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B3-02*

- **Lo que siente la persona:** Cita o razona con una fórmula que parece correcta y no lo es (un denominador que se volvió «1»).
- **Recomendación:** Detectar los patrones incoherentes (\frac{…}{1} dentro de \underset, un exponente que termina en «+») y tratar esas ecuaciones como dudosas, como ya prevé ADR-0036. Agregar al resumen una nota de que las ecuaciones de un PDF se reconstruyeron y conviene revisarlas.
- **Comprobación de la conciliadora:** En la salida de un PDF real encontré 3 coincidencias de frac{…}{1}}. No comparé con la página original renderizada; tomo esa parte de B3.

<a id="h6"></a>

### 8.6 La estimación de tiempo y memoria de los PDF, hecha por el tamaño en bytes, se equivoca muchísimo con PDF escaneados

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B2-01*

- **Lo que siente la persona:** Ve «puede tardar 26 min y detenerse», más una oferta de partir el archivo, para algo que tarda segundos. En un equipo de 4 GB, un escaneado grande se omite sin intentarlo.
- **Recomendación:** Estimar los PDF por páginas (PDFium las cuenta en milisegundos) y por una muestra de caracteres. Estimar la memoria como unas 3,5 veces el tamaño más una cantidad por página. Recalibrar el benchmark 001 con PDF de texto, de imágenes y escaneados. No dar el aviso cuando casi no hay texto.
- **Comprobación de la conciliadora:** Comprobé limits.py: PDF a 15 s/MiB y 16 MiB/MiB, y planning.py:158 compara la estimación con worker_memory. No volví a medir los tiempos reales; 036 AC-06 solo corrigió el caso de Excel.

<a id="h7"></a>

### 8.7 Un error inesperado (también al cancelar mientras se arma el PDF unido) deja la pantalla vacía, sin resumen y sin carpeta que abrir

*🟠 Media · valor alto · esfuerzo medio · ✅ Confirmada · B1-03, F1-02*

- **Lo que siente la persona:** Canceló a propósito y la app le dice «error inesperado». No ve lo que ya se hizo y el botón para abrir la carpeta está apagado: cree que perdió todo.
- **Recomendación:** En el backend, atrapar Cancelled en merging._write y devolver CANCELLED, para que el resumen se escriba. En el presenter, distinguir Cancelled de un error real, y ante un error conservar result_folders y llevar a la persona a Resultados con «Copiar Detalles» disponible.
- **Comprobación de la conciliadora:** Lo verifiqué en el código: _write (merging.py:179-182) solo atrapa ConversionError y OSError; page_runner.merge_pdfs → processes.py:114 lanza Cancelled; conversion.py hace `except Exception` → unexpected(), que pone plan=None, report=None y READY (reset.py:25-36). No reproduje la carrera de tiempos.

<a id="h8"></a>

### 8.8 Varios errores mandan a «Dividir» archivos que Dividir no acepta

*🟠 Media · valor alto · esfuerzo pequeño · ✅ Confirmada · B4-02*

- **Lo que siente la persona:** Sigue el consejo, Dividir lo rechaza y le dice «Conviértelo», que es justo lo que falló. Queda en un círculo.
- **Recomendación:** Que la acción dependa del formato, con dos variantes de clave elegidas por el presenter o por la CLI: «Divídelo» para PDF, Markdown, texto, CSV y Excel; «guárdalo como PDF desde su programa» para los demás.
- **Comprobación de la conciliadora:** es.toml:33, 37, 49, 86 y 96 sugieren dividir sin importar el formato, frente a :98 not_splittable. La bajo de alta a media porque un timeout de un .docx es raro; el skip por tamaño de un .pptx o .html grande sí es plausible.

<a id="h9"></a>

### 8.9 La CI tarda 20–24 min sobre todo por un gc.collect() que corre después de cada prueba (respuesta a la pregunta del dueño)

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B2-02, F2-07*

- **Lo que siente la persona:** Indirecto: cada arreglo espera más de 20 min antes de poder publicarse. La publicación (6–9 min) sí es normal.
- **Recomendación:** Primero, mover el gc.collect a un conftest solo de las pruebas de ventana (tests/gui, tests/unit/frontend). Luego, volver a medir. Solo después, valorar pytest-xdist y una matriz escalonada (Linux 3.14 en cada push y la matriz completa en PR, main y etiquetas). Subir siempre el JUnit.
- **Comprobación de la conciliadora:** Lo medí yo: tests/unit/i18n/test_catalog.py tarda 27,4 s con el gc y 7,7 s sin él (gc.collect anulado). El fixture está en tests/conftest.py:59-64.

<a id="h10"></a>

### 8.10 La App Clásica instalada se desempaca en cada apertura, y nadie mide el tiempo de arranque

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · B2-05, F2-01, B2-08, F2-02*

- **Lo que siente la persona:** Espera unos 5 s con la pantalla de carga en cada doble clic, y puede volver a hacer doble clic y abrir dos copias.
- **Recomendación:** Que el instalador ponga la App Clásica en modo carpeta, como ya hace con Qt y flet, y dejar el .exe de un solo archivo solo para la descarga portátil. Hay que ajustar ADR-0028 y ADR-0040: con instalador, su razón ya no aplica a la copia instalada. Cronometrar --smoke en la CI, con aviso por encima de 3 s.
- **Comprobación de la conciliadora:** Verifiqué que clearmd.spec:4-5 describe programas de un solo archivo y que clearmd.iss:211 instala ese ClearMD.exe, mientras Qt y flet se instalan como carpeta. La cifra de 5 s sale del registro de la CI, que no revisé. La bajo a media: ADR-0028 ya aceptó ese costo, y hay pantalla de carga.

<a id="h11"></a>

### 8.11 Los nombres de los resultados no son estables: dependen del lote y del idioma, y dejan duplicados

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · B1-05, B3-04*

- **Lo que siente la persona:** Su carpeta para la IA termina con «informe.md» viejo junto a «informe (pdf).md», o con 50 partes mezcladas en dos idiomas, y «Sobrescribir» no lo evita.
- **Recomendación:** Un solo contrato: el nombre de un resultado depende solo de su original. Sufijos y patrones de nombre fijos en todos los idiomas, como ADR-0016 ya hace con el resumen, o reconocer los de ambos idiomas al sobrescribir. Avisar de los resultados huérfanos.
- **Comprobación de la conciliadora:** Lo vi en el código: api/__init__.py:146 toma images.suffix del catálogo del idioma, y es.toml:570, 574 y 642 definen sufijo, part_name y el nombre de la unión. No reproduje el caso del lote; tomo la reproducción de B1.

<a id="h12"></a>

### 8.12 En la CLI, Unir y Dividir con --images dejan enlaces a imágenes que no existen

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B1-04*

- **Lo que siente la persona:** Quien usa la terminal recibe un Markdown con imágenes rotas y un «2 unidos» sin advertencia.
- **Recomendación:** Aplicar images solo en Convertir dentro de run_batch, para que la regla viva en el backend y valga para las cuatro interfaces.
- **Comprobación de la conciliadora:** api/__init__.py:145-152 asigna images a todo el plan antes de elegir entre merge y split; el presenter lo filtra (conversion.py:70) y la CLI no. No lo ejecuté.

<a id="h13"></a>

### 8.13 Una unión fallida en la CLI no dice por qué y marca como fallido un archivo sano

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B3-05*

- **Lo que siente la persona:** Ve «1 con error» sin razón en pantalla, y en el resumen aparece un ❌ junto a un archivo que estaba bien.
- **Recomendación:** Que el plan detecte que hay menos de dos documentos y la CLI salga con exit 2 y un mensaje claro. Imprimir las fallas de la unión con su razón.
- **Comprobación de la conciliadora:** merging.py:167 decide NOTHING_TO_MERGE después de convertir todo y marca FAILED a los convertidos (:191-196). El texto «document(s)» está en esa misma línea.

<a id="h14"></a>

### 8.14 Mientras convierte, el subtítulo sigue diciendo «Nada se escribe hasta que pulses Convertir»

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F1-07, F4-05*

- **Lo que siente la persona:** La frase que debería tranquilizar contradice a la barra de progreso.
- **Recomendación:** Que header_of elija el subtítulo según el estado (antes, durante y después), con una prueba que recorra cada estado.
- **Comprobación de la conciliadora:** header.py:30 usa siempre gui.page.{step}_subtitle; el estado solo cambia la línea superior.

<a id="h15"></a>

### 8.15 Textos que nombran botones que no existen y una nota del Inicio que inquieta

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F4-04, F4-03*

- **Lo que siente la persona:** Busca un botón «Convierte más» que no está, y lee «Las herramientas cambian archivos», que suena a que van a tocar sus documentos.
- **Recomendación:** Interpolar el nombre del botón real, «¿Qué Sigue?». Reescribir la nota del Inicio: «Tus originales nunca se modifican: ClearMD crea archivos nuevos en ClearMD_Output». Agregar una prueba que no permita nombres de botón escritos a mano.
- **Comprobación de la conciliadora:** es.toml:488, 491, 627, 629, 672 y 674 («Convierte/Divide/Une más») y :586 files_note.

<a id="h16"></a>

### 8.16 «Dividir los PDF grandes» reemplaza la lista y guarda en silencio los ajustes de Dividir

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · F1-03*

- **Lo que siente la persona:** Los otros 28 documentos desaparecen de la lista y sus preferencias de Dividir cambian sin aviso.
- **Recomendación:** Aplicar el número de partes solo esta vez, sin guardarlo como preferencia, y ofrecer en «¿Qué Sigue?» volver a la lista original.
- **Comprobación de la conciliadora:** tools.py:51-54: s.inputs se reemplaza por los PDF grandes y save() persiste split_cut, split_parts y split_keep.

<a id="h17"></a>

### 8.17 Controles que no se ven como lo que son: Ajustes e Inicio parecen activos en flet mientras trabaja, y «Quitar Todo» se ve tan inofensivo como «Deseleccionar Todo»

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F1-04, F3-10, F1-05*

- **Lo que siente la persona:** Un clic sin respuesta parece un cuelgue, y un clic desviado borra el orden que armó para Unir.
- **Recomendación:** En flet, aplicar el estilo deshabilitado también al contenido del riel. Dar a «Quitar Todo» un tono de advertencia, separarlo y ofrecer deshacer durante unos segundos. Agregar una prueba de paridad por estado.
- **Comprobación de la conciliadora:** look.py solo define DISABLED en algunos estilos. La comparación de las capturas 018/3 y 016/3 la tomo de F1 y F3; rail.py la citan dos lentes.

<a id="h18"></a>

### 8.18 Las listas cortan el motivo de cada archivo y el final de la carpeta

*🟠 Media · valor medio · esfuerzo medio · ◐ Parcial · F3-01*

- **Lo que siente la persona:** Para saber por qué se omite cada archivo tiene que seleccionarlo fila por fila, y todas las carpetas se ven iguales.
- **Recomendación:** En Revisar, poner el motivo como segunda línea bajo el nombre. Recortar las rutas por el principio («…\Documentos\Tesis»). Hacerlo en flet junto con la reutilización de filas (F2-03).
- **Comprobación de la conciliadora:** La 035 AC-05 ya muestra el motivo completo de la fila seleccionada debajo de la lista, así que no se pierde información. Por eso queda en media y no en alta. file_list.py corta por el final.

<a id="h19"></a>

### 8.19 La ventana y la CLI cargan al abrir las bibliotecas de PDF y Excel que solo usa el proceso de conversión

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B2-04, F2-04*

- **Lo que siente la persona:** Cada apertura y cada «--version» tardan alrededor de medio segundo más.
- **Recomendación:** Importar de forma diferida worker.pages, worker_main y pdf_report. Agregar una prueba de arquitectura que falle si openpyxl o pypdfium2 aparecen en sys.modules tras importar cada interfaz.
- **Comprobación de la conciliadora:** Dos lentes llegaron a la misma cadena por métodos distintos. No ejecuté importtime; lo acepto por esa coincidencia.

<a id="h20"></a>

### 8.20 El resumen en Markdown se ve con HTML (<details>, comentarios) si se abre en el Bloc de notas

*🟠 Media · valor medio · esfuerzo pequeño · ◐ Parcial · B3-06*

- **Lo que siente la persona:** La pieza más cuidada se ve como código.
- **Recomendación:** Quitar <details> y <summary> (detalle técnico en una línea normal e historial al final), pero conservar los marcadores del historial, que son funcionales (ADR-0016), o cambiarlos por una línea de texto equivalente. No cambiar el valor por defecto a PDF.
- **Comprobación de la conciliadora:** writer.py:117-123 y :145 generan <details>. Los marcadores HISTORY_START y HISTORY_END (:20-21) sirven para reconstruir el historial: «sin HTML» no puede significar borrarlos.

<a id="h21"></a>

### 8.21 Espera fija de unos 1,4 s al pulsar Convertir porque el proceso de conversión arranca de cero

*⚪ Baja · valor bajo · esfuerzo medio · ◐ Parcial · B2-03, F2-08*

- **Lo que siente la persona:** La barra tarda un momento en moverse justo cuando la persona mira si funcionó.
- **Recomendación:** Precalentar el proceso al entrar en Revisar y entregárselo a la conversión; cerrarlo al terminar (no dejarlo vivo entre lotes). Actualizar worker_startup_seconds=0.7.
- **Comprobación de la conciliadora:** limits.py:81 dice 0.7 s, contra 1,4 s medidos por B2. Las mejoras de importación diferida (B2-04) y el modo carpeta reducen parte de esta espera.

<a id="h22"></a>

### 8.22 Un archivo vacío se reporta como «dañado» (o como convertido y vacío)

*⚪ Baja · valor medio · esfuerzo pequeño · ✅ Confirmada · B1-06*

- **Lo que siente la persona:** Se le pide abrir y volver a guardar un archivo que en realidad no tiene nada.
- **Recomendación:** Comprobar el tamaño 0 antes de convertir y usar EMPTY_FILE («está vacío; revisa que se haya descargado bien»).
- **Comprobación de la conciliadora:** Reproducido: vacio.pdf aparece en el resumen como «Este archivo parece estar dañado…».

<a id="h23"></a>

### 8.23 Jerga y plurales «(s)» en notas y en la terminal

*⚪ Baja · valor medio · esfuerzo pequeño · ✅ Confirmada · B3-07, F4-07, B3-08*

- **Lo que siente la persona:** «StarMath», «cambios rastreados», «lote» y «resultado(s)» suenan a máquina.
- **Recomendación:** Una pasada de catálogo: plurales con .one/.other, «control de cambios», la cantidad al principio de cada nota, y una prueba que no permita «(s)» ni una lista corta de jerga.
- **Comprobación de la conciliadora:** es.toml:122, 140, 146, 147, 160, 272, 276, 278 y 309. La parte «faltan menos de un minuto» de B3-08 la refuto: es un uso aceptado.

<a id="h24"></a>

### 8.24 Documentación y ayuda de la terminal desactualizadas: README sin «clearmd-cli», ayuda a medias en español

*⚪ Baja · valor medio · esfuerzo pequeño · ✅ Confirmada · B4-03, B4-04, B4-06*

- **Lo que siente la persona:** Copia un ejemplo del README y Windows le dice que el comando no existe.
- **Recomendación:** Explicar en el README los dos nombres del comando, tomar prog de sys.argv[0], traducir los rótulos de argparse y comprobar los ejemplos con una prueba.
- **Comprobación de la conciliadora:** grep de «clearmd-cli» en README.md y README.es.md: 0 resultados; parser.py:14 tiene prog="clearmd" fijo.

<a id="h25"></a>

### 8.25 Foco del teclado poco visible (flet sin estado de foco, ttk de 1 px) y colores derivados sin prueba de contraste

*⚪ Baja · valor medio · esfuerzo pequeño · ◐ Parcial · F3-02, F3-03, F3-06*

- **Lo que siente la persona:** Quien navega con el teclado no sabe dónde está.
- **Recomendación:** Un estado de foco de 2 px en flet y Qt, distinto del estado bajo el puntero. Extender test_brand a los colores mezclados. Agregar capturas con foco.
- **Comprobación de la conciliadora:** grep de FOCUSED o focus en flet/visuals/look.py: 0 resultados. Nadie lo vio renderizado, y el público principal usa ratón; por eso queda en baja.

<a id="h26"></a>

### 8.26 El paso 1 junta muchas decisiones y la etiqueta «Resumen» se confunde con resumir el documento

*⚪ Baja · valor medio · esfuerzo pequeño · ◐ Parcial · F3-05, F4-01*

- **Lo que siente la persona:** Cree que ClearMD va a resumir su documento.
- **Recomendación:** Cambiar solo la etiqueta de la ventana, por ejemplo «Resumen del Proceso» (coherente con el archivo Resumen_ClearMD.md), y alinear las etiquetas de grupo. No sacar opciones del paso 1: lo fija la spec 009 AC-10 y es decisión del dueño.
- **Comprobación de la conciliadora:** es.toml:561 dice «Resumen:»; la spec 009 AC-10 pone el formato en el paso 1 a propósito.

<a id="h27"></a>

### 8.27 Hallazgos menores y de pulido

*⚪ Baja · valor bajo · esfuerzo medio · ◐ Parcial · B1-07, B1-08, B2-09, B2-06, B2-07, F2-03, F2-06, F1-01, F1-06, F1-08, B3-03, B3-09, B3-10, B4-07, B4-08, B4-09, B4-10, F3-04, F3-07, F3-09, F4-02, F4-08, F4-09, F4-10, F2-05*

- **Lo que siente la persona:** Detalles que restan pulido o que solo ocurren en casos raros.
- **Recomendación:** Atenderlos en lote después de los principales. F1-01: confirmar solo al cerrar con la X durante un lote. B1-07: limpiar solo los temporales con cierta antigüedad. B3-03: no convertir en título una línea larga sin puntuación final. F2-05: no reabrir ADR-0052.
- **Comprobación de la conciliadora:** Revisé al azar F1-08 (pyside inputs.py:33 empieza en Ctrl+1: confirmado), B3-03 (13 títulos #### en la salida de un PDF real: confirmado) y F2-03 (show_rows reconstruye todas las filas: confirmado). B1-07, B1-08 y F2-03 en Flutter no se han reproducido.

## 9. Los informes de cada auditor (tras el debate)

### Backend · Lógica — 7/10

Mantengo el veredicto de la ronda 1. El backend protege bien los archivos: escrituras atómicas, partes que se escriben aparte, uniones que nunca reemplazan un archivo y fallas típicas explicadas con una acción. Lo que falla es la promesa de que lo que dice ClearMD es verdad. Un texto o CSV de Windows (cp1252) pierde la «ñ» sin aviso. «Dividir en N partes» puede entregar una sola parte. Cancelar durante el paso final de Unir termina en «error inesperado» y, según F1-02, la pantalla además se queda sin resultados. Las imágenes de Unir y Dividir en la terminal quedan como enlaces rotos. Y los nombres de salida no son estables: dependen del lote y, según B3-04, también del idioma. El debate reforzó tres hechos que verifiqué en el código. La estimación de memoria de los PDF (B2-01) puede omitir un archivo sano en un equipo de 4 GB. «Copiar Detalles» deja pasar nombres (B4-01). Una unión con un solo documento se descubre al final y marca como fallido un archivo sano (B3-05). Sobre la pregunta del dueño: la publicación (6–9 min) es razonable. La CI (20–24 min) no lo es, y la causa principal medida es un gc.collect() después de cada prueba (B2-02), más que la falta de paralelismo. Nota: 7/10.

**Fortalezas que vio:**

- Escrituras atómicas y seguras: archivo temporal con nombre aleatorio, os.replace y revisión de cada carpeta sin seguir enlaces (output_files.py). Un corte de luz no deja resultados a medias.
- PartStage: las partes nuevas se escriben aparte y las de un corte anterior solo se retiran cuando todas las nuevas están listas. Una cancelación deja intacto el trabajo anterior.
- Unir nunca reemplaza un archivo existente: free_target agrega «(2)», «(3)»… Una unión cancelada antes del paso final se informa como cancelada (merging.py, el chequeo de cancel.is_set() en _write).
- Las fallas típicas llegan claras y con una acción: con contraseña, dañado y escaneado sin texto, este último con las páginas exactas.
- Los choques de nombres se resuelven sin distinguir mayúsculas ni forma Unicode, y las rutas con espacios, tildes y «#» funcionan en los enlaces de imágenes.
- El límite de tiempo se cuenta desde el último avance: un archivo largo que avanza termina, y uno trabado se detiene y se informa como «detenido».
- Dividir decodifica bien el texto (decode_source con cp1252 y preferencias en empate): es el modelo que debe seguir Convertir.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B1-01 | 🔴 Alta | pequeño | alta | Los textos y CSV en codificación de Windows (cp1252) pierden la «ñ» al Convertir o Unir, sin aviso |
| B1-02 | 🔴 Alta | pequeño | alta | «Dividir en N partes» puede entregar una sola parte, sin avisar |
| B1-03 | 🟠 Media | pequeño | alta | Cancelar mientras se arma el PDF unido termina en «error inesperado», sin resumen y con la pantalla vacía |
| B1-04 | 🟠 Media | pequeño | alta | En la línea de comandos, Unir y Dividir con imágenes dejan enlaces rotos y mezclados |
| B1-05 | 🟠 Media | medio | alta | Los nombres de los resultados no son estables entre ejecuciones: dependen de qué otros archivos vienen en el lote (y del idioma, ver B3-04) |
| B1-06 | ⚪ Baja | pequeño | alta | Un archivo vacío se reporta como «dañado», o como convertido y vacío, según el formato |
| B1-07 | ⚪ Baja | medio | media | Dos ClearMD abiertos sobre la misma carpeta pueden borrarse el trabajo en curso |
| B1-08 | ⚪ Baja | medio | media | Unir en un PDF no calcula de antemano la memoria del total |

<details><summary>Detalle técnico y evidencia</summary>

- **B1-01 — Los textos y CSV en codificación de Windows (cp1252) pierden la «ñ» al Convertir o Unir, sin aviso**
  - *Impacto:* Un .txt o .csv guardado en Windows «a la antigua» (actas, exportaciones contables, listas de Excel) sale con «ańo», «seńores» o «Núńez», y el resumen dice «convertido» sin ninguna nota. La persona le pasa a la IA un texto alterado sin enterarse. Dividir el mismo archivo sale bien, así que el mismo documento da resultados distintos según la herramienta.
  - *Evidencia:* Reproducido con la CLI en el contenedor: un .txt y un .csv en cp1252 dan U+0144 (charset_normalizer eligió cp1250), con «2 converted · 0 failed» y sin notas. `--merge markdown` da lo mismo, y `--split-words 500` sale correcto. Causa: services/conversion/csv_dialect.py:18-22 usa from_bytes(data).best() sin preferencias, mientras Dividir usa tex/source.py:42-66 decode_source. Un caso corto («café señor») terminó con U+FFFD. La nota encoding_guessed existe en el catálogo, pero no se emitió en este caso.
  - *Recomendación:* Usar un solo decodificador para todo el producto (decode_source), aplicado antes de markitdown y reescribiendo el texto como UTF-8. Si el texto no es UTF-8, probar primero cp1252. Dejar la nota «se dedujo la codificación» en lenguaje llano (ver F4-07). Agregar a las pruebas un texto y un CSV en cp1252 con ñ y tildes.
- **B1-02 — «Dividir en N partes» puede entregar una sola parte, sin avisar**
  - *Impacto:* Una persona pide 3 partes de un libro (portada corta, índice corto y un capítulo largo) para que quepa en una IA. Recibe «parte 1 de 1», del mismo tamaño que el original, y el resumen no advierte nada. Con un Excel de dos hojas pequeñas y una grande pasa lo mismo.
  - *Evidencia:* CLI: `--split-parts 3` sobre un .md de 3 secciones (2, 1 y unas 1.500 palabras) dio una sola parte; con 4 partes dio 4. text_cut.balanced_cuts([5,5,10000],3) da [], y cut_xlsx lo usa, contra su docstring. Causa: el reparto voraz de markdown_cut._into (72-90) y balanced_cuts (32-41) solo corta al alcanzar el objetivo proporcional.
  - *Recomendación:* Garantizar N partes cuando hay al menos N unidades: forzar cortes o bajar a párrafos si una sección pesa más que su parte. Si no se puede, avisarlo en el resumen. Agregar pruebas con el peso al final y al principio.
- **B1-03 — Cancelar mientras se arma el PDF unido termina en «error inesperado», sin resumen y con la pantalla vacía**
  - *Impacto:* Si la persona pulsa Cancelar justo cuando se pegan las páginas del PDF final, ve un error inesperado en vez de «cancelado», y no se escribe el Resumen_ClearMD. Como el error inesperado además borra de la pantalla lo ya hecho (F1-02), parece que el programa se rompió y que se perdió todo.
  - *Evidencia:* Re-verificado en ronda 2: merging.py:171 llama a cutter.merge_pdfs(..., cancel) dentro de _write, que solo atrapa ConversionError y OSError (líneas 180-183). Cancelled (schemas/errors.py:82) hereda de Exception. El bucle principal sí lo atrapa (línea 123), pero el paso final no. Sale por run_batch hasta el `except Exception` del presenter, que llama a unexpected() (intents/reset.py). No reproduje la carrera de tiempos.
  - *Recomendación:* Atrapar Cancelled en _write y devolver CANCELLED, igual que el chequeo previo, para que el resumen se escriba. Como regla general, que run_batch nunca deje escapar Cancelled. Agregar una prueba de cancelación en el paso final.
- **B1-04 — En la línea de comandos, Unir y Dividir con imágenes dejan enlaces rotos y mezclados**
  - *Impacto:* Con `--images`, o con «imágenes en carpeta» en la configuración compartida, el Markdown unido o dividido apunta a imágenes que nunca se guardaron, y todas las partes apuntan a la misma «image-001.png». El resumen no advierte nada.
  - *Evidencia:* `--merge markdown --images a.odt b.odt` da «2 merged», con enlaces a una carpeta _images que no existe. Pasa lo mismo con `--split-parts 2 --keep both --images`. Causa: api/__init__.py:139-146 aplica images a todo el plan. _piece (merging.py:96-104) y splitting._pdf descartan result.images. El presenter lo filtra (intents/conversion.py:70); la CLI no.
  - *Recomendación:* Mover la regla al backend: en run_batch, aplicar images solo en Convertir. Agregar una prueba de la CLI con --images y --merge o --split.
- **B1-05 — Los nombres de los resultados no son estables entre ejecuciones: dependen de qué otros archivos vienen en el lote (y del idioma, ver B3-04)**
  - *Impacto:* Una persona convierte informe.pdf (sale informe.md), luego agrega informe.docx y reconvierte con «Reemplazar si el original cambió». Le quedan informe (pdf).md, informe (docx).md y el viejo informe.md, que nadie actualiza. El PDF sin cambios se reconvirtió. Si cambia de idioma pasa lo mismo con imágenes, partes y uniones (B3-04). La carpeta que se le pasa a la IA se llena de duplicados y «Sobrescribir» no protege.
  - *Evidencia:* Reproducido en ronda 1: `clearmd in/` y luego `cp sample.docx in/informe.docx; clearmd --changed in/` dan «2 converted» y tres .md. paths.resolve_names (72-107) etiqueta solo los choques del lote actual. Re-verificado en ronda 2 para el idioma: api/__init__.py:139 toma el sufijo de imágenes de load_catalog(language), y part_name y el nombre de la unión salen del catálogo (es.toml:570, 574, 642).
  - *Recomendación:* Un contrato único: el nombre de salida de un original depende solo de ese original, nunca del lote ni del idioma. Concretamente: fijar sufijos y patrones de nombre independientes del idioma, como ADR-0016 ya hace con el resumen, o reconocer los de ambos idiomas. Mantener el nombre que el resumen anterior atribuye a un original y etiquetar solo al recién llegado. Como mínimo, avisar de resultados huérfanos. Evaluarlo junto con ADR-0048.
- **B1-06 — Un archivo vacío se reporta como «dañado», o como convertido y vacío, según el formato**
  - *Impacto:* A un .pdf o .docx de 0 bytes (una descarga fallida) se le dice que «parece dañado» y que lo abra en su programa y guarde una copia, algo imposible. Un .txt vacío se «convierte» en un .md vacío sin aviso.
  - *Evidencia:* CLI con --lang es: empty.pdf y empty.docx dan «Este archivo parece estar dañado…», y empty.txt da un .md de 0 bytes contado como convertido. ErrorCode.EMPTY_FILE solo se usa al Dividir.
  - *Recomendación:* Revisar el tamaño 0 (o un texto sin contenido) antes de convertir, en todas las herramientas, y usar EMPTY_FILE con su mensaje propio.
- **B1-07 — Dos ClearMD abiertos sobre la misma carpeta pueden borrarse el trabajo en curso**
  - *Impacto:* Abrir la app dos veces es fácil: con la App Clásica tarda unos 5 s en abrir (F2-01) y la persona vuelve a hacer doble clic. Al arrancar el lote, la segunda copia borra los temporales y las partes en preparación de la primera: la primera falla al guardar o pierde partes ya listas.
  - *Evidencia:* execution._root_problem (47-57) llama a sweep_temporary_files, que borra todo *.clearmd-tmp y lo marcado como STAGED sin revisar su antigüedad (output_files.py:136-156). No hay bloqueo de instancia única. PartStage.commit omite en silencio las partes que faltan. No lo reproduje.
  - *Recomendación:* Un archivo de bloqueo por ClearMD_Output mientras corre un lote, o limpiar solo los temporales antiguos. En commit, distinguir la parte que se retiró a propósito de la que falta.
- **B1-08 — Unir en un PDF no calcula de antemano la memoria del total**
  - *Impacto:* Al unir muchos PDF pesados, todo el resultado se arma en memoria y pasa entero entre procesos. Si supera el límite del trabajador, todo termina «detenido por memoria» después de esperar el proceso completo.
  - *Evidencia:* split/pdf_pages.py:44-58 arma el documento en un BytesIO y lo devuelve como bytes. planning revisa la memoria archivo por archivo y nunca el total. Unir no envía avances. Lo deduje del código; no lo medí. Nota: B2-01 muestra que la memoria real de PDFium por MiB es mucho menor que la estimada, lo que hace este caso menos probable.
  - *Recomendación:* En el plan de Unir a PDF, sumar los tamaños y avisar si el total supera la memoria del trabajador, o guardar el PDF unido en un temporal dentro del trabajador.

</details>

### Backend · Eficiencia — 6,5/10

Después del debate mantengo el diagnóstico. El motor de conversión es rápido: un PDF real de 86 páginas se lee en unos 2 s y partir un PDF de 108 MB tarda 3,5 s. La lentitud que nota la persona viene de tres sitios. (1) Arrancar cuesta: la App Clásica instalada se desempaqueta en cada apertura. Mi colega de Frontend lo midió en la CI de Windows: unos 5 s, frente a ~1,2 s de las otras dos apps. A eso se suma que la ventana carga bibliotecas que no usa y que el proceso de conversión arranca de cero (1,4 s) en cada lote. (2) La estimación de tiempo y memoria de los PDF se calcula por el tamaño del archivo. Por eso un PDF escaneado aparece como «unos 58 min, puede detenerse» cuando tarda 0,2 s, y en un equipo de 4 GB se omitiría sin intentarlo. (3) Unir varios PDF arma el resultado entero en memoria, sin un chequeo previo del total. Respuesta a la pregunta del dueño: la publicación (6–9 min) es razonable para 4 ejecutables y 3 instaladores probados. La CI (20–24 min) no lo es. Medí que un gc.collect() que corre después de cada una de las ~3.472 pruebas se lleva cerca del 75 % del tiempo, y quitarlo es el arreglo más barato y de mayor efecto, antes incluso que paralelizar. Nota: 6,5/10.

**Fortalezas que vio:**

- El lector de PDF propio (PDFium + limpieza) es rápido y liviano con documentos reales: 86 páginas en ~2 s con 45 MiB de memoria máxima. No hay que perderlo.
- Un solo proceso de conversión ordenado de barato a caro, con cancelación real (se mata el proceso) y límites de tiempo y memoria; el límite de tiempo se cuenta desde el último avance (ADR-0015, ADR-0050).
- Ejecutables livianos vigilados: la CI falla si numpy, pandas, onnxruntime o magika se cuelan, y los instaladores tienen tope de tamaño (packaging/check_executables.sh, ADR-0052).
- Partir y unir PDF es eficiente: un PDF de 108 MB en 4 partes tarda 3,5 s en total, arranque incluido.
- Benchmarks reproducibles con script y datos crudos (docs/benchmarks/*.json).
- Defensa contra bombas ZIP que lee solo el índice, sin descomprimir: protección sin costo de tiempo.
- Con la ventana quieta no se consume CPU: no hay sondeos inútiles, y los archivos pequeños no pagan la espera de 0,1 s.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B2-01 | 🔴 Alta | medio | alta | La estimación de tiempo y memoria de los PDF, basada en el tamaño del archivo, se equivoca entre 15 y 300 veces con documentos reales y escaneados |
| B2-05 | 🔴 Alta | medio | media | La App Clásica instalada se desempaqueta cada vez que se abre: tarda unos 5 s, frente a ~1,2 s de las otras dos |
| B2-02 | 🟠 Media | pequeño | alta | Las pruebas tardan 4–5 veces más de lo necesario por un gc.collect() que corre después de cada prueba |
| B2-03 | 🟠 Media | medio | alta | El proceso de conversión arranca de cero en cada lote (1,4 s), carga todos los conversores y solo empieza cuando la persona pulsa Convertir |
| B2-04 | 🟠 Media | pequeño | alta | La ventana y la línea de comandos cargan al abrir las bibliotecas pesadas que solo usa el proceso de conversión |
| B2-06 | 🟠 Media | medio | media | Las imágenes JPEG de un PDF se vuelven a guardar como PNG: pesan el doble, tardan 6 veces más y se pierden imágenes por el tope |
| B2-08 | 🟠 Media | pequeño | alta | Nadie mide cuánto tarda en arrancar la app ni la línea de comandos: los retrasos crecen sin aviso |
| B2-09 | ⚪ Baja | medio | media | Unir en un PDF arma todo el resultado en memoria sin calcular antes el total |
| B2-07 | ⚪ Baja | pequeño | alta | El lector de PDF guarda dos copias del archivo en memoria y abre cada página dos veces |

<details><summary>Detalle técnico y evidencia</summary>

- **B2-01 — La estimación de tiempo y memoria de los PDF, basada en el tamaño del archivo, se equivoca entre 15 y 300 veces con documentos reales y escaneados**
  - *Impacto:* Una persona abre un PDF escaneado, lo más común entre el público general, y ve «⚠ puede tardar más de 10 min y detenerse», más una sugerencia de partirlo, cuando la conversión tarda segundos. El tiempo restante sale igual de inflado. En un portátil de 4 GB, un PDF escaneado de más de ~118 MiB se omitiría por «demasiada memoria» sin intentarlo. Es una señal falsa que asusta, lo contrario de «Claridad es cariño».
  - *Evidencia:* schemas/limits.py:21 PDF=15 s/MiB y :47 PDF=16 MiB/MiB; planning.py:158-159 omite cuando estimated_memory > worker_memory; split_advice.py:37 recomienda partes con esa misma estimación. Medido: PDF real de 86 págs estimado en 40 s, real 2,1 s; PDF de fotos de 108 MB `clearmd --dry-run` → 'about 26 min', real 2,9 s (345 MiB máx); PDF de 232 MiB 'about 58 min', real 0,20 s, 731 MiB frente a una estimación de 3,8 GiB. Con worker_memory=2 GiB el umbral es (2048-160)/16 ≈ 118 MiB.
  - *Recomendación:* Estimar los PDF por el trabajo real: número de páginas (PDFium las cuenta en milisegundos) y una muestra de caracteres por página. Estimar la memoria como ~3,5 veces el tamaño más una cantidad por página. Recalibrar el benchmark 001 con PDF reales: con texto, con muchas imágenes y escaneados. No mostrar «puede detenerse» ni sugerir partir el archivo cuando casi no tiene texto.
- **B2-05 — La App Clásica instalada se desempaqueta cada vez que se abre: tarda unos 5 s, frente a ~1,2 s de las otras dos**
  - *Impacto:* La versión recomendada, la que instala casi todo el mundo, hace esperar unos 5 segundos en cada apertura, casi cuatro veces más que las otras apps. Con antivirus y en un equipo modesto, más. La persona puede creer que no pasó nada y volver a hacer doble clic, lo que abre una segunda copia. Eso, además, activa el riesgo de dos instancias sobre la misma carpeta (B1-07).
  - *Evidencia:* packaging/clearmd.spec:96 EXE de un solo archivo con Splash; packaging/installer/clearmd.iss:211 instala dist\ClearMD.exe tal cual (lo verifiqué). Las ediciones Qt y Flet ya van como carpeta (COLLECT). La medición en Windows es de F2-01, a partir de las marcas de hora del registro de la CI de publicación: ~5 s para la Clásica, ~1,2 s Qt y ~1,4 s flet, descontando la espera de --smoke. No reproduje esa medición.
  - *Recomendación:* Que el instalador ponga la App Clásica en modo carpeta (onedir), igual que Qt y flet, y dejar el .exe de un solo archivo solo para la descarga portátil. Cronometrar --smoke en CI en las dos variantes (ver B2-08).
- **B2-02 — Las pruebas tardan 4–5 veces más de lo necesario por un gc.collect() que corre después de cada prueba**
  - *Impacto:* Afecta al usuario de forma indirecta: cada arreglo espera 22–24 min de CI, y eso frena las correcciones. Responde a la pregunta del dueño: esa demora de la CI no es normal. La publicación sí lo es.
  - *Evidencia:* tests/conftest.py:58-63, fixture autouse `_collect_on_the_main_thread` con gc.collect() después de cada prueba; el motivo son los objetos de Tk. Hay 1.562 funciones de prueba, que se convierten en ~3.472 casos con la parametrización. Medido con test_catalog.py + test_architecture.py (1.094 casos): 54,0 s con gc, de los cuales 41,1 s son de gc.collect; 11,1 s sin gc. Mediana de CI: 0,185 s incluso en las pruebas triviales del catálogo.
  - *Recomendación:* Limitar la recolección a las pruebas de interfaz (tests/gui y tests/unit/frontend/ttk), o ejecutarla solo si la prueba creó una ventana Tk. Es el primer paso, el más barato. Después, valorar pytest-xdist (F2-07) y una matriz escalonada. Subir siempre el JUnit para seguir la duración de las pruebas.
- **B2-03 — El proceso de conversión arranca de cero en cada lote (1,4 s), carga todos los conversores y solo empieza cuando la persona pulsa Convertir**
  - *Impacto:* Cada vez que se pulsa Convertir hay una espera fija de ~1,4 s en la máquina de desarrollo, probablemente más en Windows empaquetado. Tres archivos diminutos tardan 3 s. Si hay un archivo sin extensión, la planificación arranca y cierra otro proceso, y la espera se paga dos veces.
  - *Evidencia:* WorkerRunner.warm_up() medido en 1,36/1,37/1,44 s y 107 MiB. limits.py:81 worker_startup_seconds=0.7, una cifra desactualizada. registry.py:57-86 construye todos los conversores. api/__init__.py:102-120 (la planificación arranca y cierra un proceso) y :144-171 (run_batch abre otro). `clearmd` con 3 archivos diminutos: 3,08 s.
  - *Recomendación:* Precalentar el proceso mientras la persona revisa el plan, reutilizar el de la planificación para la conversión y mantenerlo vivo entre lotes en las ventanas, con cierre automático tras unos minutos sin uso. Crear cada conversor solo cuando aparece su formato. Actualizar worker_startup_seconds con una medición real.
- **B2-04 — La ventana y la línea de comandos cargan al abrir las bibliotecas pesadas que solo usa el proceso de conversión**
  - *Impacto:* La app tarda más en abrir y en responder a cosas simples: `clearmd --version` tarda ~1 s, y cargar la App Clásica, 1,27 s antes de dibujar nada. Cerca de la mitad se va en bibliotecas de PDF y Excel que la ventana nunca usa. Esto suma al retraso de B2-05.
  - *Evidencia:* Tras importar clearmd.frontend.ttk.app (1,27 s) y clearmd.frontend.cli.app (0,81 s), sys.modules contiene pypdfium2, openpyxl, PIL y lxml. Cadena: api/composition.py → worker/page_runner → supervisor.py:17 → child.py:17 → worker/pages.py → split/pdf_pages y split/xlsx_cut; también summary/pdf_report. F2-04 llegó a lo mismo por su cuenta con -X importtime (427–571 ms).
  - *Recomendación:* Importar dentro de las funciones lo que solo usa el proceso de conversión, y agregar una prueba de arquitectura que falle si, tras importar cada punto de entrada, aparecen pypdfium2, openpyxl o lxml. Agregar también un presupuesto de tiempo de arranque.
- **B2-06 — Las imágenes JPEG de un PDF se vuelven a guardar como PNG: pesan el doble, tardan 6 veces más y se pierden imágenes por el tope**
  - *Impacto:* Quien activa «Imágenes en una carpeta» con un PDF de fotos espera mucho más y recibe una carpeta más pesada que el propio PDF. Además, se le dice que se omitieron imágenes «por los límites», aunque cabían en su formato original.
  - *Evidencia:* PDF de 108 MB con 12 JPEG: `clearmd --images` 17,2 s frente a 2,9 s sin imágenes, carpeta de 198 MB, solo 9 PNG escritos y la nota 'images left out (…past the limits): 3'. Son imágenes de ruido, el peor caso para PNG. pdf/pdfium/pictures.py decodifica a mapa de bits.
  - *Recomendación:* Cuando el filtro es solo DCTDecode, sin máscara, guardar los bytes originales (FPDFImageObj_GetImageDataRaw) como .jpg. Dejar PNG para el resto.
- **B2-08 — Nadie mide cuánto tarda en arrancar la app ni la línea de comandos: los retrasos crecen sin aviso**
  - *Impacto:* El retraso de la App Clásica existe desde la v0.1 y ninguna comprobación lo detectó, al igual que las importaciones pesadas. Una dependencia nueva puede sumar segundos a cada apertura sin que el dueño se entere antes de publicar.
  - *Evidencia:* Lo tomo de F2-02 y lo verifiqué en parte: check_executables.sh solo comprueba que la ventana abra y se cierre dentro de un 'timeout 120', sin guardar el tiempo. docs/benchmarks mide la conversión y no el arranque. limits.py:81 worker_startup_seconds=0.7 quedó desactualizada (hoy se mide 1,4 s) sin que nada avisara.
  - *Recomendación:* Cronometrar en CI el tiempo hasta la ventana de cada ejecutable, el de `clearmd-cli --version` y el arranque del proceso de conversión, con un aviso por encima de 3 s y un error por encima de 8 s. Publicar las cifras en la tabla de benchmarks de cada versión.
- **B2-09 — Unir en un PDF arma todo el resultado en memoria sin calcular antes el total**
  - *Impacto:* Al unir muchos PDF pesados, el documento entero se arma en memoria y pasa como bytes entre procesos. Si supera el límite del trabajador, la persona espera todo el proceso para recibir «detenido por memoria», cuando el plan podría haberlo dicho desde el principio.
  - *Evidencia:* Verifiqué split/pdf_pages.py:44-58: merge_pdfs importa todas las páginas en un PdfDocument nuevo, lo guarda en un BytesIO y devuelve bytes. La revisión de memoria del plan es por archivo. Lo planteó B1-08; no medí un caso real.
  - *Recomendación:* Sumar los tamaños en el plan de Unir a PDF y avisar si el total supera la memoria del trabajador. Que el trabajador guarde el PDF unido directamente en un temporal de la carpeta de destino, en lugar de devolver los bytes.
- **B2-07 — El lector de PDF guarda dos copias del archivo en memoria y abre cada página dos veces**
  - *Impacto:* Un PDF grande usa unas tres veces su tamaño en memoria (232 MiB → 731 MiB), lo que lo acerca al límite en equipos con poca RAM, y hay ~15 % de tiempo repetido en documentos largos.
  - *Evidencia:* pdf/__init__.py:46 lee el archivo como bytes; pdfium/document.py:25 create_string_buffer los copia. reader.py:31-39 recorre text_pages() dos veces. cProfile: ctypes.cast por carácter suma 0,35 s (fonts.py:51).
  - *Recomendación:* Leer en un bytearray y pasarlo sin copia (from_buffer); comparar direcciones sin ctypes.cast; valorar reutilizar la primera pasada.

</details>

### Backend · Experiencia de lo que entrega — 6/10

Después del debate mantengo el diagnóstico y lo endurezco un poco. La forma de lo que ClearMD entrega está muy cuidada: resumen con titular, mensajes humanos, nombres ordenados y velocidad. Pero dos colegas confirmaron, y yo lo volví a comprobar, que en algunos casos el contenido entregado no es fiel al original y el producto no avisa. Un .txt guardado en Windows sale con «ańo», «seńores» y «Núńez», y el resumen lo da por convertido (B1-01). «Dividir en 3 partes» entrega «parte 1 de 1» y lo reporta como éxito (B1-02). Un PDF vacío se reporta como «dañado» y se le pide a la persona algo imposible (B1-06). A eso se suman mis hallazgos sobre PDFs reales: tablas con registros partidos en varias filas, ecuaciones mal escritas sin aviso y frases convertidas en títulos. El patrón común es que la salida se ve segura cuando no lo es. Para un producto cuyo destino es una IA, la regla debería ser esta: lo que ClearMD no puede garantizar, lo dice en el resumen. Bajo la nota a 6/10 porque la fidelidad del texto, que es lo más básico, falla en un caso cotidiano para el público hispano.

**Fortalezas que vio:**

- El resumen (Markdown y PDF) empieza por un titular con el resultado y luego dice dónde están los archivos y qué hacer con cada problema. El PDF del resumen tiene muy buena presentación.
- Los mensajes de error comunes son humanos y dicen qué hacer (dañado, con contraseña, archivo comprimido peligroso con su cifra y su límite). El detalle técnico va aparte y plegado.
- Hay transparencia sobre la limpieza: «Lo que ClearMD Limpió» y notas por archivo (encabezados y pies omitidos, fuentes recuperadas, caracteres ilegibles marcados).
- Los nombres no chocan y se leen bien: «sample (pdf).md» / «sample (docx).md», «DOCX, detectado por el contenido» para un archivo sin extensión.
- Las partes llevan ceros a la izquierda («part 01 of 25») y se ordenan bien en cualquier explorador. Cada documento tiene su carpeta dentro de OutputSep.
- En el Markdown unido, cada documento empieza con un rótulo visible («Documento 2 de 3: nombre») y un comentario de origen.
- Excel, CSV, ODT y LaTeX salen como tablas Markdown limpias, y las fórmulas de ODT y LaTeX como LaTeX correcto.
- Dividir y Unir un Markdown decodifican bien el texto de Windows (decode_source): ya existe dentro del producto el modelo correcto para arreglar Convertir.
- La línea de comandos tiene códigos de salida distintos, nunca sobrescribe por su cuenta sin terminal interactiva, y --dry-run no escribe nada.
- Es rápido: 17 archivos mixtos en unos 4 s y un PDF real de unas 80 páginas con imágenes en 4 s.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B3-01 | 🔴 Alta | medio | alta | En las tablas de un PDF, una celda escrita en varias líneas se parte en varias filas |
| B3-02 | 🔴 Alta | medio | alta | Algunas ecuaciones de un PDF salen mal escritas y el resumen no lo advierte |
| B3-03 | 🟠 Media | medio | alta | Frases del texto se convierten en títulos, a veces cortadas a la mitad, y la jerarquía queda invertida |
| B3-04 | 🟠 Media | pequeño | alta | Los nombres de lo que se entrega dependen del idioma, y al cambiarlo quedan copias duplicadas |
| B3-05 | 🟠 Media | pequeño | alta | Cuando la unión falla, la línea de comandos no dice por qué y culpa a un archivo sano |
| B3-06 | 🟠 Media | pequeño | media | El resumen en Markdown, que es el formato por defecto, se ve con etiquetas técnicas fuera de un visor |
| B3-07 | ⚪ Baja | pequeño | alta | Las notas del resumen usan jerga técnica o números sin contexto |
| B3-08 | ⚪ Baja | pequeño | alta | Plurales con «(s)» y concordancia rota en la línea de comandos |
| B3-09 | ⚪ Baja | pequeño | media | El Markdown de un PDF no indica de qué página viene cada parte |
| B3-10 | ⚪ Baja | pequeño | alta | Imágenes sin descripción y archivos sin salto de línea final |

<details><summary>Detalle técnico y evidencia</summary>

- **B3-01 — En las tablas de un PDF, una celda escrita en varias líneas se parte en varias filas**
  - *Impacto:* Un solo registro queda repartido en 5 a 8 filas con las demás celdas vacías. La persona, o la IA que recibe la tabla, cree que hay muchos más registros y no sabe qué dato va con cuál. La tabla se ve correcta, así que el error pasa desapercibido.
  - *Evidencia:* `clearmd real --images --lang es` sobre un PDF académico real de 25 páginas (docs/Examples, anonimizado): 84 filas de tabla empiezan con la primera celda vacía (`grep -c '^\| *\|'`), y la primera tabla muestra un registro seguido de 7 filas `\| \| \| \| <resto> \| \|`. Otro PDF real de unas 80 páginas: 60 filas así. Contradice ADR-0034:25 («a cell wrapped over lines stays one cell») y :32.
  - *Recomendación:* Unir a la fila anterior las filas de continuación (primera columna vacía y texto que sigue al de arriba), con un espacio o <br>. Agregar como prueba fija una tabla realista con celdas de varias líneas, para que la promesa del ADR-0034 quede comprobada.
- **B3-02 — Algunas ecuaciones de un PDF salen mal escritas y el resumen no lo advierte**
  - *Impacto:* Quien estudia o cita un artículo recibe fórmulas que parecen seguras y dicen otra cosa (una fracción cuyo denominador se volvió «1»). Nada en el resumen le sugiere revisarlas, y la IA razonará con la fórmula equivocada.
  - *Evidencia:* En el PDF real de 25 páginas, tres ecuaciones numeradas salen como `\underset{o}{\frac{EF_{o}^{t}(...)}{1}} \\ EF^{t+} (...)`. Al compararlas con la página renderizada (pypdfium2) se ve que es una sola fracción con su denominador real. Ni «Necesita Tu Atención» ni las notas lo mencionan: `formula_kept_as_source` (en.toml:278) solo existe para ODT. Contradice ADR-0036 («Never a wrong formula, said with confidence»).
  - *Recomendación:* Detectar patrones incoherentes (fracción con denominador «1» dentro de \underset, exponente que termina en «+» sin número) y tratar esas ecuaciones como «dudosas», dejando el texto o la imagen, como ya prevé ADR-0036. Cuando un PDF tenga ecuaciones reconstruidas, agregar al resumen una nota: «las ecuaciones se reconstruyeron; revísalas contra el original».
- **B3-03 — Frases del texto se convierten en títulos, a veces cortadas a la mitad, y la jerarquía queda invertida**
  - *Impacto:* El documento pierde su esqueleto: hay títulos que son media oración y la línea de autores sale como subtítulo antes del título principal. Además, «Dividir para una IA» corta por títulos (ADR-0045), así que corta en lugares equivocados.
  - *Evidencia:* PDF real de unas 80 páginas: 13 títulos `####`, varios con más de 120 caracteres, sin puntuación final, y la oración sigue en la línea siguiente. En el PDF de 25 páginas, los autores salen como `###` antes del único `#`. Revisado con `grep -n '^####'` y el contexto enmascarado.
  - *Recomendación:* No convertir en título una línea que no cierra la oración (sin puntuación final y con la siguiente en minúscula) ni una de más de unos 100 caracteres. Que el primer título nunca sea de un nivel menor que los siguientes.
- **B3-04 — Los nombres de lo que se entrega dependen del idioma, y al cambiarlo quedan copias duplicadas**
  - *Impacto:* Si la persona convierte en español y luego, con la app en inglés, vuelve a convertir con «Sobrescribir», quedan dos carpetas de imágenes del mismo documento, o 50 partes en vez de 25, mezcladas «parte 01 de 25» con «part 01 of 25». «Sobrescribir» no protege, porque los nombres no coinciden. Tiene la misma raíz que B1-05: el nombre de un resultado no es estable entre ejecuciones.
  - *Evidencia:* Con --images --lang es y luego --images --overwrite --lang en, OutputMD contiene doc1_imagenes y doc1_images (11 MB cada una). Con `--split-pages 1` en inglés y luego `--lang es --overwrite`: `ls OutputSep/doc2 \| wc -l` = 50. Nombres del catálogo: es.toml:570 `suffix = "_imagenes"`, :574 `part_name`, :642 `name = "Unidos {stamp}"`. El resumen, en cambio, tiene nombre fijo en todos los idiomas (ADR-0016).
  - *Recomendación:* Aplicar a imágenes, partes y archivo unido el criterio de ADR-0016: un nombre que no dependa del idioma, o reconocer los nombres de ambos idiomas como «ya existe». Conviene resolverlo junto con B1-05, con una sola regla: el nombre de un resultado depende solo de su original.
- **B3-05 — Cuando la unión falla, la línea de comandos no dice por qué y culpa a un archivo sano**
  - *Impacto:* La persona ve «0 unidos · 1 con error» sin ninguna razón en pantalla. En el resumen, un archivo sano aparece con ❌, y ese resumen reemplaza al de una unión exitosa hecha antes.
  - *Evidencia:* `clearmd mg/sample.txt --merge markdown`: solo «[1/1] sample.txt» y «0 merged · 0 skipped · 1 failed», exit 1, sin línea ✗. progress.py:35-50 solo imprime las fallas de ConversionFinished; NOTHING_TO_MERGE se decide después (merging.py:167). Incumple spec/contracts/ux.md §3.
  - *Recomendación:* Imprimir las fallas de la unión con su razón. Si antes de empezar ya se sabe que hay menos de dos documentos válidos, avisar como error de uso (exit 2): «Para unir hacen falta al menos dos documentos», sin marcar ningún archivo como fallido.
- **B3-06 — El resumen en Markdown, que es el formato por defecto, se ve con etiquetas técnicas fuera de un visor**
  - *Impacto:* Quien hace doble clic en Resumen_ClearMD.md suele abrirlo en el Bloc de notas y ve `<details><summary>…`, `<!-- clearmd:history -->`, comillas invertidas y asteriscos. Justo la pieza más cuidada se ve como código. Como señala F4-01, además, la etiqueta «Resumen» de la ventana se confunde con un resumen del documento.
  - *Evidencia:* Resumen_ClearMD.md generado en /tmp/audit-B3 contiene HTML en bruto. schemas/settings.py:20 `summary_format: str = "markdown"` (ADR-0031). El PDF del resumen, renderizado, se lee perfectamente.
  - *Recomendación:* Usar «Markdown + PDF» por defecto, o dejar el Markdown en Markdown puro, sin HTML. En la ventana, llamarlo «Informe» (F4-01) sin cambiar el nombre del archivo (ADR-0016).
- **B3-07 — Las notas del resumen usan jerga técnica o números sin contexto**
  - *Impacto:* «…shown as their StarMath source: 2», «la codificación… se dedujo», «cambios rastreados» o «PDFium could not open it (error 3)» no le dicen nada a quien no sabe qué es LaTeX o PDFium, y el número al final no se entiende. F4-07 encontró más casos en la misma familia.
  - *Evidencia:* en.toml:278 y es.toml:278 (`formula_kept_as_source`): sobre tests/fixtures/odt/formulas.odt produce «…StarMath source: `2`». F4-07 suma [note] encoding_guessed, pdf_text_decoded y tracked_changes, que verifiqué en es.toml.
  - *Recomendación:* Reescribir con la cantidad al principio y en lenguaje llano: «2 fórmulas no se pudieron pasar a formato matemático; quedaron como en el original». Usar «control de cambios», como Word. Revisar todas las claves [note] buscando nombres de tecnologías.
- **B3-08 — Plurales con «(s)» y concordancia rota en la línea de comandos**
  - *Impacto:* «Ya existen 1 resultado(s)», «Se convertirían 2 archivo(s)» y «faltan menos de un minuto» suenan a máquina, en un producto cuyo lema es «Claridad es cariño».
  - *Evidencia:* es.toml:122, 140, 146, 147, 160; en.toml:122, 140, 146, 147; merging.py:167 `f"{len(pieces)} document(s) to merge"`. Nuevo en la ronda 2: la CLI imprimió «faltan menos de un minuto», porque es.toml:155 `time_left = "faltan {duration}"` se combina con :165 `under_a_minute = "menos de un minuto"`. Contradice ADR-0031 (plurales desde .one/.other).
  - *Recomendación:* Pasar estas claves a .one/.other y agregar una prueba que no permita «(s)» en los catálogos. Para el tiempo restante, usar una frase completa propia («falta menos de un minuto») en lugar de componer «faltan» + duración.
- **B3-09 — El Markdown de un PDF no indica de qué página viene cada parte**
  - *Impacto:* Cuando la IA responde algo, la persona no puede ir a la página del original para comprobarlo o citarlo.
  - *Evidencia:* El .md del PDF de 25 páginas no tiene ninguna marca de página (`grep -c '<!--'` = 0). Las presentaciones sí llevan '<!-- Slide number: 1 -->'.
  - *Recomendación:* Ofrecer, al menos como opción, una marca discreta por página («<!-- página 12 -->»), como ya ocurre con las diapositivas.
- **B3-10 — Imágenes sin descripción y archivos sin salto de línea final**
  - *Impacto:* Las imágenes se enlazan como «![](…/image-001.png)», sin texto alternativo: ni la IA ni un lector de pantalla saben qué son. Varios .md terminan sin salto de línea, y al pegarlos el último renglón se une al texto siguiente.
  - *Evidencia:* `![](doc2_imagenes/image-001.png)` en el .md del PDF de 25 páginas. 'sample (docx).md', 'sample (pptx).md' y 'sample (epub).md' terminan sin '\n'.
  - *Recomendación:* Usar como texto alternativo el pie de figura cercano, o al menos «Imagen 1». Asegurar el salto de línea final en todos los .md.

</details>

### Backend · Claridad es cariño — 7/10

Después de leer a los otros siete auditores, mantengo el diagnóstico y lo afino. Los catálogos de ClearMD están por encima de la media: cada error trae su siguiente paso y el tono es cálido. El problema que se repite en los dos tableros, y que para esta lente es el más importante, es que el texto promete algo que el producto no cumple. Pasa con «Copiar Detalles», que dice que se cambiaron los nombres de los archivos y no siempre lo hace (B4-01). Pasa con «Prueba con Dividir» en formatos que Dividir no acepta (B4-02). Pasa con «lo que ya se convirtió se conserva», que aparece en una pantalla vacía (F1-02), con «Nada se escribe» mientras ya se está escribiendo (F1-07/F4-05) y con «parece dañado» para un archivo que en realidad está vacío (B1-06, lo reproduje). Los colegas añadieron casos del mismo tipo que comprobé en el código: plurales con «(s)», jerga como «StarMath», «cambios rastreados» o «lote», botones que ya no existen («Convierte más») y una unión fallida que en la terminal no dice por qué. Alrededor de la app siguen los mismos huecos: el README desactualizado, el comando clearmd-cli que no aparece en la documentación, la ayuda de la terminal a medias en español y un canal de soporte que exige una cuenta de GitHub y no explica cómo usarlo. Casi todo se arregla con cambios de texto y unas pocas pruebas automáticas. Nota: 7/10.

**Fortalezas que vio:**

- Cada código de error del backend tiene mensaje y acción en los dos catálogos, y un test verifica que tengan las mismas claves y marcadores. Ningún error llega a la pantalla como traza técnica.
- Los motivos de omisión son concretos y amables: Office antiguo, imágenes, archivos temporales de Office y archivos comprimidos peligrosos, explicados sin la palabra «bomba».
- La sección [terminal] cambia los botones por opciones de la línea de comandos: la ventana no habla de --opciones y la terminal no habla de botones.
- El resumen abre con una frase humana, usa plurales correctos y separa «Necesita Tu Atención» de «Lo que ClearMD Limpió».
- Las promesas tranquilizadoras se repiten donde importan: «Tus originales nunca se modifican» y «Nada se escribe hasta que confirmes». Varios auditores coinciden en que es la mayor fortaleza del producto.
- En la terminal, el error inesperado es honesto: dice «revísalas antes: pueden incluir nombres de archivos» (es.toml:154). Ese es el tono que debería tener también la ventana.
- Los textos del instalador son claros, y la desinstalación garantiza que nunca toca los documentos.
- SECURITY.md y CONTRIBUTING.md son breves, respetuosos y advierten que nunca se adjunten documentos privados.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B4-01 | 🔴 Alta | pequeño | alta | «Copiar Detalles» promete ocultar los nombres de tus archivos, pero algunos se filtran |
| B4-02 | 🔴 Alta | pequeño | alta | Varios mensajes mandan a «Dividir» archivos que Dividir no acepta: un callejón sin salida |
| B4-03 | 🟠 Media | pequeño | alta | El README y la ayuda dicen «clearmd», pero en Windows el instalador crea «clearmd-cli» |
| B4-04 | 🟠 Media | medio | alta | El README quedó en versiones viejas: muestra salidas que ya no existen y omite dos de las tres herramientas |
| B4-05 | 🟠 Media | pequeño | alta | Reportar un problema: «avísanos» sin decir dónde, «adjunta el resumen» con nombres privados, jerga («issue») y formularios solo en inglés |
| B4-06 | 🟠 Media | pequeño | alta | La ayuda de la terminal mezcla español e inglés y describe de menos lo que hace Dividir |
| B4-07 | ⚪ Baja | pequeño | alta | Acciones que dan por hecho que la persona sabe hacerlas: «Quítale la contraseña», «Hazlo visible» |
| B4-08 | ⚪ Baja | pequeño | alta | Al volver a convertir con «conservar», el resumen grita «Ninguno se pudo convertir» y la terminal salta números |
| B4-09 | ⚪ Baja | pequeño | alta | Las notas de versión mezclan los dos idiomas en cada línea y usan jerga interna |
| B4-10 | ⚪ Baja | pequeño | alta | Detalles del instalador: una pregunta sin signo de cierre y una bienvenida con un tono distinto al de la app |

<details><summary>Detalle técnico y evidencia</summary>

- **B4-01 — «Copiar Detalles» promete ocultar los nombres de tus archivos, pero algunos se filtran**
  - *Impacto:* Tras un error inesperado, la persona lee «Cambiamos los nombres de tus archivos y carpetas por <archivo>» y pega el texto en una página pública. Si el error menciona el archivo solo por su nombre, o una carpeta con espacios, el nombre real queda publicado. Puede ser el nombre de un paciente o de un cliente.
  - *Evidencia:* presenter/screens/details.py:13-14, regex _PATH: exige una unidad, \\ o una barra inicial, y corta en el primer espacio. Lo probé con without_paths(): "KeyError: 'Historia clinica Ana.pdf'" queda intacto; "D:\\Clientes\\Ana Ruiz\\ClearMD_Output" queda como '<file> Ruiz\\ClearMD_Output'. La promesa está en es.toml:472 (details_copied). El catálogo de la terminal, es.toml:154, sí es honesto («pueden incluir nombres de archivos»).
  - *Recomendación:* Que el código cumpla más y el texto prometa menos. Reemplazar también los nombres de los archivos del lote, que el presenter conoce, y los tokens entre comillas con extensión de documento; en una ruta con espacios, tapar hasta el final de la línea o de la comilla. Cambiar el texto a «Intentamos ocultar los nombres de tus archivos; revisa que no quede ninguno antes de enviarlo», como ya dice la terminal. Agregar tests con nombre suelto, nombre entre comillas y carpeta con espacios.
- **B4-02 — Varios mensajes mandan a «Dividir» archivos que Dividir no acepta: un callejón sin salida**
  - *Impacto:* A un Word, un PowerPoint o una página web que se detiene por tiempo o por memoria, el mensaje le sugiere «Prueba dividiéndolo con Dividir». Dividir lo rechaza y le dice «Conviértelo», que es justo lo que falló. La persona da vueltas sin salida.
  - *Evidencia:* es.toml [error.timed_out], [error.out_of_memory] y [error.worker_crashed] (acciones), y [skip_action] too_large y too_much_memory, frente a [skip] not_splittable y [skip_action] not_splittable («Conviértelo, o guárdalo primero como PDF»). En la terminal, error.timed_out.action menciona --split-parts. Ninguno de estos textos depende del formato. B2-01 agrava el caso: la estimación inflada dispara la sugerencia de partir el archivo con más frecuencia de la que corresponde.
  - *Recomendación:* Que la acción dependa del formato: «Divídelo con Dividir» para PDF, Markdown, texto, CSV y Excel; para los demás, «Ábrelo en su programa y guárdalo como PDF o en varios archivos más pequeños». Bastan dos variantes de clave, elegidas en el presenter. not_splittable no debería decir «Conviértelo» cuando la persona viene de una conversión fallida.
- **B4-03 — El README y la ayuda dicen «clearmd», pero en Windows el instalador crea «clearmd-cli»**
  - *Impacto:* Quien instala la Línea de Comandos y copia un ejemplo del README recibe «el comando no existe». La propia ayuda repite el nombre equivocado.
  - *Evidencia:* packaging/clearmd.spec:6 y :119 (name="clearmd-cli"); packaging/installer/clearmd.iss:129-130 y :142-143; cli/parser.py:14 tiene prog="clearmd" fijo; grep de 'clearmd-cli' en README.md: sin resultados. La plantilla de bug también pide «clearmd --version».
  - *Recomendación:* Explicar en el README los dos nombres (clearmd-cli si se instaló con el instalador; clearmd si se instaló con pip o uv) y tomar prog de Path(sys.argv[0]).stem.
- **B4-04 — El README quedó en versiones viejas: muestra salidas que ya no existen y omite dos de las tres herramientas**
  - *Impacto:* La puerta del producto muestra mensajes que la app ya no da, solo habla de Convertir, mantiene una insignia de «en construcción» en la versión 2.10 y dice que todas las licencias son permisivas sin contar Qt (LGPL).
  - *Evidencia:* README.es.md: el ejemplo «crece 338 veces al descomprimirse… (posible bomba ZIP)» y «1 omitidos» no coinciden con la salida real de la 2.10 («al abrirse… por seguridad no se abre», «1 omitido»). «Qué produce» solo lista OutputMD/. Dice «25 ADRs» cuando docs/decisions tiene 52. Los créditos dicen «todas permisivas» sin mencionar pyside6-essentials (LGPL), flet ni openpyxl.
  - *Recomendación:* Poner arriba «Qué hace y dónde quedan tus archivos», con las tres carpetas y el resumen. Generar los ejemplos con un script o comprobarlos con un test. Quitar los conteos escritos a mano y corregir los créditos.
- **B4-05 — Reportar un problema: «avísanos» sin decir dónde, «adjunta el resumen» con nombres privados, jerga («issue») y formularios solo en inglés**
  - *Impacto:* En el peor momento, el mensaje dice «avísanos» sin decir dónde, pide adjuntar un resumen que contiene nombres de archivos y carpetas, y la ventana habla de «issue» y de una cuenta de GitHub. Quien usa la app en español termina en un formulario en inglés, con nombres de app distintos a los de la ventana.
  - *Evidencia:* es.toml [error.conversion_failed].action («avísanos y adjunta el resumen») y [error.worker_crashed].action, sin canal. es.toml:470 y :472 («issue nuevo», «cuenta gratuita de GitHub»), comprobado de nuevo tras leer F4-06. .github/ISSUE_TEMPLATE/bug_report.yml está todo en inglés, con las opciones «Classic (ttk)», «Modern (Qt)» y «flet».
  - *Recomendación:* Crear una sola clave de catálogo, «cómo reportar», que se use en todos los mensajes. Debe decir dónde reportar, qué copiar (la línea de Detalle Técnico) y qué no copiar (el resumen completo), con palabras simples («cuéntanos el problema» en lugar de «issue»). Si se agrega un canal sin cuenta, como propone F4-06, mejor. Hacer bilingües los formularios con los nombres de app de la ventana.
- **B4-06 — La ayuda de la terminal mezcla español e inglés y describe de menos lo que hace Dividir**
  - *Impacto:* Con --lang es, «usage», «options» y «error:» siguen en inglés. La ayuda de --split-parts dice «cada PDF», aunque también divide Markdown, texto, CSV y Excel, y el error de --keep no menciona --split-words.
  - *Evidencia:* Ejecuté `clearmd --lang es --help`: los rótulos de argparse salen en inglés. `--split-parts 2 notas.md t.csv` dividió los dos archivos, frente al texto de [cli.help] split_parts. keep_needs_split no menciona --split-words, aunque cli/flow.py:47 lo acepta.
  - *Recomendación:* Traducir los rótulos de argparse, corregir split_parts, split_pages y keep_needs_split, y agregar un epílogo con 3 o 4 ejemplos.
- **B4-07 — Acciones que dan por hecho que la persona sabe hacerlas: «Quítale la contraseña», «Hazlo visible»**
  - *Impacto:* El mensaje trae una acción, pero alguien sin experiencia técnica no sabe cómo llevarla a cabo.
  - *Evidencia:* `clearmd --lang es` sobre tests/fixtures/documents/encrypted.pdf imprime «Quítale la contraseña e inténtalo de nuevo.». La clave [skip_action] hidden dice «Hazlo visible para convertirlo.».
  - *Recomendación:* Dar el cómo en una frase (guardar una copia sin contraseña desde su programa; Propiedades → desmarcar «Oculto»), o enlazar a la Ayuda.
- **B4-08 — Al volver a convertir con «conservar», el resumen grita «Ninguno se pudo convertir» y la terminal salta números**
  - *Impacto:* Si 4 documentos ya estaban bien y 3 fallan, el resumen abre con una ❌: «Ninguno de los 3 documentos se pudo convertir». Asusta y no cuenta los conservados. La terminal salta de [2/7] a [5/7].
  - *Evidencia:* Ejecuté `clearmd --lang es c` y luego `--skip c` sobre una copia de tests/fixtures/documents. Titular: «❌ **Ninguno de los 3 documentos se pudo convertir.**»; la terminal mostró [2/7], [5/7] y [7/7].
  - *Recomendación:* Mencionar los conservados en el titular y reservar la ❌ para cuando nada esté bien. Numerar en la terminal solo lo que se procesa.
- **B4-09 — Las notas de versión mezclan los dos idiomas en cada línea y usan jerga interna**
  - *Impacto:* La página de descargas alterna inglés y español en cada viñeta, acumula unas 280 líneas y habla de ADR, PyPI y «auditoría».
  - *Evidencia:* packaging/RELEASE_NOTES.md (283 líneas, viñetas «EN … / ES …»; «ADR-0050», «Trusted Publishing»).
  - *Recomendación:* Dos bloques separados, solo las novedades de la versión y lo técnico al final, en «Para desarrolladores».
- **B4-10 — Detalles del instalador: una pregunta sin signo de cierre y una bienvenida con un tono distinto al de la app**
  - *Impacto:* Al desinstalar, la pregunta de Sí/No no se cierra (en inglés ni siquiera tiene forma de pregunta). La bienvenida dice «Bienvenido», mientras la app dice «Te Damos la Bienvenida».
  - *Evidencia:* packaging/installer/clearmd.iss:160-161 (RemoveSettings sin «?»), :555 MB_YESNO, :93 WelcomeLabel1; es.toml gui.welcome.title.
  - *Recomendación:* Cerrar las preguntas en los dos idiomas y unificar el tono de la bienvenida.

</details>

### Frontend · Lógica — 7,5/10

Tras leer a los otros siete auditores y volver a revisar el código, mantengo el diagnóstico. El presentador compartido es la pieza más sana del producto: decide estados, páginas y botones una sola vez para las tres ventanas, descarta resultados viejos y no tiene bloqueos sin salida. Los fallos de mi lente siguen estando en los bordes, donde una persona no técnica puede perder trabajo o quedarse sin explicación. Los colegas me hicieron ver dos cosas. (1) El «error inesperado» que deja la pantalla vacía (F1-02) no es un caso raro: también ocurre cuando alguien cancela justo mientras se arma un PDF unido (B1-03, verificado en el código), así que le subo la prioridad dentro de los medios. (2) La promesa de «Copiar Detalles», que vive en el presentador, no se cumple: lo comprobé y un nombre suelto o una carpeta con espacios salen sin ocultar (B4-01). El subtítulo que dice «nada se escribe» mientras se escribe (F1-07) coincide con F4-05: lo dejo como un solo hallazgo. Respecto a la pregunta del dueño sobre la demora de la compilación y la publicación, no es mi lente; apoyo la explicación medida de B2-02 y F2-07: la publicación (6–9 min) es razonable y la CI (20–24 min) no lo es. Nota: 7,5/10.

**Fortalezas que vio:**

- Un solo presentador para las tres ventanas (ADR-0026, ADR-0039): estado, página, botón principal, encabezado y política de cierre se calculan una sola vez, así que la lógica casi no puede divergir entre ttk, Qt y flet.
- Los resultados de un análisis cancelado nunca pisan la pantalla actual, gracias al contador de «generación» (presenter/background.py:later), y el conteo del escaneo se refresca como máximo cada 100 ms.
- Todo botón principal deshabilitado dice por qué (screens/primary.py:why), y Unir avisa desde Revisar que falta un segundo documento, no al final.
- La pausa de 0,5 s tras cambiar de página (chrome/primary_gate.py) impide que un doble clic o un Enter mantenido convierta sin pasar por Revisar, igual en las tres ventanas.
- Una sola regla de edición (intents/reset.py:editable): nada se edita mientras trabaja, y editar después de un plan lo descarta, así que nunca se convierte un plan que no corresponde a la lista.
- Cerrar mientras convierte cancela, oculta la ventana y espera a que se escriba el resumen; nada se abre después.
- Los duplicados se descartan al agregar y otra vez en el backend: una carpeta y un archivo de esa misma carpeta no dan salidas repetidas.
- El presentador ya filtra la opción de imágenes para Unir y Dividir (intents/conversion.py:70): la regla correcta existe; solo falta que la cumpla también el backend (B1-04).

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F1-02 | 🟠 Media | medio | alta | Un error inesperado (también al cancelar mientras se arma un PDF unido) borra los resultados de la pantalla y deja a la persona en el paso 3 sin salida clara |
| F1-01 | 🟠 Media | pequeño | alta | Cerrar la ventana (o pulsar Cancelar) durante una conversión la detiene sin preguntar |
| F1-03 | 🟠 Media | medio | alta | «Dividir los PDF grandes» desde Revisar reemplaza la lista de la persona y cambia en silencio sus preferencias de Dividir |
| F1-04 | 🟠 Media | pequeño | alta | En flet (la interfaz principal) Ajustes e Inicio parecen activos mientras se analiza o convierte, pero no responden |
| F1-05 | 🟠 Media | pequeño | alta | «Quitar Todo» borra la lista entera sin confirmación ni deshacer, junto a «Deseleccionar Todo» y con el mismo estilo |
| F1-07 | 🟠 Media | pequeño | alta | Mientras convierte, el encabezado sigue diciendo «Nada se escribe hasta que pulses Convertir» (fusionado con F4-05) |
| F1-06 | ⚪ Baja | pequeño | alta | Cambiar un ajuste que afecta el plan descarta en silencio la revisión ya hecha |
| F1-08 | ⚪ Baja | pequeño | alta | Paridad de teclado: Ctrl+0 (ir a Inicio) funciona en ttk y flet, pero no en Qt |

<details><summary>Detalle técnico y evidencia</summary>

- **F1-02 — Un error inesperado (también al cancelar mientras se arma un PDF unido) borra los resultados de la pantalla y deja a la persona en el paso 3 sin salida clara**
  - *Impacto:* El mensaje dice que «lo que ya se convirtió se conserva», pero la persona no ve qué se convirtió, «Abrir Carpeta de Resultados» queda deshabilitado y el paso 3 le dice «Pulsa Siguiente en Elegir». Si cambia de página, el mensaje y «Copiar Detalles» desaparecen. Esto no solo pasa con fallos raros: si alguien pulsa Cancelar justo mientras se pegan las páginas de un PDF unido, ve este mismo «error inesperado» en vez de «cancelado». Puede creer que perdió todo o no encontrar sus archivos.
  - *Evidencia:* intents/reset.py:unexpected pone plan=None y report=None, llama forget_work y deja el estado en READY sin cambiar de página. Lo probé con una vista y un backend falsos cuyo run_batch lanza una excepción: queda en la página 3 con Primary(label='Convert', enabled=False, hint='Press Next on Choose…'). El mensaje se borra al cambiar de página (ttk/window/view.py:69-70, flet/window/view.py:57, pyside/window/view.py:66). Vía de cancelación (B1-03, revisada por mí): intents/conversion.py:102 atrapa `except Exception` y llama unexpected; use_cases/merging.py:180-182 en _write solo atrapa ConversionError y OSError, y Cancelled (schemas/errors.py:82) hereda de Exception, así que una cancelación durante merge_pdfs llega al presentador como error inesperado.
  - *Recomendación:* Tras un error, llevar a la persona a Resultados con lo que se sabe: las carpetas de salida del plan (guardar result_folders antes de descartarlo), para que «Abrir Carpeta de Resultados» funcione, y una línea que diga qué pasó. Mantener «Copiar Detalles» disponible, por ejemplo en Ayuda, aunque cambie de página. En el presentador, tratar Cancelled por separado de los errores: si la persona canceló, mostrar «cancelado», nunca «error inesperado». El arreglo de fondo en el backend lo propone B1-03.
- **F1-01 — Cerrar la ventana (o pulsar Cancelar) durante una conversión la detiene sin preguntar**
  - *Impacto:* Quien pulsa la X por error, o Cancelar buscando otro botón, detiene en el acto el archivo en curso y todos los pendientes de un lote que pudo llevar muchos minutos. La ventana desaparece en silencio mientras termina, así que la persona puede creer que el programa se cerró mal. Lo ya convertido se conserva, pero hay que volver a armar y lanzar el resto.
  - *Evidencia:* presenter/chrome/close_policy.py:on_close devuelve CANCEL_AND_WAIT sin confirmación; flet/window/closing.py:44-49, pyside/window/closing.py:54-59 y ttk/window/closing.py:41-47 llaman presenter.cancel() y ocultan la ventana de inmediato; intents/conversion.py:cancel cancela sin preguntar. spec/features/016 y 018 AC-07 solo piden «cancela y espera». Captura docs/screenshots/018/3-convert-light-es.png.
  - *Recomendación:* Con una conversión en curso, pedir confirmación antes de cerrar o cancelar: «Se está convirtiendo el archivo 3 de 6. Si cierras, se detiene y lo ya convertido se guarda. ¿Detener?», con «Seguir Convirtiendo» como opción por defecto. La decisión va en close_policy para que las tres ventanas la compartan. Se puede omitir la pregunta si falta menos de un archivo.
- **F1-03 — «Dividir los PDF grandes» desde Revisar reemplaza la lista de la persona y cambia en silencio sus preferencias de Dividir**
  - *Impacto:* Alguien elige 30 documentos, ve en Revisar que 2 son demasiado grandes y acepta la oferta. Su lista queda reducida a esos 2: los otros 28, aún sin convertir, desaparecen y hay que buscarlos de nuevo. Además, el corte, el número de partes y lo que guarda Dividir, que la persona había dejado configurados, se reemplazan y se guardan sin aviso.
  - *Evidencia:* Revisado de nuevo: intents/tools.py:52-54 `s.inputs = [path for path, _ in found]`, `settings = replace(s.settings, split_cut="parts", split_parts=parts, split_keep="markdown")` y `save(...)`, que persiste en el archivo de ajustes. La oferta aparece en Revisar (models.PlanView.split_offer; captura docs/screenshots/018/2-review-split-offer-light-es.png). La spec 025 pide listar solo esos PDF, pero no olvidar la lista original ni guardar los ajustes.
  - *Recomendación:* Guardar la lista original y la herramienta antes de saltar a Dividir, y ofrecer después en «¿Qué Sigue?» la opción «Volver a Convertir los Otros 28». Aplicar el número de partes recomendado solo esta vez, sin guardarlo como preferencia.
- **F1-04 — En flet (la interfaz principal) Ajustes e Inicio parecen activos mientras se analiza o convierte, pero no responden**
  - *Impacto:* Durante la conversión, la persona pulsa «Ajustes» o «Inicio» y no pasa nada, sin ninguna explicación. En la versión Qt los mismos botones se ven atenuados. Ese clic sin respuesta da la sensación de que la aplicación se colgó.
  - *Evidencia:* docs/screenshots/018/3-convert-light-es.png (flet: «Ajustes» igual que «Ayuda») frente a docs/screenshots/016/3-convert-light-es.png (Qt: atenuados). flet/window/controls.py:apply_enabled marca rail.settings.disabled, pero flet/components/rail.py:_draw pinta siempre con el rol fijo 'railButton', sin estilo de deshabilitado. Inicio no aparece en apply_enabled, y tools.go_home y choose_tool hacen `return` en silencio en WORKING. F3-02 confirma desde lo visual que los estilos de flet no definen estados (FOCUSED); el de deshabilitado del riel tampoco existe.
  - *Recomendación:* En flet, pintar Ajustes e Inicio atenuados mientras trabaja, igual que en Qt. En las tres ventanas, si se pulsa algo bloqueado, mostrar la línea que ya existe («Convirtiendo… espera a que termine o cancélalo»). Agregar una prueba de paridad: en el estado CONVERTING, las tres ventanas exponen los mismos controles deshabilitados.
- **F1-05 — «Quitar Todo» borra la lista entera sin confirmación ni deshacer, junto a «Deseleccionar Todo» y con el mismo estilo**
  - *Impacto:* En Unir, el orden de los documentos se arma con cuidado, flecha por flecha. Un clic desviado de «Deseleccionar Todo» a «Quitar Todo» lo borra todo y no hay forma de recuperarlo. Para una persona no técnica, «quitar» y «deseleccionar» se parecen mucho.
  - *Evidencia:* docs/screenshots/018/1-choose-merge-light-es.png: «Quitar lo Seleccionado · Quitar Todo · Deseleccionar Todo», tres enlaces iguales y contiguos. flet/components/inputs_card.py:40 `self.clear = button('link', on_clear)` sin confirmación; intents/inputs.py:clear_inputs borra directamente; no hay «deshacer» en el catálogo.
  - *Recomendación:* Ofrecer deshacer inmediato («Lista vaciada · Deshacer», durante unos segundos) o pedir confirmación cuando la lista tenga 3 o más elementos. Separar visualmente «Quitar Todo» y darle tono de advertencia.
- **F1-07 — Mientras convierte, el encabezado sigue diciendo «Nada se escribe hasta que pulses Convertir» (fusionado con F4-05)**
  - *Impacto:* Durante la conversión el subtítulo afirma lo contrario de lo que ocurre: ya se está escribiendo. Contradice a la barra de progreso justo cuando la persona mira si algo está pasando, y le resta credibilidad a la frase tranquilizadora en los demás momentos.
  - *Evidencia:* Revisado de nuevo: presenter/chrome/header.py:28-31 usa siempre `gui.page.{step}_subtitle`; el estado solo cambia la línea superior (eyebrow). Capturas docs/screenshots/018/3-convert-light-es.png y 016/3-convert-light-es.png: «PASO 3 DE 4 · CONVIRTIENDO» con «Nada se escribe hasta que pulses Convertir…». Pasa igual en Dividir y Unir ([tool.split] y [tool.merge] gui.page.convert_subtitle). F4-05 llegó a lo mismo por su cuenta.
  - *Recomendación:* En header_of, elegir el subtítulo según el estado: antes, el texto actual; durante, «Tus resultados se están guardando; puedes cancelar cuando quieras y lo ya terminado se conserva»; después, «Listo: mira los Resultados». Con una prueba que recorra cada estado.
- **F1-06 — Cambiar un ajuste que afecta el plan descarta en silencio la revisión ya hecha**
  - *Impacto:* La persona está en Revisar o Convertir, abre Ajustes y cambia «incluir subcarpetas» o el modo HTML. Al volver, Revisar está vacío y «Convertir» deshabilitado con «Pulsa Siguiente en Elegir», sin que nada le diga que fue por el ajuste. Parece que algo se rompió.
  - *Evidencia:* intents/preferences.py:save_settings llama a editable() si cambian recursive o html_strategy, y editable() (reset.py:12-22) descarta el plan sin mensaje. Probado con el presentador falso: tras invertir recursive en la página 3, queda Primary(enabled=False, hint='Press Next on Choose…').
  - *Recomendación:* Mantener el descarte que exige ADR-0029, pero decirlo en una línea: «Cambiaste un ajuste que cambia lo que se convierte: pulsa Siguiente en Elegir para revisar de nuevo». Mejor aún, volver a analizar automáticamente si había un plan.
- **F1-08 — Paridad de teclado: Ctrl+0 (ir a Inicio) funciona en ttk y flet, pero no en Qt**
  - *Impacto:* Quien usa el teclado, por ejemplo con un lector de pantalla, no puede volver a Inicio con el mismo atajo en la versión Qt.
  - *Evidencia:* pyside/window/inputs.py:33 `for number in range(1, len(STEPS) + 1)` (Ctrl+1..4); ttk/window/inputs.py:44 `for number in range(5)` (Ctrl+0..4); flet/window/keys.py:18 STEP_KEYS desde HOME (0).
  - *Recomendación:* Incluir Ctrl+0 en Qt y declarar los atajos en presenter/chrome, con una prueba de paridad entre las tres ventanas.

</details>

### Frontend · Eficiencia — 6,5/10

Después del debate mantengo el diagnóstico y lo afino con lo que vieron los colegas. La interfaz no se congela al convertir y no gasta CPU cuando está quieta. La lentitud que nota la persona viene de tres cosas. (1) La App Clásica, que es la del instalador liviano recomendado, tarda unos 5 s en abrir en Windows frente a ~1,2 s de las otras, porque se instala como ejecutable de un solo archivo y se desempaca en cada apertura (B2-05 llegó a lo mismo por otra vía). (2) Al abrir, la ventana carga bibliotecas de PDF y Excel que no usa (coincido con B2-04). Después, al pulsar Convertir, espera ~1,4 s a que arranque el proceso de conversión, una espera que podría hacerse mientras la persona revisa el plan (B2-03). (3) Nadie mide el tiempo de arranque, así que estos retrasos no aparecen en ningún informe. Sobre la pregunta del dueño corrijo mi primera respuesta. La publicación (6–9 min) sí es normal. La CI (20–24 min) no lo es. La causa principal no es la falta de paralelismo que señalé en la ronda 1, sino un gc.collect() que corre después de cada una de las ~3.472 pruebas. Lo comprobé yo mismo: 600 pruebas del catálogo tardan 27,9 s con él y 7,9 s sin él. Arreglarlo es pequeño y no quita ninguna garantía. Nota: 6,5/10.

**Fortalezas que vio:**

- La conversión corre en un proceso trabajador aparte con cancelación real (ADR-0015/0050): la ventana nunca se congela mientras convierte, y la decisión de un solo trabajador se tomó midiendo.
- No hay consultas periódicas inútiles: los únicos temporizadores son el progreso (solo mientras convierte), el conteo del análisis y la espera al cerrar. Con la ventana quieta, la CPU no se usa.
- La lista de ttk pinta íconos y casillas solo de las filas visibles (ttk/components/file_list.py:124-143), y los redibujos esperan a que termine el cambio de tamaño (REDRAW_MS).
- En flet, el progreso refresca solo su tarjeta y no la página entera (flet/window/window.py:116, narrow()). Es el patrón que hay que extender a la lista.
- Ejecutables livianos vigilados: la CI falla si numpy, pandas, onnxruntime o magika se cuelan (packaging/check_executables.sh), y pone topes de tamaño a los instaladores (ADR-0052).
- El instalador liviano recomendado (~40 MB) pensado para conexiones lentas o medidas: hay que conservarlo.
- El motor es rápido de verdad con documentos reales (B2 lo midió: 86 páginas en ~2 s). La lentitud que se percibe está en los costos fijos de arranque, no en convertir, y eso hace que arreglarla sea barato.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F2-01 | 🔴 Alta | medio | alta | La App Clásica, la recomendada, es la que más tarda en abrir en Windows (unos 5 s contra ~1,2 s de las otras) |
| F2-02 | 🟠 Media | pequeño | alta | Nadie mide cuánto tarda en abrir cada ventana: si empeora, nadie se entera |
| F2-03 | 🟠 Media | medio | media | La lista de flet se vuelve pesada con muchos archivos: cada cambio reconstruye todas las filas y refresca la página entera |
| F2-04 | 🟠 Media | pequeño | alta | Al abrir, la ventana (y la línea de comandos) cargan bibliotecas de conversión que solo usa el proceso trabajador |
| F2-08 | 🟠 Media | medio | media | Al pulsar Convertir hay una espera fija de ~1,4 s que podría hacerse mientras la persona lee Revisar |
| F2-07 | 🟠 Media | pequeño | alta | La CI tarda 20–24 min sobre todo por una limpieza de memoria que corre después de cada prueba, no por las pruebas en sí |
| F2-05 | 🟠 Media | grande | media | Tres ventanas cuestan caro: ~380 MB instalados en la edición completa, cuatro copias del motor y cada función hecha tres veces |
| F2-06 | ⚪ Baja | pequeño | alta | En Linux solo hay una descarga de 224 MB con todo dentro |

<details><summary>Detalle técnico y evidencia</summary>

- **F2-01 — La App Clásica, la recomendada, es la que más tarda en abrir en Windows (unos 5 s contra ~1,2 s de las otras)**
  - *Impacto:* Quien instala la versión recomendada espera unos 5 segundos cada vez que hace doble clic, casi cuatro veces más que con las otras dos apps. En un portátil modesto con antivirus puede tardar todavía más. Una persona no técnica puede creer que no pasó nada y volver a hacer doble clic. Eso abre una segunda copia, que además puede interferir con el trabajo de la primera sobre la misma carpeta (B1-07). Si la app se cierra a la fuerza, quedan carpetas temporales sueltas.
  - *Evidencia:* Registro de la CI de publicación (job 'Executables (windows)', paso 'Check the executables'). Entre 'command line: 12 of 12 converted' y 'window: opened and closed' pasan 8,0 s, 3 de ellos de la espera de --smoke, así que ClearMD.exe tarda ~5 s en abrir. Con el mismo cálculo, Qt tarda ~1,2 s y flet ~1,4 s. En el contenedor, sin empaquetar, ttk abre en 1,6–1,8 s y Qt en ~1,5 s: la diferencia la pone el desempaque. Lo volví a comprobar en esta ronda: packaging/clearmd.spec:4-5 dice 'Two one-file programs: ClearMD (... a splash while it unpacks)', packaging/installer/clearmd.iss:211 instala dist\ClearMD.exe tal cual, y en cambio :215 y :220 instalan las carpetas ClearMD-Qt\* y ClearMD-Flet\*. B2-05 llegó a la misma conclusión desde el ADR.
  - *Recomendación:* El instalador debe instalar la App Clásica como carpeta (onedir), igual que ya hace con Qt y flet. El .exe de un solo archivo se queda solo para la descarga portátil. Hay que ajustar ADR-0028/0040 en este punto: la razón de ADR-0028 ('un solo archivo fácil de bajar') no aplica a una copia instalada, porque la persona nunca ve la carpeta. Lo esperable es que abra en ~1–1,5 s. Antes de decidir, medir las dos variantes con F2-02.
- **F2-02 — Nadie mide cuánto tarda en abrir cada ventana: si empeora, nadie se entera**
  - *Impacto:* El retraso de F2-01 existe desde la v0.1 y no aparece en ningún informe. Una dependencia nueva o una importación pesada (como las de F2-04) pueden sumar segundos al abrir sin que el dueño lo sepa antes de publicar.
  - *Evidencia:* packaging/check_executables.sh:34-36, 72-74 y 110-112, y packaging/check_installer.ps1:191-196, solo comprueban que la ventana abra y se cierre antes de 'timeout 120'; no guardan el tiempo. spec/roadmap.md (006b) mide el tamaño del ejecutable, no el arranque. docs/benchmarks/ mide la conversión, no la interfaz. Las cifras de F2-01 tuve que sacarlas de las marcas de hora del registro.
  - *Recomendación:* Que --smoke imprima los milisegundos hasta la primera ventana de cada app (y del instalador), con un aviso por encima de 3 s y un error por encima de 8 s. Agregar esa cifra a los benchmarks de cada versión, también en Linux.
- **F2-03 — La lista de flet se vuelve pesada con muchos archivos: cada cambio reconstruye todas las filas y refresca la página entera**
  - *Impacto:* Quien agrega una carpeta con cientos o miles de documentos en la App Estilo Móvil puede ver que la ventana se traba al agregar, al quitar un archivo o al marcar casillas. En Qt y ttk la misma lista es casi instantánea.
  - *Evidencia:* Medido en el contenedor con la FileList real. flet con 2.000 filas: 0,46 s y 18.007 controles solo para crearlas en Python. Qt con 2.000 filas: 0,024 s. Lo volví a comprobar en esta ronda: flet/components/file_list.py show_rows crea `self.lines = [self._line(...) for ... in self._rows]` desde cero en cada llamada, y flet/window/flet_page.py:66, 94, 103 y 130 llaman a page.update() de toda la página. No pude medir el envío ni el dibujo en Flutter porque el contenedor no tiene cliente.
  - *Recomendación:* Reusar las filas que ya existen: crear solo las nuevas y quitar solo las que salen. En selección y casillas, refrescar solo la lista (narrow), no la página. Si no alcanza, mostrar N filas con 'y M más'. Probarlo con un lote sintético de 2.000 archivos.
- **F2-04 — Al abrir, la ventana (y la línea de comandos) cargan bibliotecas de conversión que solo usa el proceso trabajador**
  - *Impacto:* Cada apertura gasta entre medio y un segundo cargando las bibliotecas de Excel, PDF y del resumen PDF, aunque la conversión ocurra en otro proceso que las carga por su cuenta. `clearmd --version` tarda ~1 s. En Windows empaquetado pesa más, y la ventana ocupa memoria sin necesidad.
  - *Evidencia:* Con python -X importtime en el contenedor: clearmd.frontend.presenter.ports importa clearmd.backend.api y acumula 427–571 ms de un total de 1,46 s. La cadena es composition → worker.page_runner → supervisor → child → worker.pages → split.xlsx_cut (openpyxl, 184 ms) y summary.pdf_report (pypdfium2, ~98 ms). B2-04 llegó a la misma cadena por su lado y midió `clearmd --version` en 1,01–1,08 s. Esto incumple la intención de ADR-0015 ('el padre nunca importa' las bibliotecas de conversión).
  - *Recomendación:* Importar dentro de las funciones lo que solo usa el trabajador (worker.pages, la referencia a worker_main, pdf_report). Agregar una prueba de arquitectura que falle si, tras importar cada punto de entrada de interfaz, openpyxl, pypdfium2 o lxml están en sys.modules.
- **F2-08 — Al pulsar Convertir hay una espera fija de ~1,4 s que podría hacerse mientras la persona lee Revisar**
  - *Impacto:* Cada vez que se pulsa Convertir, la barra tarda en moverse porque el proceso de conversión arranca de cero, incluso con archivos diminutos. Si se cancela y se vuelve a lanzar, se paga otra vez. En un portátil con Windows y el ejecutable empaquetado, la espera probablemente sea mayor. Es justo el momento en que la persona mira si 'funcionó'.
  - *Evidencia:* Tomado de B2-03: warm_up() mide 1,36–1,44 s y 107 MiB, y run_batch arranca un proceso nuevo (api/__init__.py:144-171). No lo volví a medir en esta ronda. En el presenter, el paso Revisar ya deja a la persona leyendo el plan varios segundos, y la pausa de 0,5 s de primary_gate garantiza un tiempo mínimo en esa pantalla.
  - *Recomendación:* Precalentar el trabajador al entrar en Revisar y entregárselo a la conversión. No mantenerlo vivo entre lotes: en portátiles de 4 GB, 107 MiB ociosos no compensan, así que hay que cerrarlo al terminar o al salir de Revisar sin convertir. Así se mantiene un solo proceso y la cancelación real.
- **F2-07 — La CI tarda 20–24 min sobre todo por una limpieza de memoria que corre después de cada prueba, no por las pruebas en sí**
  - *Impacto:* Al usuario no le afecta directamente, pero responde la pregunta del dueño. La publicación (6–9 min) es normal: arma 4 ejecutables y 3 instaladores y los prueba. Los 20–24 min de CI no son normales: cada arreglo espera eso antes de poder publicarse, y esa espera desanima a probar seguido.
  - *Evidencia:* tests/conftest.py:57-63 define el fixture autouse _collect_on_the_main_thread, que llama a gc.collect() después de cada prueba; solo hace falta por los objetos de Tk. Lo medí yo en esta ronda: tests/unit/i18n/test_catalog.py (600 pruebas) tarda 27,89 s con el fixture y 7,86 s si gc.collect se anula con un plugin en /tmp/audit-F2r2. Es la misma proporción que midió B2-02 (54 s → 11 s). Corrijo mi cifra de la ronda 1: 1.562 son las funciones de prueba (grep 'def test_'); los casos ejecutados, con parámetros, son ~3.472. ci.yml:56 corre pytest en serie en 4 combinaciones, y Windows marca el total.
  - *Recomendación:* Hacerlo en este orden. (1) Mover gc.collect a un conftest solo de las pruebas de ventana (tests/gui, tests/unit/frontend/*), o ejecutarlo solo si la prueba creó una ventana Tk. Es un cambio pequeño y conserva el motivo del fixture. (2) Medir otra vez; si sigue siendo largo, agregar pytest-xdist a las pruebas de backend. (3) Correr solo Linux con 3.14 en cada push y dejar la matriz completa para PR, main y etiquetas. (4) Guardar como artefacto fijo el instalador viejo 0.0.1 de la prueba de actualización, en vez de recompilarlo.
- **F2-05 — Tres ventanas cuestan caro: ~380 MB instalados en la edición completa, cuatro copias del motor y cada función hecha tres veces**
  - *Impacto:* Quien elige la edición completa recibe la misma app cuatro veces, cada una con su propio Python y su propio motor. Para el dueño, cada función nueva y cada arreglo visual se hacen y se prueban tres veces. Los colegas lo confirman con hallazgos de paridad (F1-04, F1-08, F3-03, F3-07): esa triple superficie es donde nacen las diferencias entre ventanas.
  - *Evidencia:* Registro de CI (Windows): ClearMD.exe 37 MB, clearmd-cli.exe 37 MB, ClearMD-Qt 134 MB y ClearMD-Flet 172 MB. Código: ttk 4.967 líneas, PySide 3.735 y flet 3.746, más 2.018 del presentador compartido. Pruebas por GUI: ttk 203, PySide 117 y flet 152.
  - *Recomendación:* Respetar la decisión del dueño (ADR-0052) y ponerle tope al costo. (1) Elegir una ventana de referencia: una función se publica cuando funciona ahí, y las otras pueden ir una versión detrás. (2) Llevar al presentador lo que hoy decide cada ventana, como el estado deshabilitado de los controles y los atajos (F1-04, F1-08), para que la paridad salga sola. (3) Revisar una vez al año si alguna ventana tiene usuarios reales.
- **F2-06 — En Linux solo hay una descarga de 224 MB con todo dentro**
  - *Impacto:* Quien usa Linux y solo quiere la App Clásica tiene que bajar 224 MB, unas cinco veces lo que pesa la Clásica sola. Windows ya lo resolvió con el instalador liviano.
  - *Evidencia:* Release v2.9.0: ClearMD-v2.9.0-linux.tar.gz pesa 224 MB (gh release view). packaging/package.sh:41-46 mete las cuatro apps en un solo tar.gz.
  - *Recomendación:* Publicar en Linux un paquete liviano (Clásica más línea de comandos, ~70 MB) y otro completo, como en ADR-0052. Las notas de la versión deben decir primero cuál necesita la mayoría.

</details>

### Frontend · Estilo visual UI/UX — 7/10

Después del debate mantengo el diagnóstico: la identidad visual es coherente y está cuidada en las tres interfaces, y los problemas están en lo que la persona no alcanza a ver o a distinguir. Sigue en primer lugar el texto cortado en las listas: el motivo de cada archivo y el final de la carpeta. Le siguen el foco del teclado (invisible en flet, débil en ttk) y el paso 1 de Dividir y Unir, que junta demasiadas decisiones. Uno este último hallazgo con el de F4 sobre la palabra «Resumen», que suma una ambigüedad real. Los colegas me hicieron ver una clase de problema que antes pasé por alto: controles que no se ven como lo que son. En flet, Ajustes parece activo mientras trabaja (F1-04, lo verifiqué en el código), y «Quitar Todo» tiene el mismo estilo que «Deseleccionar Todo» (F1-05). Lo agrego como F3-10. Retiro mi hallazgo sobre Title Case en español: el dueño lo declaró doctrina explícita para los dos idiomas, y el texto actual la cumple, así que no es un defecto. También apoyo el subtítulo «Nada se escribe…» durante la conversión (F1-07/F4-05), que comprobé en header.py. Todo se corrige sin rediseñar. Nota: 7/10.

**Fortalezas que vio:**

- Una sola fuente de colores, espaciados y tipografía (frontend/design/) compartida por ttk, PySide6 y flet: las tres se ven como el mismo producto.
- Los colores base pasan el contraste WCAG AA en los dos temas, y hay una prueba automática (test_brand.py) que vigila 15 pares.
- La persona siempre sabe dónde está: el riel marca el paso y la cabecera dice «PASO N DE 4 · estado».
- Un solo botón principal por pantalla, claramente dominante, con 44 px de alto y texto de 14 px como mínimo.
- Nada depende solo del puntero: la línea bajo la lista repite el motivo de la fila seleccionada.
- Íconos por formato y tarjetas de cifras que combinan número, palabra y color: el estado no se comunica solo con color.
- Riel compacto automático y un modo oscuro cuidado.
- Capturas automáticas en los dos temas y los dos idiomas: un registro visual excelente para detectar regresiones.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F3-01 | 🔴 Alta | medio | alta | Las listas cortan justo lo que la persona necesita leer: el motivo de cada archivo y el final de la carpeta |
| F3-02 | 🟠 Media | pequeño | media | En flet, la interfaz principal, no se ve dónde está el foco del teclado en las tarjetas ni en los botones |
| F3-03 | 🟠 Media | pequeño | alta | Foco débil en ttk (anillo de 1 px y bajo contraste), y en Qt el foco de una tarjeta se ve igual que el puntero encima |
| F3-05 | 🟠 Media | medio | media | El paso 1 pide demasiadas decisiones juntas, y una de ellas («Resumen») se confunde con resumir el documento |
| F3-10 | 🟠 Media | pequeño | alta | Hay controles que no se ven como lo que son: Ajustes parece activo cuando está bloqueado y «Quitar Todo» se ve tan inofensivo como «Deseleccionar Todo» |
| F3-04 | 🟠 Media | medio | alta | En la ventana más pequeña permitida, las opciones de Dividir quedan cortadas a mitad de línea mientras sobra espacio debajo |
| F3-06 | 🟠 Media | pequeño | alta | Los colores calculados (fila seleccionada, puntero encima, enlace al pasar el puntero) no tienen prueba de contraste y dos de ellos no alcanzan AA |
| F3-07 | ⚪ Baja | pequeño | alta | Pequeñas diferencias entre las tres interfaces que restan pulido |
| F3-09 | ⚪ Baja | pequeño | alta | Las capturas de referencia tienen huecos que impiden ver estados clave |

<details><summary>Detalle técnico y evidencia</summary>

- **F3-01 — Las listas cortan justo lo que la persona necesita leer: el motivo de cada archivo y el final de la carpeta**
  - *Impacto:* En Revisar, la columna «Qué Pasará» aparece cortada en casi todas las filas, y hay que hacer clic fila por fila para leer el motivo. En ttk el texto se corta a mitad de palabra y solo se ven 3 filas. En Elegir (flet), la columna Carpeta muestra el principio de la ruta, que es igual en todas las filas, y se pierde la carpeta que las distingue.
  - *Evidencia:* docs/screenshots/007/2-review-light-es.png; 016/2-review-split-offer-light-es.png; 018/2-review-dark-es.png; 018/1-choose-merge-dark-es.png; flet/components/file_list.py:168 (max_lines=1, TextOverflow.ELLIPSIS por el final).
  - *Recomendación:* Poner el motivo como segunda línea bajo el nombre, o dejar que ocupe dos líneas. Recortar las rutas por el medio o por el principio («…\Documentos\Tesis»). En ttk, dar a la lista de Revisar todo el alto libre.
- **F3-02 — En flet, la interfaz principal, no se ve dónde está el foco del teclado en las tarjetas ni en los botones**
  - *Impacto:* Quien navega con Tab no sabe qué tarjeta o botón está activo en Inicio ni en «¿Qué Sigue?». El contrato UX exige foco visible.
  - *Evidencia:* flet/visuals/look.py:126 (tile_style con overlay TRANSPARENT y sin ControlState.FOCUSED); look.py:76-112 sin FOCUSED; grep FOCUSED en frontend/flet: 0 resultados. PySide sí lo define (stylesheet.py:91-111). No lo vi renderizado.
  - *Recomendación:* Agregar a todos los estilos de flet un estado «con foco» con un borde de 2 px, distinto del estado bajo el puntero, y capturas automáticas con el foco puesto.
- **F3-03 — Foco débil en ttk (anillo de 1 px y bajo contraste), y en Qt el foco de una tarjeta se ve igual que el puntero encima**
  - *Impacto:* En ttk el anillo de foco cuesta verlo. En Qt, quien usa el teclado no distingue entre «estoy aquí» y «el ratón pasó por aquí».
  - *Evidencia:* ttk/visuals/shapes.py:37-47 (con SUPERSAMPLE=4 el anillo queda en 1 px, aunque el docstring dice 2 px); ttk/visuals/buttons.py:40 (ring=palette.clear, 3,43:1 sobre ground claro); pyside/visuals/stylesheet.py:102-103 (hover y focus con el mismo borde).
  - *Recomendación:* Anillo de 2 px con un contraste de al menos 3:1. En Qt, un aspecto propio para el foco.
- **F3-05 — El paso 1 pide demasiadas decisiones juntas, y una de ellas («Resumen») se confunde con resumir el documento**
  - *Impacto:* En Dividir, una sola tarjeta junta qué guardar, cómo cortar, dónde guardar y el formato del resumen: de 10 a 13 controles antes de poder seguir, con etiquetas a distintas alturas. Además, en una herramienta para IA, «Resumen: Markdown / PDF» parece una promesa de resumir el documento (aporte de F4-01). Resumen e Imágenes se repiten en Ajustes.
  - *Evidencia:* docs/screenshots/018/1-choose-split-light-es.png, 018/1-choose-compact-light-es.png, 018/6-settings-light-es.png; es.toml [gui.main] summary_title = «Resumen:».
  - *Recomendación:* En el paso 1, dejar solo la decisión esencial de cada herramienta y mostrar los valores por defecto como una frase con «Cambiar». Lo demás va en «Más opciones» o solo en Ajustes. Renombrar la etiqueta de la ventana como «Informe de lo que pasó» (el archivo puede conservar su nombre según ADR-0016). Alinear las etiquetas de grupo en una columna.
- **F3-10 — Hay controles que no se ven como lo que son: Ajustes parece activo cuando está bloqueado y «Quitar Todo» se ve tan inofensivo como «Deseleccionar Todo»**
  - *Impacto:* Mientras convierte en flet, «Ajustes» se ve igual que «Ayuda» pero no responde: un clic muerto que parece un cuelgue. En Elegir, el enlace que borra toda la lista (y el orden armado para Unir) tiene el mismo aspecto que uno inofensivo y está justo al lado.
  - *Evidencia:* flet/components/rail.py:70-73 (el texto de Ajustes es un label con el rol fijo «railButton»: el estilo deshabilitado del botón no le llega); flet/window/controls.py:28 solo pone disabled; comparar docs/screenshots/018/3-convert-light-es.png con 016/3-convert-light-es.png. flet/components/inputs_card.py:39-40: remove y clear usan el mismo button("link"); captura 018/1-choose-merge-light-es.png.
  - *Recomendación:* Que todo control deshabilitado tome el color «disabled» también en su contenido, y que una prueba de paridad compare por estado los controles deshabilitados de las tres interfaces. Dar a «Quitar Todo» un tono de advertencia, separarlo de «Deseleccionar Todo» y ofrecer un deshacer (F1-05).
- **F3-04 — En la ventana más pequeña permitida, las opciones de Dividir quedan cortadas a mitad de línea mientras sobra espacio debajo**
  - *Impacto:* A 800 px, la tarjeta «Cómo Dividir» corta su explicación y obliga a descubrir una barra interna fina. Queda un hueco vacío antes del botón. De flet no hay ninguna captura a ese tamaño.
  - *Evidencia:* docs/screenshots/016/1-choose-split-800-light-es.png; 007/1-choose-split-800-dark-es.png; ls docs/screenshots/018 \| grep 800 → 0 archivos.
  - *Recomendación:* En la ventana mínima, desplazar la página completa en vez de una tarjeta interna, o mostrar menos (F3-05). Agregar capturas de flet a 800 × 624.
- **F3-06 — Los colores calculados (fila seleccionada, puntero encima, enlace al pasar el puntero) no tienen prueba de contraste y dos de ellos no alcanzan AA**
  - *Impacto:* En tema oscuro, el texto secundario sobre una fila seleccionada baja a 4,36:1. En claro, un enlace con el puntero encima baja a 4,24:1. La fila seleccionada pierde el color de error a propósito, así que la primera fila nunca se ve en rojo.
  - *Evidencia:* Cálculo propio con palette.py y colors.blend (selected = blend(accent, card, 0.18)); test_brand.py:23-39 solo prueba los pares base; flet/visuals/look.py:91-93; ADR-0027 afirma un mínimo de 5,0:1, pero warning sobre ground da 4,59:1.
  - *Recomendación:* Incluir en la prueba los colores mezclados y el anillo de foco (3:1). Ajustar «selected» o «muted» en oscuro. Agregar a cada fila una señal de estado que no sea solo color (ícono o palabra) también en Revisar. Corregir la cifra del ADR.
- **F3-07 — Pequeñas diferencias entre las tres interfaces que restan pulido**
  - *Impacto:* En ttk y Qt hay una tarjeta dentro de otra en Inicio. Ajustes y Ayuda no tienen ícono en el riel ancho y en el compacto salen como ⚙ y ? pequeños. ttk muestra 3 filas en Revisar y las otras dos interfaces 5. Los radios de Ajustes de Qt están desalineados.
  - *Evidencia:* docs/screenshots/007/0-home-light-es.png, 016/0-home-dark-es.png frente a 018/0-home-light-es.png; 018/1-choose-compact-light-es.png; 016/6-settings-light-es.png.
  - *Recomendación:* Íconos propios para Ajustes y Ayuda, quitar la tarjeta interior y llevar una lista de paridad visual que se revise con las capturas lado a lado.
- **F3-09 — Las capturas de referencia tienen huecos que impiden ver estados clave**
  - *Impacto:* No hay capturas con foco del teclado ni de flet a tamaño mínimo. Los Ajustes de flet se cortan sin una barra visible que indique que hay más contenido. Así, las regresiones de estos puntos pasan sin que nadie las vea.
  - *Evidencia:* ls docs/screenshots/018 (ningún *-800-*); ninguna captura con foco en 007/016/018; 018/6-settings-light-es.png.
  - *Recomendación:* Generar en cada interfaz las capturas de ventana mínima, de foco en el botón principal y en una tarjeta, y de Ajustes desplazado. En flet, mostrar la barra de desplazamiento o un degradado.

</details>

### Frontend · Claridad es cariño — 7,5/10

Después de leer a los ocho auditores mantengo el diagnóstico: el flujo de las ventanas se entiende, tranquiliza y casi siempre dice qué hacer. Los problemas son de precisión en los textos, no de concepto. El debate cambia el orden de prioridades. Lo más grave para quien no sabe de tecnología es que algunos mensajes prometen algo que el producto no cumple. «Copiar Detalles» dice que cambió los nombres de tus archivos, y lo comprobé: un nombre entre comillas pasa intacto (B4-01). Algunos errores mandan a «Dividir» archivos que Dividir no acepta (B4-02). Y para reportar un fallo se pide adjuntar el resumen, que trae nombres privados, a través de un «issue» con cuenta de GitHub. Por eso la promesa rota de privacidad pasa a ser mi hallazgo principal: reúno la parte de los textos que me toca en un solo punto, F4-06. Bajo a media «Resumen» en el paso 1. La confusión es real, pero sacarlo de ahí contradice la especificación 009 (AC-10). Los textos viejos («Convierte más») y el subtítulo «Nada se escribe…» mientras se escribe siguen confirmados; el segundo coincide con F1-07. Sobre la pregunta del dueño, desde esta mirada: que la CI tarde más de 20 minutos no es normal y se puede reducir (B2-02, F2-07). La publicación de 6 a 9 minutos sí es razonable. Lo que sí afecta a la persona es que la App Clásica tarda unos 5 s en abrir: sin ninguna señal, alguien no técnico vuelve a hacer doble clic. Todo se arregla cambiando textos y con cambios pequeños en el presentador. Nota: 7,5/10.

**Fortalezas que vio:**

- Hay frases que tranquilizan en cada momento sensible: «Nada se escribe hasta que confirmes», «Tus originales nunca se modifican», «100 % local · nada sale de tu equipo» y «Tus archivos están en: …». Son el núcleo de «Claridad es cariño» y no deben perderse.
- Los errores siempre traen una acción concreta y humana, y nunca se muestran trazas técnicas. Hay que conservar esa regla y corregir solo las acciones que no se pueden cumplir (B4-02).
- Las tarjetas y las filas combinan número, palabra y color («Con error:», «Omitido:», «Detenido:»), así que el significado no depende solo del color.
- La Ayuda explica Markdown en una frase excelente y toma los nombres de los botones de los botones reales (presenter/screens/help.py). Es el modelo a seguir para el resto del catálogo.
- Todo botón principal deshabilitado dice por qué (screens/primary.py), con mensajes amables. Coincido con F1 en que es una fortaleza.
- El español es natural, con tuteo coherente y plurales .one/.other en la ventana. Hay una prueba que verifica que los dos idiomas tengan las mismas claves.
- Los textos de la terminal están separados ([terminal]): la ventana no habla de --flags y la terminal no habla de botones.
- El diálogo «¿Qué Sigue?» es claro: tres tarjetas grandes con ícono y una sola casilla explicada.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F4-06 | 🔴 Alta | pequeño | alta | Reportar un problema: el texto promete ocultar los nombres y no lo cumple, pide adjuntar el resumen con nombres privados y exige un «issue» con cuenta de GitHub |
| F4-05 | 🟠 Media | pequeño | alta | Durante la conversión, el subtítulo sigue diciendo «Nada se escribe hasta que pulses Convertir» |
| F4-04 | 🟠 Media | pequeño | alta | Hay textos viejos que nombran botones u opciones que ya no existen |
| F4-03 | 🟠 Media | pequeño | alta | La nota del Inicio («Las herramientas cambian archivos, nunca lo que hay dentro») inquieta en vez de tranquilizar |
| F4-01 | 🟠 Media | pequeño | media | La etiqueta «Resumen» del paso 1 se confunde con un resumen del documento |
| F4-07 | 🟠 Media | pequeño | alta | Las notas de Resultados y del Resumen usan jerga técnica, y la palabra «lote» aparece por toda la ventana |
| F4-02 | 🟠 Media | pequeño | alta | La promesa principal es «Markdown», pero la palabra solo se explica dentro de la Ayuda |
| F4-09 | ⚪ Baja | pequeño | alta | El mismo concepto se llama distinto en la misma pantalla, y las tarjetas no explican sus números |
| F4-08 | ⚪ Baja | medio | media | Resultados muestra rutas largas como texto, y «Abrir Carpeta de Resultados» abre todas las carpetas a la vez |
| F4-10 | ⚪ Baja | pequeño | media | Encabezados incompletos y títulos repetidos con dos versiones |

<details><summary>Detalle técnico y evidencia</summary>

- **F4-06 — Reportar un problema: el texto promete ocultar los nombres y no lo cumple, pide adjuntar el resumen con nombres privados y exige un «issue» con cuenta de GitHub**
  - *Impacto:* Cuando algo falla de verdad, que es el momento de más angustia, la persona sigue tres textos y cada uno la expone o la frena. El aviso de «Copiar Detalles» le asegura «Cambiamos los nombres de tus archivos y carpetas», pero un nombre entre comillas, por ejemplo el de un paciente, se publica intacto. La acción del error le dice «avísanos y adjunta el resumen», y el resumen trae nombres y carpetas. Y todo termina en un «issue» de GitHub con cuenta, que para el público general es jerga y una barrera.
  - *Evidencia:* Reproduje el regex de screens/details.py:13-14 (_START exige unidad, \\ o barra inicial): "KeyError: 'Historia clinica Ana.pdf'" queda sin cambios; 'D:\Clientes\Ana Ruiz\ClearMD_Output' queda como '<file> Ruiz\ClearMD_Output'. es.toml:472 details_copied = «…Pégalos en tu issue en github.com/… Cambiamos los nombres de tus archivos y carpetas por <archivo>…». es.toml:17 (conversion_failed.action) = «…avísanos y adjunta el resumen.»; es.toml:49 (worker_crashed) = «…avísanos.» sin canal. Coincide con B4-01 y B4-05.
  - *Recomendación:* Primero, que el texto no prometa más de lo que hace: «Intentamos ocultar los nombres de tus archivos; antes de enviarlo, revisa que no quede ninguno». Ampliar además el ocultamiento a los nombres del lote, que el presenter conoce. Cambiar «adjunta el resumen» por «copia solo la línea de Detalle Técnico (el resumen tiene los nombres de tus archivos)». Usar una sola clave de catálogo para «cómo reportar», con palabras simples («cuéntanos el problema»), el canal concreto y, si se puede, una vía sin cuenta. GitHub puede quedar como segunda opción.
- **F4-05 — Durante la conversión, el subtítulo sigue diciendo «Nada se escribe hasta que pulses Convertir»**
  - *Impacto:* Mientras ClearMD ya está escribiendo archivos, la pantalla afirma que no se escribe nada. Justo cuando la persona se pregunta «¿está funcionando?», el texto contradice a la barra de progreso.
  - *Evidencia:* es.toml:528, :614 y :662 (convert_subtitle de Convertir, Dividir y Unir). presenter/chrome/header.py:19-27: el estado solo cambia la línea superior (eyebrow) y el subtítulo sigue fijo. Capturas docs/screenshots/018/3-convert-light-es.png y 016/3-convert-light-es.png. Coincide con F1-07.
  - *Recomendación:* Que header_of elija el subtítulo según el estado. Durante la conversión: «Tus resultados se están guardando; puedes cancelar cuando quieras: lo ya terminado se conserva». Al terminar: «Listo: mira los Resultados».
- **F4-04 — Hay textos viejos que nombran botones u opciones que ya no existen**
  - *Impacto:* La ventana le pide a la persona que busque «Convierte más», «Divide más» o «Une más», y ningún botón se llama así. Además le da listas de formatos incompletas. Quien sigue las instrucciones al pie de la letra se pierde y deja de confiar en los textos.
  - *Evidencia:* es.toml:488 done y :491 nothing_written («o Convierte más»); :629 y :674 («Divide más», «Une más»). Se muestran como pista del botón deshabilitado (presenter/screens/primary.py:38, :63). El botón real es «¿Qué Sigue?» → «Convertir Otra Vez». [tool.split] gui.plan.nothing: «PDF o Markdown», frente a split_body: «PDF, Markdown, texto, CSV o Excel». split_help no menciona la división por palabras. recursive_help dice «carpetas» y no «subcarpetas».
  - *Recomendación:* Corregir los textos: «…mira los Resultados o pulsa {more}», interpolando el nombre del botón; listar los cinco formatos; agregar «o en partes de unas N palabras»; escribir «también se incluyen sus subcarpetas». Agregar una prueba que no permita nombres de botón escritos a mano en el catálogo.
- **F4-03 — La nota del Inicio («Las herramientas cambian archivos, nunca lo que hay dentro») inquieta en vez de tranquilizar**
  - *Impacto:* Una persona sin conocimientos técnicos lee «cambian archivos» y entiende que ClearMD va a modificar sus documentos, justo el miedo que el resto de la app intenta quitar. Para Convertir, además, la frase es falsa en sentido literal.
  - *Evidencia:* es.toml:586 files_note; captura docs/screenshots/018/0-home-light-es.png. La contradice [gui.help] where: «Tus originales nunca se modifican».
  - *Recomendación:* «Tus originales nunca se modifican: ClearMD crea archivos nuevos en una carpeta ClearMD_Output. Dividir y Unir no cambian ni una palabra del contenido».
- **F4-01 — La etiqueta «Resumen» del paso 1 se confunde con un resumen del documento**
  - *Impacto:* En una herramienta para preparar documentos para una IA, «Resumen: Markdown / Markdown + PDF / Solo PDF» hace creer que ClearMD va a resumir el documento. En realidad es un informe de lo que pasó con cada archivo.
  - *Evidencia:* es.toml:561 summary_title = «Resumen:»; :423 «Formato del Resumen»; capturas 016/1-choose-light-es.png y 018/1-choose-split-light-es.png. spec/features/009_human-summary/spec.md:33 AC-10 pone a propósito el formato en el paso 1. ADR-0016 fija solo el nombre del archivo.
  - *Recomendación:* Cambiar solo la etiqueta de la ventana: «Informe de Lo Que Pasó:», con la ayuda «un archivo que dice qué pasó con cada documento». El nombre Resumen_ClearMD.md puede quedarse. En la ronda 1 propuse además sacar Resumen e Imágenes del paso 1: lo retiro de aquí y lo reúno con F3-05, porque contradice la especificación 009 AC-10 y esa decisión es del dueño.
- **F4-07 — Las notas de Resultados y del Resumen usan jerga técnica, y la palabra «lote» aparece por toda la ventana**
  - *Impacto:* Las notas son lo que la persona lee para saber si su documento quedó bien, pero varias solo las entiende un técnico. «Cambios rastreados» ni siquiera es el término de Word en español («control de cambios»).
  - *Evidencia:* es.toml:272 encoding_guessed («la codificación del texto no estaba declarada y se dedujo»); :278 formula_kept_as_source («fuente StarMath»); :309 tracked_changes («cambios rastreados»); «lote» en :488, :491 y en open_when_done_help. Coincide con B3-07.
  - *Recomendación:* Lenguaje cotidiano con la cantidad al principio. Por ejemplo, encoding_guessed: «ClearMD tuvo que adivinar cómo estaba escrito el texto: revisa que tildes y eñes se vean bien» (esta nota será clave si se corrige B1-01). StarMath: «2 fórmulas quedaron escritas tal como estaban en el original». «Control de cambios». En lugar de «lote», «esta tarea».
- **F4-02 — La promesa principal es «Markdown», pero la palabra solo se explica dentro de la Ayuda**
  - *Impacto:* Quien nunca oyó la palabra no sabe si el producto le sirve ni qué va a recibir. La muy buena explicación de la Ayuda no aparece en el momento en que la persona decide.
  - *Evidencia:* es.toml [gui.home] convert = «Convertir a Markdown»; [gui.app] subtitle; [gui.welcome] no explica qué es. La explicación solo está en [gui.help] markdown. Capturas 018/0-home-light-es.png y 018/0-welcome-light-es.png.
  - *Recomendación:* Una línea en la bienvenida y bajo la tarjeta Convertir, tomada de la Ayuda: «texto simple y ordenado que las IA leen mejor que un PDF o un Word».
- **F4-09 — El mismo concepto se llama distinto en la misma pantalla, y las tarjetas no explican sus números**
  - *Impacto:* «Skipped» frente a «Left out:», «Omitidos» frente a «No Incluidos». En Revisar no queda claro si «Ya Existen 1» está dentro de «Por Convertir 6». Cada pequeña duda resta confianza.
  - *Evidencia:* en.toml [gui.result] stat_skipped frente a word_skipped; es.toml [summary] left_out = «No Incluidos» frente a [gui.result] stat_skipped = «Omitidos». Capturas 018/2-review-light-es.png y 018/4-results-light-es.png. B4-08 muestra el caso extremo: con 4 conservados, el titular dice «Ninguno… se pudo convertir».
  - *Recomendación:* Un término por concepto en la ventana, el Resumen y las filas, y una línea corta bajo cada número de las tarjetas.
- **F4-08 — Resultados muestra rutas largas como texto, y «Abrir Carpeta de Resultados» abre todas las carpetas a la vez**
  - *Impacto:* Para responder «¿dónde están mis archivos?» aparecen rutas completas que no se pueden pulsar, y el único botón abre una ventana del explorador por cada carpeta, todas de golpe.
  - *Evidencia:* docs/screenshots/018/4-results-light-es.png; presenter/intents/results.py:31-35 llama a open_folder() por cada carpeta de result_folders().
  - *Recomendación:* Sin cambiar la estructura (ADR-0019): un botón «Abrir» por carpeta, con un nombre corto que diga qué contiene, y que el botón general abra solo la primera.
- **F4-10 — Encabezados incompletos y títulos repetidos con dos versiones**
  - *Impacto:* Un encabezado que es media frase («Los Resultados Van») se lee como un error en un producto que se presenta como cuidado.
  - *Evidencia:* es.toml [gui.main] output_title = «Los Resultados Van», frente a pick_output_title = «¿Dónde Van los Resultados?»; [summary] kept = «Conservados (el Resultado Ya Existía)»; [gui.result] problems = «Lo que Necesita Tu Atención» frente a [summary] attention = «Necesita Tu Atención».
  - *Recomendación:* Usar «¿Dónde Van los Resultados?», escribir los paréntesis explicativos en minúscula inicial y unificar el título de atención. Agregar una prueba de Title Case sobre las claves de títulos, según la doctrina del dueño.

</details>

## 10. Lecciones para las plantillas

Las lecciones de esta segunda auditoría se incorporaron a
[`docs/lessons-learned.md`](../lessons-learned.md), Parte XI (en inglés, como el resto de ese archivo).
Lo que propuso la conciliadora:

- Producto: toda garantía escrita en un ADR o en un mensaje («una celda es una celda», «ocultamos tus nombres», «nada se escribe aún») lleva una prueba fija con su caso difícil. Si no se puede garantizar, el texto dice «intentamos».
- Producto: un solo decodificador de texto en todo el producto, con un archivo cp1252 con ñ y tildes en las pruebas.
- Producto: regla de honestidad de la salida: lo que se reconstruye por heurística, o no se entrega como se pidió, se dice en el resumen.
- Producto: los nombres de salida dependen solo del original, nunca del idioma ni del lote, y las reglas por herramienta viven en el backend.
- Producto: la cancelación no es un error, con una prueba en cada etapa larga, incluido el paso final.
- Producto: las constantes de estimación calibradas con datos sintéticos se revalidan con documentos reales (escaneados, con imágenes) antes de que puedan omitir un archivo.
- Producto: pruebas de catálogo baratas: prohibir «(s)», detectar jerga, interpolar siempre los nombres de botón y tener una sola clave «cómo reportar».
- Aplicar una auditoría: después de aplicar sus mejoras, conviene una pasada corta que verifique cada recomendación en el código (resuelto, parcial o pendiente), porque varias quedaron a medias: Unir en la CLI, imágenes en la CLI, archivo vacío.
- Aplicar una auditoría: priorizar correcciones de verdad sobre controles nuevos. Cada confirmación, deshacer u opción extra debe justificarse frente a «Claridad es cariño».
- CI: perfilar dónde se va el tiempo antes de paralelizar; un fixture autouse con costo global vive solo en la carpeta que lo necesita, y conviene subir siempre el JUnit.
- Empaquetado: con instalador, la copia instalada va en modo carpeta, y el tiempo hasta la ventana se mide en la CI.
- Esta segunda auditoría: la regla de reverificar (reverified) funcionó, pero algunas severidades subieron sin reverificar. La plantilla del debate debería exigir reverified=true para subir una severidad y prohibir fusiones que suban la severidad sin evidencia nueva.
- Esta segunda auditoría: el conciliador debe ejecutar al menos los tres hallazgos de más valor (aquí cp1252, el reparto en N partes y Copiar Detalles) y la medición que responde la pregunta del dueño. Costó minutos y dio certeza.
