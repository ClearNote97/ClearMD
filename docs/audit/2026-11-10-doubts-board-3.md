# Junta de Dudas n.º 3 — La 2.14.0, lo Oculto, los Capítulos LaTeX y el Resumen

> **Fecha:** 2026-11-10 · **Para:** el dueño del producto. Documento en español por excepción a ADR-0011.
> **Por qué se convocó:** la [quinta auditoría](./2026-11-10-audit-boards-v5.md), la última de la línea 2.x, te dejó
> cuatro decisiones abiertas. Respondiste «Procedan con lo de la junta», así que una junta aparte las decidió.
> Datos completos: [`2026-11-10-doubts-board-3.json`](./2026-11-10-doubts-board-3.json).

## Quiénes Opinaron

- **Asesora de «Claridad es cariño»**
- **Asesor de ingeniería**
- **Abogada del diablo**
- **Síntesis**: comprobó en el código lo que importaba, decidió cada duda y registró el desacuerdo.

Una corrección antes de empezar. La pregunta sobre LaTeX que recibió la junta estaba mal planteada: hablaba de
un capítulo incluido dos veces dentro de un mismo archivo. La abogada del diablo lo notó. El problema real
(hallazgo B3-07) es otro: al convertir la carpeta de una tesis, cada capítulo sale dentro de main.md **y además**
suelto. La junta decidió sobre el problema real.

## Resumen para Ti

La junta resolvió las cuatro preguntas. Esto es lo que decidió, en palabras sencillas.

1. **Dónde va lo pendiente.** Se hace una versión 2.14.0 corta, sin auditoría, solo con arreglos que hacen que
   la app diga la verdad: las mejoras 1, 2, 3, 4, 6, 7 y 9, y una parte de la 5, la 10 y la 11. Lo grande va a la
   3.0.0: la mejora 8, el resto de la 5, la 10 y la 11, y lo de LaTeX. La lista de la 2.14.0 queda cerrada aquí. No
   habrá una sexta auditoría con otro nombre: cada arreglo se comprueba con una prueba que reproduce el fallo, y la
   primera auditoría de la 3.0.0 revisa que todo quedó bien.

2. **Lo oculto en Excel, Word, PowerPoint y páginas web.** Se extiende tu regla del PDF: lo que la persona no ve al
   abrir el archivo no se le entrega a la IA, y siempre se avisa. En la 2.14.0, las hojas ocultas de Excel quedan
   fuera, con un aviso que las nombra. Los párrafos ocultos de un ODT, que ya quedaban fuera en silencio, ahora se
   avisan. En Word y PowerPoint, la 2.14.0 solo avisa que hay texto o diapositivas ocultas. Quitarlos de verdad lo
   harán los conversores nuevos de la 3.0.0. Las notas del orador se quedan, marcadas, porque el autor las escribió
   para leerlas. Las partes .xlsx de Dividir nunca se tocan.

3. **Los capítulos de LaTeX que salen dos veces.** Sí se corrige. Un capítulo que ya entró en main.md quedará en
   «Dejados fuera: es parte de main.tex», en vez de salir suelto y mal. Pero va a la 3.0.0, como primera etapa
   propia, porque cambia cómo se planea la carpeta y conviene que lo revise una auditoría. En la 2.14.0 solo se
   arregla un error que ya existe hoy: con «Reemplazar si el original cambió», editar un capítulo no renovaba
   main.md.

4. **«Markdown + PDF» como resumen por defecto.** No, por ahora. El resumen sigue en «Markdown». En la 2.14.0, la
   pantalla de Resultados de las tres ventanas dirá en una línea cómo abrir un .md. Se vuelve a hablar en la
   conversación sobre la metodología, antes de la 3.0.0.

Nadie modificó archivos ni hizo commits. Hacen falta una ADR nueva (0056) y notas cortas en cuatro ADR: 0022, 0047,
0048 y 0054.

## Las Decisiones

### D1. Dónde van las once mejoras y lo demás de la quinta auditoría

**Decisión:** (c) dividir, con una 2.14.0 corta y cerrada.

En la **2.14.0** (versión menor, sin auditoría):

- **Mejora 1:** Resultados no dice «todo bien» cuando un documento tiene un aviso que pide revisarlo.
- **Mejora 2:** un resultado sin texto es «fallido» en todas las herramientas y formatos.
- **Mejora 3:** una sola revisión previa de seguridad para Convertir, Dividir y Unir.
- **Mejora 4:** las partes de un CSV conservan su codificación y sus acentos.
- **Mejora 5, solo su parte de verdad:** el aviso dice qué textos quitó; si quitó líneas en negrita del tamaño
  del texto o líneas con un número que avanza, pasa a «conviene revisar» (8.13); y la carta de 2 páginas con el
  pie dibujado después del encabezado se arregla mirando la posición de cada línea, no el orden en que se dibujó.
  No se reordenan las líneas de todos los PDF.
- **Mejora 6:** Dividir acepta las hojas ocultas, y cada causa de fallo tiene su propio consejo.
- **Mejora 7:** Revisar avisa qué PDF puede tardar demasiado.
- **Mejora 9:** cada mensaje dice lo que pasó (Dividir, la terminal y el README).
- **Mejora 10, solo la fuga:** los valores «solo para esta tarea» del atajo de Dividir nunca se guardan en disco.
- **Mejora 11, solo la frase falsa:** el instalador deja de llamar a la App Moderna «la que mejor funciona con un
  lector de pantalla» hasta que se pruebe.
- De D2: las hojas ocultas de Excel fuera y avisadas, el aviso de párrafos ocultos en ODT y el aviso de texto o
  diapositivas ocultas en Word y PowerPoint.
- De D3: solo el arreglo de «Reemplazar si el original cambió» para los .tex.

En la **3.0.0** (con sus propias auditorías):

- **Mejora 8:** párrafos, bibliografías y listas «a)» del PDF.
- **El resto de la mejora 5:** ordenar en general las líneas del PDF por su altura.
- **El resto de la mejora 10:** guardar solo los ajustes que la persona eligió, y sumar la lista al volver a
  Convertir (F1-02).
- **El resto de la mejora 11:** foco con nombre al cambiar de paso, anunciar el final y una prueba real con NVDA o
  Narrador.
- **D3 completa** (capítulos de LaTeX), como primera etapa propia, antes de cambiar markitdown.
- **El resto de D2:** quitar de verdad lo oculto en Word, PowerPoint y páginas web, y las filas y columnas ocultas
  de Excel.
- Los demás hallazgos de 8.26 (títulos sueltos, formato de los números de Excel, numeración de ecuaciones) y los
  menores de 8.27.

**Por qué:** ADR-0055, líneas 26 y 27, dice que corregir algo que era falso es una versión menor, contado en
«Cambios de comportamiento». Todo lo de la 2.14.0 es eso. Ya hay un precedente: quitar el texto invisible del PDF
(ADR-0054) salió en la 2.12.0, una versión menor. Esperar a la 3.0.0 no sirve. La 3.0.0 no tiene fecha: falta
escoger la librería, y antes va la conversación sobre la metodología. Mientras tanto la persona seguiría viendo
«Terminado» con páginas que faltan, o «JosÃ©» en sus datos. Además, la 3.0.0 debe cambiar una sola cosa en las
salidas grabadas (las 109 huellas de tests/golden): el cambio de markitdown. Si llegan juntas otras correcciones,
nadie sabrá por qué cambió cada huella. Lo que va a la 3.0.0 es lo de esfuerzo medio que cambia mucho texto (la 8),
toca las tres ventanas (la 10 y la 11) o cambia cómo se planea una carpeta (D3). Sin una auditoría que lo revise,
es demasiado riesgo.

Una aclaración sobre la mejora 10. Dos asesoras dijeron que cambia el contrato del archivo de ajustes. No es así.
Los nombres de las claves no cambian, y ClearMD ya lee bien un archivo al que le faltan claves: usa el valor por
defecto (use_cases/settings.py:40-51). Va a la 3.0.0 por su costo y su riesgo, no por el contrato. Su parte
pequeña sí es una mentira de hoy: el código promete «solo para esta tarea, nunca guardado»
(intents/tools.py:59), pero cualquier guardado posterior escribe esos valores (tools.py:123). Esa parte va en la
2.14.0.

**Cómo:** se comprueba la 2.14.0 sin una sexta auditoría, así:

1. Cada arreglo empieza con una prueba que falla antes del cambio. Se usa el archivo de prueba que describió la
   auditoría (el libro con la hoja oculta «Listas», la diapositiva vacía, el CSV con «José»).
2. Cada cambio en las salidas grabadas se revisa uno por uno y se explica con un punto de esta lista.
3. La CI pasa en Windows, macOS y Linux.
4. Cada cambio lleva su revisión de código, y la mejora 3 también una revisión de seguridad, con pruebas en las
   tres herramientas (Excel trampa, contraseña, memoria).
5. Las notas de la versión traen una tabla: hallazgo de la quinta auditoría → prueba que lo cubre.
6. Tú pruebas la app empaquetada con capturas en docs/, como siempre.
7. La primera auditoría de la 3.0.0 empieza revisando esa tabla.

Esto **no** es una auditoría: no hay juntas, ni nota, ni búsqueda de hallazgos nuevos. Si al trabajar aparece algo
nuevo, va a la 3.0.0, salvo que sea un fallo causado por la propia 2.14.0. Cada cambio de comportamiento va en
«Cambios de comportamiento»: por ejemplo, «Nada que convertir» ya no termina con código 0, y Dividir deja fuera
lo que la revisión de seguridad rechaza.

**Desacuerdo registrado:** Las tres opiniones eligieron (c), pero con listas distintas. La asesora de claridad y
el asesor de ingeniería ponían la mejora 5 entera; se adopta la división de la abogada del diablo. Ninguna ponía
la fuga de la mejora 10 en la 2.14.0; la síntesis la añade porque el código promete algo que no cumple. El asesor
de ingeniería ponía D3 en la 2.14.0; ver D3. Las tres rechazan (b): mezclar los arreglos con el cambio de
markitdown.

### D2. Lo oculto en Word, Excel, PowerPoint y páginas web (hallazgo 8.12)

**Decisión:** (c), ajustada. Una ADR nueva (0056) extiende a todos los formatos el principio de ADR-0054. La regla:
**lo que la persona no ve al abrir el archivo queda fuera, y el resumen dice qué se quitó.** Eso incluye las hojas
ocultas y muy ocultas, las filas y columnas ocultas, las diapositivas ocultas, el texto oculto de Word y, en las
páginas web, lo marcado como oculto en el propio HTML. Hay dos excepciones. Las notas del orador se quedan, marcadas
como notas, porque el autor las escribió para leerlas. El texto blanco no se quita, igual que en el PDF. Las partes
.xlsx de Dividir nunca se tocan (ADR-0047).

Calendario:

- **2.14.0:** las hojas ocultas y muy ocultas de Excel quedan fuera, con un aviso que las nombra. Los párrafos y
  secciones ocultos de un ODT, que ya quedaban fuera, ahora se avisan. Word y PowerPoint solo avisan: «este archivo
  tiene texto oculto (o diapositivas ocultas) y se incluyó».
- **3.0.0:** los conversores nuevos de Word y PowerPoint dejan fuera el texto y las diapositivas ocultas desde el
  primer día. Es un requisito del experimento: el conversor elegido debe poder verlos. Las páginas web dejan fuera
  lo oculto del propio HTML. Excel deja fuera las filas y columnas ocultas.

**Por qué:** El caso del informe lo dice todo: «la IA me citó la hoja de salarios que yo tenía escondida». Una marca
como «Hoja oculta:» no protege nada, porque quien lee es la IA. Además, ClearMD no conoce la intención del autor.
Solo sabe lo que la persona ve, y ese es el criterio de ADR-0054. Quitar es reversible: el original queda intacto,
el aviso dice qué se quitó, y la persona puede mostrar la hoja y volver a convertir. Una filtración no tiene vuelta
atrás. Las celdas visibles conservan sus valores, así que quitar una hoja de listas no le quita nada a la IA.

Las hojas van ya porque es barato y seguro. El lector de Excel da el estado de cada hoja aun en modo de solo
lectura (openpyxl/reader/excel.py:228-229), y el conversor de ClearMD recorre todas las hojas sin mirarlo
(xlsx.py:115). Las filas y columnas esperan porque ese modo no las da (ReadOnlyWorksheet no tiene
row_dimensions): habría que leer el XML de cada hoja. Word y PowerPoint pasan hoy por markitdown, que la 3.0.0
reemplaza; quitar ahí lo oculto sería código que se tira. Avisar sí cabe, y ClearMD ya lee word/document.xml para
buscar celdas combinadas (markitdown_adapter.py:163-170). Las páginas web necesitan un filtro propio antes del
modo artículo y cambian muchas salidas: mejor con auditoría.

**Cómo:** Antes de escribir código, un archivo de prueba por caso: una hoja oculta, una muy oculta, un libro con
todas las hojas ocultas (debe fallar con su motivo, no salir vacío), un párrafo oculto en ODT, un texto con
w:vanish (y otro con w:vanish w:val="0", que no está oculto), una diapositiva oculta y una sola nota del orador.
Nadie reprodujo B2-01 en la quinta ronda (informe v5, línea 115), así que estas pruebas son lo primero. El aviso nuevo
de Word y PowerPoint lee el XML bajo la misma revisión de seguridad de ZIP (mejora 3). Los avisos son tipos de nota
nuevos (schemas/notes.py), en inglés y español, en palabras humanas: «Este libro tenía 1 hoja oculta (Salarios);
quedó fuera. Para incluirla, muéstrala en Excel y vuelve a convertir.» Un aviso de que algo se quitó pide revisar;
no va en la parte tranquila. En Dividir, la hoja oculta va dentro de cada parte .xlsx sin tocar, y la Markdown de
esa parte la deja fuera, como Convertir. La ADR lo dice claro para que nadie «arregle» una cosa con la otra.

**Desacuerdo registrado:** La asesora de claridad quería conservar las hojas y filas ocultas, marcadas. El asesor de
ingeniería quería quitar solo las hojas muy ocultas y marcar las ocultas normales. No se adopta: la marca no evita
que la IA lea los salarios. La abogada del diablo quería quitar las hojas recién en la 3.0.0, por el contrato. No se
adopta: la 2.12.0 ya quitó texto invisible del PDF como versión menor, y Excel es un conversor propio que la 3.0.0 no
toca. Queda un límite aceptado: en la 2.14.0 las filas y columnas ocultas de Excel y lo oculto de las páginas web
siguen pasando, sin aviso. Por eso el aviso de la 2.14.0 nombra solo las hojas, y no promete «todo lo oculto».

### D3. Capítulos de LaTeX que salen dos veces (B3-07, ADR-0022:27)

**Decisión:** Sí, se enmienda ADR-0022, línea 27, pero en la 3.0.0, como primera etapa propia y en sus propios
commits, antes del cambio de markitdown. La nueva regla: en una misma tarea, un .tex que otro .tex de la tarea
incluyó de verdad, sin error, queda en «Dejados fuera: es parte de main.tex». El aviso añade que se puede convertir
ese archivo solo. Un archivo que solo define macros e incluye otro tampoco sale como fallido. Si la inclusión falló
(fuera de la carpeta, por un límite, un ciclo) o el principal queda fuera por otro motivo, el capítulo se convierte
suelto, como hoy. Si la persona elige un capítulo suelto, se convierte. La numeración de ecuaciones (\ref, \eqref)
no entra en esta enmienda.

En la **2.14.0** solo se arregla un error que ya existe hoy. Con «Reemplazar si el original cambió», ClearMD compara
solo la fecha de main.tex con la de main.md (use_cases/changes.py:13). Si cambias ch1.tex, main.md se queda viejo.
El arreglo es prudente: un .tex cuenta como cambiado si cualquier .tex de su carpeta, o de las de adentro, es más
nuevo que su resultado. Solo mira fechas, no lee archivos. En la duda, convierte de nuevo.

**Por qué:** El problema real lo confirma el código: includes.py:151-175 solo detecta ciclos dentro de un mismo
documento (línea 160), y ADR-0022:27 pide convertir los capítulos también por separado. Las rutas se resuelven desde la carpeta
del principal (includes.py:3), así que el capítulo suelto da avisos falsos de «no encontrado» y deja las macros sin
expandir. La IA recibe cada capítulo dos veces, una bien y otra mal. Pero el arreglo no es pequeño. Hay que saber qué
incluye cada documento antes de decidir qué se deja fuera, con un paso nuevo en el plan (planning.py:117-173) que
lee archivos de la persona en el proceso de la ventana, antes del trabajador. Ese paso tiene que usar el mismo
resolutor seguro y los mismos límites (200 archivos, profundidad 8, 250 MiB). Además cambia qué archivos aparecen
en OutputMD: quien convertía la carpeta para tener ch1.md ya no lo tendrá. Es de severidad media (8.26), no alta.
Hacerlo sin auditoría es mucho riesgo para un daño medio. Y como la 3.0.0 no toca LaTeX, hacerlo allí en su etapa
propia no mezcla las salidas grabadas con las de markitdown.

**Cómo:** En la 3.0.0: un motivo nuevo de «Dejado fuera» (schemas/errors.py) con el nombre del principal, sus
textos en inglés y español, la línea del resumen y de la terminal, y las huellas de la tesis reescritas a propósito.
Pruebas con tests/fixtures/tex/thesis, con el principal que falla, con un capítulo usado por dos principales, con un
ciclo y con un capítulo elegido solo. Ese mismo cambio hace exacta la regla de «Reemplazar si el original cambió»:
comparar con la fecha más nueva del principal y de sus incluidos. Hasta entonces, macros.tex sigue saliendo con su
❌, como hoy. Es honesto, aunque feo.

**Desacuerdo registrado:** La asesora de claridad y el asesor de ingeniería querían D3 en la 2.14.0, como
corrección de algo falso. No se adopta, por el tamaño del cambio y el paso nuevo que lee archivos sin una auditoría
que lo revise. El propio asesor de ingeniería dijo que D3 era lo primero que podía salir de la 2.14.0. Se adopta su
hallazgo del error de fechas, que entra ya en su forma prudente. La abogada del diablo corrigió la pregunta mal
planteada de la junta, y su versión de la regla es la que se adopta.

### D4. «Markdown + PDF» como resumen por defecto

**Decisión:** Esperar. No se enmienda ADR-0031. El resumen sigue en «Markdown». En la 2.14.0, la pantalla de
Resultados de las tres ventanas muestra una línea, junto al botón de la carpeta: el resumen es un texto que se abre
con el Bloc de notas, y en Ajustes se puede pedir también en PDF. Sin controles nuevos, y no en el paso 1. Se vuelve
a hablar en la conversación sobre la metodología, antes de la 3.0.0.

**Por qué:** Hay un solo valor por defecto, summary_format = "markdown" (backend/schemas/settings.py:20), y lo usa
también la terminal (frontend/cli/flow.py:101). Cambiarlo cambia lo que hace la terminal, y ADR-0055:18 pone sus
valores por defecto en el contrato: sería una versión mayor. Separar un valor solo para las ventanas parte un ajuste
que hoy es uno. Además, dos resúmenes en la carpeta crean otra duda («¿cuál le paso a la IA?»), y el PDF dibuja «?» en
las letras que no son latinas (ADR-0031). La línea va en la pantalla porque quien no sabe abrir un .md nunca leerá
una ayuda escrita dentro del .md.

**Cómo:** Una frase nueva en los catálogos de textos, en inglés y español, que no use la palabra «Markdown» sin
explicarla. Una prueba por ventana de que la línea aparece en Resultados. La terminal no cambia.

**Desacuerdo registrado:** Ninguno sobre el fondo: las tres opiniones dicen esperar. La asesora de claridad y el
asesor de ingeniería querían la línea también dentro del resumen. Se adopta la posición de la abogada del diablo:
solo en la pantalla, donde sirve. Su riesgo de que «esperar» se vuelva «nunca» se cubre llevándolo a la conversación
de la metodología.

## Cambios a las ADR

- **ADR-0056 (nueva), lo oculto en todos los formatos:** lo que la persona no ve al abrir el archivo queda fuera y se
  avisa; las notas del orador se quedan, marcadas; el texto blanco se queda; las partes .xlsx de Dividir no se tocan;
  el calendario 2.14.0 / 3.0.0 de D2.
- **ADR-0054 (texto oculto del PDF):** una línea: «Extendida a todos los formatos por ADR-0056».
- **ADR-0047 (Dividir texto, CSV y Excel):** una línea: las hojas ocultas van sin tocar en cada parte .xlsx, y la
  Markdown de cada parte sigue ADR-0056.
- **ADR-0022 (LaTeX):** enmienda de la línea 27, aceptada ahora y aplicada en la 3.0.0: un .tex que otro de la tarea
  incluyó de verdad queda en «Dejados fuera: es parte de main.tex».
- **ADR-0048 (Reemplazar si el original cambió):** enmienda en la 2.14.0: un .tex cuenta como cambiado si cualquier
  .tex de su carpeta es más nuevo que su resultado; exacto en la 3.0.0 con la enmienda de ADR-0022.
- **ADR-0031 y ADR-0055:** sin cambios. La forma de comprobar la 2.14.0 sin auditoría queda en este informe y se lleva
  a la conversación sobre la metodología.

## Qué Queda para Ti

La junta decidió las cuatro dudas. No tienes que elegir nada para empezar la 2.14.0. Solo tres cosas, cuando
puedas:

- **Si prefieres conservar las hojas ocultas de Excel con una marca**, en vez de dejarlas fuera, dilo antes de la
  2.14.0. Es la decisión con más desacuerdo.
- **Probar la 2.14.0 empaquetada**, con las capturas en docs/, como siempre.
- **En la conversación sobre la metodología, antes de la 3.0.0:** dos temas que la junta deja anotados. Si la forma
  de comprobar una versión sin auditoría se vuelve regla, y si el resumen debe salir también en PDF por defecto. Para
  la prueba con un lector de pantalla de la 3.0.0 hará falta alguien que use NVDA o Narrador en Windows.

## Opiniones Completas

### Asesora de «Claridad es cariño»: hablo por la persona no técnica que usa ClearMD y por la IA que lee lo que sale.

- **D1:** (c), con un corte por «decir la verdad». En 2.14.0: mejoras 1, 2, 3, 4, 5, 6, 7 y 9, y la frase del
  instalador de la 11. En 3.0.0, como primera etapa propia: la 8, la 10 y el resto de la 11; los hallazgos menores
  (8.27) también.
  - *Por qué:* hoy la persona ve «Terminado» y le entrega a la IA un archivo vacío o un CSV con «JosÃ©». Eso no puede
    esperar a una 3.0.0 que ni empezó. ADR-0055 lo admite como versión menor. Así la 3.0.0 empieza limpia. Propuso
    verificar con una prueba por mejora, la tabla hallazgo → prueba, la CI y las capturas.
  - *Riesgos:* un arreglo a medias, como pasó con 5 de las 11 mejoras de v4; meter «una cosita más»; la mejora 5 es
    de esfuerzo medio.
- **D2:** (c) tal como la recomendó la quinta auditoría: lo escondido para no verse, fuera y avisado; las notas del
  orador, las hojas y filas ocultas, marcadas y avisadas. En 2.14.0, marcar las hojas ocultas de Excel y avisar los
  párrafos ocultos de ODT. Web, Word y PowerPoint en 3.0.0.
  - *Por qué:* quitar las notas o las filas sería borrar el trabajo de la persona; no hacer nada deja la puerta
    abierta a instrucciones escondidas.
  - *Riesgos:* el modo de solo lectura quizá no da las filas ocultas; las marcas cambian salidas grabadas; el aviso
    debe ser una línea humana.
- **D3:** sí, en 2.14.0. Un capítulo que ya entró en otro documento queda en «Dejados fuera» con su motivo; un
  archivo de macros no sale como fallido; un capítulo elegido solo se convierte.
  - *Por qué:* la persona ve una ❌ y avisos falsos, y la IA recibe cada capítulo dos veces.
  - *Riesgos:* hacen falta dos pasadas; si se hace mal, un capítulo puede desaparecer.
- **D4:** esperar. Una línea sobre cómo abrir un .md, en Resultados y al inicio del resumen.
  - *Por qué:* dos resúmenes crean la duda de cuál pasarle a la IA.
  - *Riesgos:* si la línea solo va dentro del .md, no ayuda a quien no puede abrirlo.

### Asesor de ingeniería: revisé el código de Excel, ODT, LaTeX, el plan, los ajustes y las salidas grabadas, y medí el costo de cada opción.

- **D1:** (c). En 2.14.0: mejoras 1, 2, 3, 4, 5, 6, 7 y 9, además D3 y la parte barata de D2. En 3.0.0: la 8, la 10,
  la 11, los menores de 8.27 y quitar de verdad lo oculto en Word, PowerPoint y web.
  - *Por qué:* ADR-0055:26-27 admite corregir algo falso en una menor. La 3.0.0 debe cambiar una sola cosa en las 109
    huellas de tests/golden. Propuso verificar con pruebas que reproducen el fallo, huellas explicadas, CI en tres
    sistemas, revisiones de código y seguridad, capturas y una tabla para la primera auditoría de 3.0.0.
  - *Riesgos:* que la 2.14.0 crezca; la mejora 5 es la más arriesgada; la mejora 3 cambia lo que Dividir deja fuera.
- **D2:** (c) en dos pasos. En 2.14.0, avisos en los cuatro formatos y las hojas muy ocultas fuera; las ocultas
  normales, marcadas. En 3.0.0, Word, PowerPoint y web dejan fuera lo oculto, y las filas y columnas de Excel se
  avisan.
  - *Por qué:* openpyxl da el estado de la hoja en solo lectura, pero no las filas ni columnas ocultas; Word y
    PowerPoint pasan por markitdown, que se reemplaza; las notas del orador ya salen como «### Notes:».
  - *Riesgos:* quitar contenido toca el contrato; los límites del CSS por clase y los estilos de Word deben
    escribirse.
- **D3:** sí, en 2.14.0, con un paso nuevo en el plan que sigue los \input con el mismo resolutor seguro; uno o dos
  días.
  - *Por qué:* el plan ya ve todos los .tex, y hay un archivo de prueba.
  - *Riesgos:* ciclos; principal que falla; y encontró un error que ya existe: con «Reemplazar si el original
    cambió», cambiar ch1.tex no renueva main.md.
- **D4:** esperar; la línea «cómo abrir un .md» en el resumen y en Resultados.
  - *Por qué:* el valor por defecto lo comparte la terminal, y cambiarlo sería una versión mayor (ADR-0055:18).
  - *Riesgos:* la línea dentro del .md no ayuda a quien no lo abre.

### Abogada del diablo: busco cómo puede salir mal cada opción, o en qué choca con una ADR o con una decisión tuya, y me quedo solo con lo que aguanta esa crítica.

- **D1:** (c), con una 2.14.0 corta y cerrada: mejoras 1, 2, 3, 4, 6, 7 y 9, y la 5 solo en su parte de verdad, más
  un aviso de contenido oculto. Lo demás, a la 3.0.0.
  - *Por qué:* (b) mezcla dos cambios en las salidas grabadas; (a) completa mete cosas grandes en una menor; la 11 no
    se puede verificar sin una prueba real con NVDA.
  - *Riesgos:* la trampa del nombre: una «revisión aparte» con juntas y nota sería una sexta auditoría. Que sea solo
    la comprobación, sin buscar hallazgos nuevos. Y si aparece algo nuevo, no entra salvo que sea una regresión de la
    propia 2.14.0.
- **D2:** (c) ajustada. Una ADR nueva; en 2.14.0 solo avisar; en 3.0.0 quitar todo lo que la persona no ve,
  incluidas hojas, filas y columnas ocultas. Las notas del orador se quedan, marcadas.
  - *Por qué:* la (c) original falla en su propio ejemplo: con la hoja de salarios marcada, la IA la sigue leyendo.
    Quitar es reversible; filtrar no.
  - *Riesgos:* nadie reprodujo B2-01 en la quinta ronda; leer el XML debe pasar por la revisión de ZIP; posible choque
    con la mejora 6, que hay que escribir claro.
- **D3:** sí, pero corrigió la pregunta: el problema real es ADR-0022:27, no un capítulo incluido dos veces. Lo puso
  en 3.0.0.
  - *Por qué:* cambia qué archivos salen en OutputMD.
  - *Riesgos:* perder un capítulo si se deja fuera sin que el principal lo haya incluido de verdad; macros.tex sigue
    con su ❌ hasta entonces; no mezclar la numeración de ecuaciones.
- **D4:** esperar; la línea en la pantalla de Resultados, no dentro del .md ni en el paso 1.
  - *Por qué:* quien no sabe abrir un .md nunca leerá una ayuda escrita dentro de él.
  - *Riesgos:* que «esperar» se vuelva «nunca»; llevarlo a la conversación de la metodología.
