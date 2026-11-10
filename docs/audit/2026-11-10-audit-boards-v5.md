# Juntas de Auditoría de ClearMD 2.13.0 (Versión 5, la última de 2.x)

> **Fecha:** 2026-11-09 · **Versión auditada:** 2.13.0 · **Para:** el dueño del producto.
> Quinta auditoría, la última de la línea 2.x: agentes nuevos desde cero, cinco expertos por junta y tres conciliadoras con «Claridad es cariño». Anteriores: [primera](./2026-11-08-audit-boards.md), [segunda](./2026-11-09-audit-boards-v2.md), [tercera](./2026-11-09-audit-boards-v3.md) y [cuarta](./2026-11-09-audit-boards-v4.md). Junta de dudas del ciclo: [n.º 2](./2026-11-09-doubts-board-2.md).
> Documento en español por excepción a ADR-0011: está escrito para que el dueño decida.
> Presentación ejecutiva: [ClearMD · Auditoría v5](https://claude.ai/artifact/KMyyF5YerCvaLTepPh48Ur) (privada del dueño).
> Datos completos de las tres rondas: [`2026-11-10-audit-boards-v5.json`](./2026-11-10-audit-boards-v5.json).

## Cómo leer este documento

- **Si tienes 5 minutos:** lee el resumen ejecutivo (sección 1) y las once mejoras recomendadas (sección 4).
- **Para decidir:** las secciones 5 (lo que no conviene hacer) y 6 (desacuerdos abiertos).
- **Para el detalle:** la sección 8 trae cada hallazgo verificado: qué siente la persona, qué se recomienda y
  qué comprobó la junta conciliadora. La sección 9 trae el informe de cada auditor.
- Las referencias técnicas (archivo:línea) quedan para quien implemente; no hace falta entenderlas para decidir.

## 1. Resumen ejecutivo

**Veredicto: 7 de 10**, igual que en la cuarta auditoría. La 2.13.0 cumplió casi todo lo que
prometió arreglar. Lo que queda está en los bordes de las herramientas nuevas, Dividir y Unir, que
todavía no heredan todas las protecciones de Convertir, y en la pantalla final, que a veces dice
"todo bien" cuando el resumen escrito pide revisar algo.

Esta es la **quinta y última auditoría de la línea 2.x**: como decidiste, cinco por versión mayor.
Lo pendiente pasa a la 3.0.0, o a una revisión que pidas aparte.

**Lo que mejoró de verdad con la 2.13.0 (comprobado en el código y en ejecuciones):**

- Las notas cortas de Windows salen bien, incluso las de una o dos letras ("Sí", "¿Qué?", "é").
- Unir respeta el orden en que una persona cuenta (1, 2, 3, 10, 11) y ya no toca el código.
- "Copiar Detalles" manda a la comunidad o al correo, como decidiste.
- Un logo ya no apaga el filtro del texto invisible; solo lo protege una imagen de media página.
- Las marcas raras desaparecieron: "AT&T", "juan_perez" y "[12]" salen limpios y legibles.
- Dividir ya no dice "todo bien" si falta una parte, y solo barre los temporales viejos.
- El "qué hacer" de cada archivo se lee completo, y el foco del teclado se ve.

**De las once mejoras de la cuarta auditoría:** 6 resueltas del todo y 5 en parte; ninguna
empeoró. **De tus decisiones y las de la junta de dudas 2:** casi todas cumplidas; la línea "Parte
N de M" sigue pendiente, como decidió la junta.

**Lo que todavía no es verdad, es decir, lo que una persona vería:**

- **Resultados dice "todo bien" y abre la carpeta** aunque el resumen escrito diga "Necesita Tu
  Atención" (por ejemplo, un PDF con páginas sin texto).
- **Algunos resultados vacíos siguen contando como "convertidos":** una diapositiva vacía, un Excel
  vacío o un Markdown vacío al unir.
- **Dividir no hace las revisiones de seguridad de Convertir:** un Excel trampa que Convertir
  rechaza pasa sin control.
- **Las partes de un CSV cambian la codificación:** Excel muestra "JosÃ©".
- **Un Excel con una hoja oculta falla al dividirse**, con un consejo que no sirve.
- **Una carta de dos páginas con el número abajo** puede conservar "Página 1 de 2" mientras el
  resumen dice que lo quitó.

**La buena noticia:** casi todo es pequeño, y las cinco primeras mejoras hacen que la app diga la
verdad en todos los casos encontrados.

**Junta de dudas de este ciclo:** se convocó la **n.º 2** al aplicar la cuarta auditoría
([informe](./2026-11-09-doubts-board-2.md)). Decidió el escape legible (hecho), respetar "Página
completa" guardada y avisarlo cada vez (hecho), y dejar la línea "Parte N de M" para después.

### Lo que tienes que decidir

1. **Si te acoges a las once mejoras** (sección 4). Recomendación: sí.
2. **Tres desacuerdos abiertos** (sección 6):
   - ¿se extiende el principio de ADR-0054 a lo oculto en Word, Excel, PowerPoint y páginas web?
     (Recomendado: lo escondido para que no se vea, fuera y avisado; lo que el autor usa como
     apoyo, como las notas del orador o las filas ocultas, marcado y avisado.)
   - ¿se enmienda ADR-0022 para que los capítulos de LaTeX no salgan dos veces? (Recomendado.)
   - ¿"Markdown + PDF" como resumen por defecto en las ventanas? (Recomendado esperar.)
3. **Dónde va lo pendiente:** a la 3.0.0, o a una revisión aparte, ya sin auditoría de la línea 2.x.

## 2. Qué se hizo

Se convocaron **dos juntas de cinco expertos y tres conciliadoras**, todas con **"Claridad es cariño"** como criterio, pensando en una
persona del público general que nunca ha abierto una terminal:

| Junta | Integrantes | Qué miró |
| --- | --- | --- |
| **Backend** | 5 expertos | Lógica y robustez · Seguridad y privacidad · Fidelidad del contenido para la IA · Eficiencia y empaquetado · Claridad es cariño |
| **Frontend** | 5 expertos | Lógica y estados · Accesibilidad · Estilo visual UI/UX · Primer uso, instalación e idioma · Claridad es cariño |
| **Conciliadoras** | 3, en cadena, todas con "Claridad es cariño" | La verdad (verifica y reproduce en el código) → Claridad es cariño (ordena por lo que siente la persona) → Doctrina y síntesis clara (revisa los ADR y tus decisiones, escribe para ti) |

**Tres rondas:**

1. **Revisión independiente.** Cada auditor revisó por su cuenta y reprodujo lo que pudo con la app real en el
   contenedor de desarrollo. Resultado: 91 hallazgos.
2. **Debate.** Cada auditor leyó los ocho informes, de las dos juntas, y apoyó, cuestionó, matizó o amplió los
   hallazgos de los demás. Fueron 120 intervenciones. Después corrigió su propio
   informe: 93 hallazgos tras el debate.
3. **Conciliación.** La junta conciliadora volvió al código y a las capturas, unió los duplicados y quedó con
   **27 hallazgos verificados**.

**Lecciones de la primera auditoría, aplicadas como reglas** (`docs/lessons-learned.md`, IX.16):

- Cada auditor leyó los ADR antes de recomendar algo que los contradijera, y lo citó.
- Cada hallazgo dice si su evidencia la comprobó el propio auditor.
- En el debate, subir una gravedad exigía volver a comprobarla en el código (`reverified`).
- La ronda 2 debía listar todo hallazgo propio que retiraba y por qué; la conciliadora comparó las dos rondas.
- Las juntas no leyeron la primera auditoría; solo la conciliadora, para decir qué se resolvió.
- Ningún informe nombra los documentos privados del dueño, y antes de publicar se revisó que así fuera.

**Comprobación de lo retirado:** Comparé la ronda 1 con la ronda 2, y además las dos conciliadoras entre sí. Entre las rondas no se perdió nada: las tres fusiones (B5-09 en B5-08, F4-09 en F3-04/F5-06 y F5-05 en F3-05) conservan su evidencia, como confirmó C1. Entre las conciliadoras sí hubo una pérdida: C2 dejó fuera de su lista, sin mencionarlo, B3-01 (párrafos, bibliografías y listas fundidas en un bloque), que C1 había confirmado con severidad alta. Lo rescato en el puesto 8. También encontré una pérdida que viene de la junta de dudas: su decisión D2 (no cambiar el «Página completa» guardado) desapareció del razonamiento de F4-01, C1 y C2, que volvieron a proponer el cambio. Lo corrijo en las recomendaciones y en lo que no conviene hacer. Por último, nadie probó la carta de 2 páginas de la enmienda de ADR-0030. La probé yo y falla (C-1).

**Lo que la conciliadora de la verdad reprodujo ella misma:**

- B5-01/B1-05: en el contenedor creé una presentación con una diapositiva en blanco y un Excel nuevo vacío; `clearmd b2` dio '2 converted · 0 failed', exit=0, y los .md solo contienen '<!-- Slide number: 1 -->' y '## Sheet'. `clearmd m --merge markdown` con vacio.md (0 bytes), blancos.md (solo espacios) y uno.md dio '3 merged · 0 failed', exit=0.
- B2-02: un Excel sintético de 0,97 MB que crece 257 veces al abrirse. `clearmd --dry-run bomb` lo deja fuera ('grows 257 times… not opened, for safety'); `clearmd --dry-run --split-parts 2 bomb` responde '1 file would be split', exit=0.
- B1-02: CSV sintético en cp1252 con CRLF y acentos, `clearmd t.csv --split-parts 2 --keep pdf`: la parte sale en UTF-8 y con LF (od -c muestra 'J o s 303 251' y '\n'), así que ya no es el mismo archivo.
- B1-01/B5-11: libro sintético con la hoja 'Datos' y una hoja oculta 'Listas', `clearmd hid --split-parts 2 --keep both` → '0 split · 1 failed', exit=1, con el consejo genérico 'Open it in its own program and save it again'.
- B5-02: carpeta vacía, `clearmd e --lang es` → 'Nada que convertir.', exit=0.
- B3-02: PDF sintético de 6 páginas (tests/support/pdf_builder.py) con el encabezado dibujado antes que el pie 'Page N of 6': la salida empieza con 'Page 1 of 6' y la repite 6 veces encima de cada página, y el resumen dice 'headers, footers and page numbers repeated on the pages were left out'.
- B2-03: safe_output('[a [b] c](javascript:alert(1))') y safe_output('[![x](images/a.png)](file:///C:/x.exe)') salen sin cambios, mientras '[ok](javascript:alert(1))' sí se limpia.
- Leído en el código, sin ejecutar: presenter/screens/results.py:35-36 (lo convertido se salta sin mirar las notas), intents/conversion.py:146-169 (estado y apertura de la carpeta), chrome/header.py:26-27, use_cases/settings.py:54-70 (se escriben todos los campos), `git show v2.11.0` (html_strategy='full'), intents/tools.py:60-62, planning.py:134-150 y cli/flow.py:80-85.

**Notas de la conciliadora de Claridad es cariño:** Criterio del orden: primero van los arreglos que hacen que la app diga la verdad (lugares 1, 2, 5, 6, 7 y 9), porque un resultado equivocado que llega a la IA sin aviso es el peor daño para esta persona. Además casi todos son de esfuerzo pequeño. Siguen los dos riesgos de datos y de seguridad que la persona no puede detectar sola (lugares 3 y 4). Valores que bajé: B2-03 (enlaces con corchetes) lo bajo de 'medio' a 'bajo' para el público general. El archivo va sobre todo a una IA, y el clic peligroso exige un documento armado a propósito y un visor que siga enlaces file: o javascript:; conviene arreglarlo, pero no antes que lo anterior. F3-01 (botón debajo de la barra de tareas) lo dejo fuera de los diez, aunque su valor es alto, porque nadie lo vio en Windows. Primero hay que tomar una captura al 150 %; si se confirma, sube al lugar 3 o 4. F4-02 (página de descarga larga) lo bajo de 'alto' a 'medio': molesta y da mala impresión, pero no daña resultados. B2-01 (lo oculto en Word, Excel y web pasa a la IA) es el siguiente en la fila, por ser un daño de privacidad. No entra en los diez porque nadie lo reprodujo en esta ronda y porque amplía una decisión del dueño (ADR-0054); es lo primero que debería decidir después de estos diez. Rechazo cualquier idea de agregar controles nuevos (casillas, más opciones en el paso 1) para resolver estos problemas. Todos se resuelven corrigiendo lo que la app dice o hace, y eso cuida mejor el lema 'Claridad es cariño'. Respeto todas las decisiones del dueño citadas. Solo el lugar 8 toca la enmienda de ADR-0025, y lo dejo marcado como decisión suya.

**Notas por lente (de 0 a 10, tras el debate):**

| Lente | Nota | Hallazgos | Intervenciones en el debate |
| --- | --- | --- | --- |
| Backend · Lógica y robustez | 6,5 | 10 | 10 |
| Backend · Seguridad y privacidad | 7 | 8 | 10 |
| Backend · Fidelidad del contenido para la IA | 6,5 | 10 | 10 |
| Backend · Eficiencia y empaquetado | 7 | 8 | 10 |
| Backend · Claridad es cariño | 6,5 | 10 | 15 |
| Frontend · Lógica y estados | 7 | 9 | 11 |
| Frontend · Accesibilidad | 6 | 10 | 11 |
| Frontend · Estilo visual UI/UX | 7 | 10 | 14 |
| Frontend · Primer uso, instalación e idioma | 6,5 | 10 | 13 |
| Frontend · Claridad es cariño | 7 | 8 | 16 |

## 2b. Qué se resolvió desde la cuarta auditoría (y las decisiones tuyas y de la junta de dudas 2)

| Estado | Mejora o decisión de la cuarta auditoría | Nota de la conciliadora de doctrina |
| --- | --- | --- |
| ◐ Parcial | 1. Si el resultado sale vacío, decir «falló» y explicar qué hacer | Cumplido para el PDF escaneado (código 1, con motivo y OCR). No se cumple con una diapositiva vacía, un Excel vacío, un .md vacío al unir ni con «solo Markdown» al dividir un escaneado. C1 lo reprodujo; la causa está en child.py, que mide un texto con marcas del programa. |
| ✅ Resuelto | 2. Unir en el orden en que una persona cuenta | Lo comprobé: «Capitulo 1, 2, 3, 10, 11» se unen en ese orden. |
| ✅ Resuelto | 3. Que «Copiar Detalles» lleve a la comunidad o al correo | es.toml:517 usa {report}, que nombra las discusiones de la comunidad y el correo para quien no tiene cuenta. |
| ◐ Parcial | 4. Cumplir «abrir un resultado no descarga nada», también en Unir, con marcas legibles | Las marcas legibles y Unir por la puerta única, sí (lo comprobé con una página web). Pero un enlace con corchetes en el texto, o una imagen dentro de un enlace, conserva su destino file: o javascript: (lo reproduje con safe_output). |
| ✅ Resuelto | 5. Mostrar completo el «qué hacer» de cada archivo | En flet, las listas para leer ajustan el texto completo (list_line.py), y en Qt no se recorta (ElideNone). No lo verifiqué en pantalla. |
| ✅ Resuelto | 6. Que Dividir nunca diga «todo bien» si faltan partes | El barrido borra solo lo que tiene más de 24 h (output_files.py), y part_stage falla si falta una parte. Hay una causa nueva y distinta: si una parte está abierta en otro programa, la carpeta queda mezclada (B1-04). |
| ✅ Resuelto | 7. Que un logo no apague el filtro de texto invisible (ADR-0054 enmendada) | pdfium/hidden.py: SCAN_SHARE = 0.5. Solo una imagen que cubre al menos media página protege el texto invisible. |
| ✅ Resuelto | 8. No cambiar lo que la persona escribió: notas cortas, código al unir, CSV con comillas | Lo comprobé con casos más difíciles que sus pruebas: «Sí», «Año», «¿Qué?» y una sola «é» salen bien. «[^0-9]» queda intacto al unir. Un CSV de 400 filas con «24" pulgadas» da 4 partes de 101 líneas. Aparte queda el cambio de codificación de las partes (B1-02). |
| ◐ Parcial | 9. PDF: listas numeradas y membrete fuera de las frases (ADR-0030 enmendada) | La regla de las cartas de 2 o 3 páginas existe (running.py). Pero en mi carta sintética de 2 páginas, con el pie dibujado después del encabezado, «Page 1 of 2» queda encima del cuerpo y el resumen dice que lo quitó (C-1). Las listas «a)» con minúscula se siguen fundiendo (B3-01). |
| ◐ Parcial | 10. Que cifras, colores y consejos nunca se contradigan | «Conservado» ya no sale en naranja (INFORMING), y el consejo para archivos de más de 250 MB ya no manda a Dividir. Quedan tres cosas: el estado del lote anterior en otras páginas (header.py:26-27), el consejo «divide» dentro de Dividir (en.toml, timed_out y out_of_memory) y el «todo bien» con avisos (F5-01). |
| ◐ Parcial | 11. Que el foco del teclado se vea en Qt y flet | Los botones de Qt y flet ya tienen anillos de 2 px (stylesheet.py). Quedan una parada de tabulador invisible en el panel de desplazamiento de Qt (F2-04) y las flechas que dejan de funcionar en flet después de usar el tabulador (F2-08). |
| ◐ Parcial | Decisión del dueño: un resultado sin texto «falló», con su razón y código 1 | Igual que la mejora 1: se cumple en el PDF, pero no en PowerPoint, Excel, Unir ni en «solo Markdown» al dividir. |
| ✅ Resuelto | Decisión del dueño: ADR-0054 enmendada (solo una imagen de media página protege) | Aplicada en hidden.py:24. |
| ◐ Parcial | Decisión del dueño: ADR-0030 enmendada (membrete en PDF de 2 o 3 páginas) | Se aplica cuando el pie se dibuja primero. Falla cuando se dibuja después del encabezado, y aun así el aviso afirma que lo quitó (C-1, reproducido). |
| ✅ Resuelto | Junta de dudas 2, D1: escape legible dentro de la puerta única | Lo comprobé en una página web: «AT&T», «juan_perez», «\[12\]». El hueco de los enlaces con corchetes es otro defecto de esa misma puerta, no del escape. |
| ✅ Resuelto | Junta de dudas 2, D2: respetar «Página completa» y avisarlo cada vez | child.py:115 y es.toml:309 (note.html_full_page). El aviso llega al resumen y a la terminal. En la ventana no se ve por F5-01; cuando se arregle, sí se verá, porque no está clasificado como buena noticia. |
| ⏳ Pendiente | Junta de dudas 2, D3: línea «Parte N de M» en las partes de un PDF | Se aplazó como decidió la junta, porque los membretes repetidos en las partes no se arreglaron en este ciclo. Es lo previsto. |

## 3. Lo que hay que proteger

Las fortalezas que ninguna mejora debe romper:

- Todo ocurre en el computador de la persona: en el instalador de Windows no se descarga nada.
- Las escrituras son seguras y atómicas, no siguen enlaces y nunca dejan archivos a medio escribir.
- Convertir rechaza los archivos trampa con un mensaje claro («no se abrió, por seguridad»). Es el modelo para las otras herramientas.
- El trabajador nuevo y aislado en cada tarea, con límites de tiempo por avance real, de memoria y de tamaño.
- La regla que separa los avisos que solo informan de los que piden revisar ya existe en el núcleo. Hay que usarla, no inventar otra.
- La puerta única de salida con marcas legibles («AT&T», «juan_perez», «\[12\]»), probada con un lector de Markdown real.
- Las notas cortas de Windows, el orden natural al unir y el código que la persona escribió se conservan, probados con el caso más corto.
- Dividir conserva las partes buenas, falla si falta una y solo barre los temporales viejos.
- Un solo presentador para tres ventanas: un arreglo llega a las tres a la vez.
- Cada fallo trae su motivo y qué hacer, en dos idiomas y con tono amable.
- Tablas de PDF, ecuaciones como LaTeX y el modo artículo para páginas web.
- La costumbre de decidir por escrito (ADR), de convocar juntas de dudas y de aprender de cada auditoría.

## 4. Las once mejoras recomendadas

Ordenadas por valor para el cliente final frente al esfuerzo. Marca tu decisión en la última columna.

| # | Mejora | Por qué le importa a la persona | Esfuerzo | ¿Me acojo? |
| --- | --- | --- | --- | --- |
| 1 | **Que Resultados no diga «todo bien» cuando un documento tiene un aviso que pide revisarlo** | Hoy la persona ve «Terminado», la carpeta se abre sola y cree que todo salió bien, aunque falten páginas. La app ya sabe qué avisos piden revisar: solo tiene que mostrarlos («Convertido, pero: 3 páginas sin texto»). | pequeño | ☐ Sí ☐ No |
| 2 | **Un resultado sin texto es «fallido» en todas las herramientas y formatos** | La 2.13 lo prometió. Pero una diapositiva vacía, un Excel vacío o un .md vacío al unir siguen saliendo como logrados, y la persona entrega a la IA un archivo vacío. | pequeño | ☐ Sí ☐ No |
| 3 | **Una sola revisión previa de seguridad para Convertir, Dividir y Unir** | Un Excel trampa que Convertir rechaza puede trabar el computador si se usa Dividir. Lo mismo pasa con la contraseña y con el cálculo de memoria. | pequeño | ☐ Sí ☐ No |
| 4 | **Las partes de un CSV salen igual que el original, con sus acentos** | Si al abrir una parte en Excel se lee «JosÃ©», la persona cree que ClearMD le dañó los datos. ADR-0047 promete que nada cambia por dentro. | pequeño | ☐ Sí ☐ No |
| 5 | **En los PDF, el aviso cuenta lo que de verdad se quitó, también en cartas de 2 páginas** | Lo subo del puesto 7 de C2 por dos razones. Comprobé que la regla de las cartas cortas, que tú enmendaste, falla cuando el pie se dibuja después del encabezado, y aun así el resumen dice que lo quitó. Además, ese aviso está clasificado como buena noticia, así que nunca llegaría a la pantalla. Que diga qué quitó, y que ordene las líneas por su altura en la página. | medio | ☐ Sí ☐ No |
| 6 | **No dar el consejo «ábrelo y guárdalo de nuevo» cuando el problema es otro** | Con una hoja oculta, Dividir falla y aconseja guardar de nuevo. La persona lo hace varias veces sin resultado. Dividir debe aceptar las hojas ocultas, y cada causa debe tener su propio consejo. | pequeño | ☐ Sí ☐ No |
| 7 | **Avisar en Revisar qué PDF puede tardar demasiado y detenerse** | La pantalla dice «Listo», la persona espera diez minutos y ve «Detenido». La terminal ya avisa; la ventana debe avisar también. | pequeño | ☐ Sí ☐ No |
| 8 | **Que los párrafos, bibliografías y listas «a)» de un PDF no se fundan en un bloque** | Lo rescato porque C2 lo dejó fuera sin decirlo. Es el daño más común a lo que recibe la IA en libros, contratos y trabajos académicos. | medio | ☐ Sí ☐ No |
| 9 | **Que cada mensaje diga lo que pasó: Dividir, la terminal y el README** | «Dividido» con una sola parte, «Nada que convertir» con código de éxito y un README que dice «página completa por defecto» le quitan confianza a todo lo demás. | pequeño | ☐ Sí ☐ No |
| 10 | **Guardar desde ahora solo los ajustes que la persona eligió, sin migrar lo ya guardado** | El atajo de Dividir puede cambiar para siempre las opciones de Dividir. Guardar solo lo elegido lo evita. No se cambia el «Página completa» ya guardado: ADR-0025 y la junta de dudas 2 lo decidieron, y el resumen ya lo avisa. | medio | ☐ Sí ☐ No |
| 11 | **Probar la App Moderna con un lector de pantalla antes de recomendarla** | Quien usa NVDA o Narrador la elige por consejo del instalador y no oye en qué paso está ni cuándo terminó. Hay que corregir lo básico y probarlo una vez. | medio | ☐ Sí ☐ No |

Los códigos de cada mejora (por ejemplo, B1-01) llevan a los hallazgos de la sección 8:

- **1.** F5-01, F1-08
- **2.** B5-01, B1-05, B1-06
- **3.** B2-02, B1-09, B1-08
- **4.** B1-02
- **5.** C-1, B3-02, C-2, B3-03, B3-04
- **6.** B5-11, B1-01
- **7.** F5-03
- **8.** B3-01
- **9.** B5-03, B5-02, B5-04, F4-10
- **10.** F4-01, F1-01, F1-02
- **11.** F2-01, F2-02

## 5. Lo que no conviene hacer

Propuestas que surgieron en las juntas y que, según la conciliadora, **añadirían complejidad o romperían algo**:

- No cambiar una vez el ajuste «Página completa» guardado (ADR-0025 enmendada, línea 95; junta de dudas 2, D2), salvo que el dueño enmiende antes la ADR. El aviso en el resumen ya cumple.
- No ignorar en silencio desktop.ini, Thumbs.db ni .DS_Store: UX §3 pide que toda omisión diga su motivo. Basta con plegarlos.
- No sacar Imágenes ni Resumen del paso 1 (ADR-0031, ADR-0033, spec 009 AC-10). Plegarlos dentro del paso 1, sí.
- No añadir la línea «Parte N de M» a las partes de un Markdown o un texto (ADR-0045, D3). En las de PDF, solo después de arreglar los membretes.
- No cambiar el resumen por defecto a «Markdown + PDF» sin enmendar ADR-0031.
- No quitar las hojas ocultas de las partes .xlsx de Dividir (ADR-0047), aunque se decida dejarlas fuera del Markdown.
- No dejar que el trabajador escriba fuera de su tubería sin las garantías de escritura segura (lstat, no seguir enlaces).
- No mantener vivo el trabajador entre tareas para ganar arranque (decisión del dueño). Basta con cargar cada conversor la primera vez que se usa.
- No arreglar las listas de PowerPoint ni reemplazar markitdown en 2.x (planeado para 3.0.0).
- No añadir un ajuste de tamaño de texto sin enmendar ADR-0012.
- No subir F3-01 a alta ni cambiar código de alta resolución sin una captura en Windows.
- No resolver los problemas de claridad agregando controles o texto al paso 1: corregir lo que la app dice.
- Mantener las tres ventanas y la App Clásica como edición por defecto. El aviso para lectores de pantalla no la cambia.
- No confirmar Cancelar; solo pregunta cerrar durante una tarea.
- No renombrar OutputMD, OutputSep ni OutputUnif sin una migración.

## 6. Desacuerdos que quedan abiertos

- Cambiar una vez el «Página completa» guardado antes de la 2.12 (F4-01, C1, C2): ZANJADO en contra. ADR-0025 enmendada dice «no migration» (línea 95). La junta de dudas 2 ya lo deliberó (D2) y aplicó la alternativa: el resumen lo avisa cada vez. Nadie aportó un hecho nuevo. Se mantiene solo la parte que mira hacia adelante: guardar desde ahora solo lo que la persona elige.
- Ignorar en silencio desktop.ini y archivos parecidos (F5-02) frente a mostrarlos plegados (B5, F1): ZANJADO a favor de plegarlos, porque UX §3 pide que toda omisión diga su motivo.
- Plegar las opciones del paso 1 (F3-04, F4-09) frente a añadir una línea de ayuda a cada una (F5-06): ZANJADO, se pliegan dentro del paso 1, en palabras. Es lo mismo que decidió la cuarta auditoría. Sacarlas del paso 1 sigue sin hacerse (ADR-0031/0033, spec 009 AC-10).
- Resumen «Markdown + PDF» por defecto en las ventanas (F4-07): ABIERTO, lo decide el dueño, porque exige enmendar ADR-0031. Recomiendo primero la línea «cómo abrir un .md».
- Lo oculto en otros formatos (B2-01): ABIERTO, lo decide el dueño (extender ADR-0054). Recomiendo la distinción de B3: lo escondido para engañar queda fuera, y lo que el autor usa como apoyo va marcado. Siempre con aviso, y sin tocar las partes .xlsx (ADR-0047).
- Capítulos LaTeX que salen dos veces (B3-07): ABIERTO, exige enmendar ADR-0022:27. Recomiendo enmendarla.
- Línea de contexto en las partes (B3-05): ZANJADO por la junta de dudas 2 (D3). Va solo en las partes de un PDF y después de arreglar los membretes. Lo que sí se hace ya: mantener cada título con su bloque.
- Unir PDF grandes, aviso en el plan o el trabajador escribe directo en la carpeta (B1-03, B4): ZANJADO, primero el aviso en el plan. Escribir directo exige las garantías de escritura segura.
- Severidad de F3-01 (alta para F3, media para F2 y C1): ZANJADO en media hasta tener una captura en Windows al 150 %. Si se confirma, sube.
- Valor de B2-03, enlaces con corchetes (medio para C1, bajo para C2): ZANJADO en severidad media. Se arregla después de los puntos que hacen que la app diga la verdad, y dentro de la misma puerta de salida.
- Archivo ligero para Linux (B4-01): ABIERTO, de baja prioridad. Exige enmendar ADR-0038, y C1 no lo citó.

## 7. Cómo trabajaron las juntas

La conciliadora también auditó a las juntas y a su debate:

### Junta Backend (B1-B5) — rigor 8,5/10

- **Lo que hizo bien:** Reprodujo casi todo con gemelos sintéticos y comandos concretos. Encontró el patrón de fondo de esta versión: cada protección nació en Convertir y no llegó a Dividir ni a Unir (bomba ZIP, contraseña, memoria, resultado vacío). Citó las ADR en cada hallazgo y respetó las decisiones del dueño (sin PDFium, el trabajador no queda vivo, markitdown solo en 3.0.0).
- **Lo que no vio:** Probó el pie de página dibujado después del encabezado solo en un PDF de 6 páginas, y no en la carta de 2 o 3 páginas que el dueño acababa de enmendar (ADR-0030). Ahí también falla (C-1). Tampoco vio que la nota «se quitaron encabezados y pies» está clasificada como buena noticia (schemas/notes.py:60-62): aunque se arregle la pantalla de Resultados, nunca llegaría a la ventana, y esa nota puede ser falsa (C-2).
- **Donde se excedió:** B2-01 se presenta con severidad alta como si fuera un fallo del código, pero es una ampliación de una decisión del dueño (ADR-0054). B3-07 pide enmendar ADR-0022 y lo dice bien, aunque lo mezcla con el número de las ecuaciones. B1-03 propone que el trabajador escriba fuera de su tubería; B2 tuvo que recordar las garantías de escritura segura.

### Junta Frontend (F1-F5) — rigor 8/10

- **Lo que hizo bien:** Encontró el hallazgo más importante de la auditoría (F5-01: Resultados ignora los avisos), lo comprobó en el código y mostró que el arreglo es pequeño, porque la regla ya existe (models.py:153). Lo apoyó en capturas reales y fue honesta cuando no pudo probar en Windows (F3-01, F3-02).
- **Lo que no vio:** F4-01 volvió a pedir que se cambie una vez el ajuste «Página completa», pero ADR-0025 ya dice «no migration» (línea 95), y la junta debía leer las ADR antes de recomendar. Nadie revisó que el aviso nuevo de «página completa» (D2) solo llega al resumen escrito, y no a la ventana, por culpa de F5-01.
- **Donde se excedió:** F3-01 se marcó como alta sin medirlo en Windows. F1-08 repite F5-01. F4-07 pide cambiar el valor por defecto de ADR-0031 con evidencia que nadie probó (la asociación del .md en Windows). F5-02 propone ignorar archivos en silencio, y eso choca con UX §3.

### Debate (ronda 2) — rigor 8/10

- **Lo que hizo bien:** Las intervenciones volvieron al código («reverified») antes de apoyar algo. Unieron bien los duplicados (B5-09 con B5-08, F4-09 con F3-04, F5-05 con F3-05). Ninguna severidad subió sin una nueva comprobación. Las advertencias cruzadas fueron útiles: no agregar texto al paso 1, y las partes .xlsx no cambian por dentro (ADR-0047).
- **Lo que no vio:** Nadie preguntó si la migración de F4-01 ya estaba decidida. B3-05 propuso otra vez la línea de contexto en las partes, que la junta de dudas 2 ya había limitado a los PDF (D3).
- **Donde se excedió:** Algunas fusiones metieron problemas distintos en un mismo hallazgo (B5-11 junta un consejo genérico con consejos que no siguen la herramienta), y eso hace más difícil aceptarlos por partes.

### Conciliador 1 (verificación) — rigor 8,5/10

- **Lo que hizo bien:** Reprodujo él mismo los hallazgos clave: el resultado vacío, la bomba ZIP al dividir, el CSV, la hoja oculta, la salida de la línea de comandos, el pie de página y los enlaces con corchetes. Dijo con franqueza qué solo leyó en el código. Su comprobación de lo retirado entre rondas fue correcta, y rescató el comentario HTML de PowerPoint.
- **Lo que no vio:** Repitió la migración de F4-01 como «decisión del dueño», sin decir que la junta de dudas 2 ya la había descartado y que esa decisión ya está aplicada (child.py:115, es.toml:309). No probó la carta corta de 2 páginas (C-1).
- **Donde se excedió:** En los últimos grupos juntó muchos hallazgos distintos. El grupo de seguridad de bajo riesgo, por ejemplo, mezcla seis temas, y así se pierde el detalle para decidir.

### Conciliador 2 (valor) — rigor 7,5/10

- **Lo que hizo bien:** Ordenó bien, poniendo primero que la app diga la verdad, y casi todo es de esfuerzo pequeño. Rechazó agregar controles nuevos. Explicó por qué dejó fuera F3-01 y B2-01.
- **Lo que no vio:** Dejó fuera de su lista, sin mencionarlo, B3-01 (párrafos, bibliografías y listas que se funden en un solo bloque), que C1 había confirmado con severidad alta y que daña lo que recibe la IA. En el puesto 8 juntó F1-02 (la lista que se reemplaza), que no es un problema de ajustes guardados.
- **Donde se excedió:** En el puesto 8 dejó viva la migración del ajuste «Página completa», que contradice ADR-0025 enmendada y la decisión D2.

## 8. Hallazgos verificados

Son 27 hallazgos, ordenados por gravedad. **Veredicto:** ✅ confirmada · ◐ parcialmente cierta · ✖ refutada.

| Gravedad | Valor para el usuario | Esfuerzo | Veredicto | Hallazgo |
| --- | --- | --- | --- | --- |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [1. La pantalla de Resultados dice «todo bien» aunque un documento tenga avisos que piden revisarlo](#h1) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [2. Un resultado vacío todavía cuenta como «convertido», «unido» o «dividido»](#h2) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [3. Dividir un Excel se salta las revisiones previas de Convertir: archivo trampa, contraseña y memoria](#h3) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [4. Las partes de un CSV cambian su codificación y Excel muestra los acentos rotos](#h4) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [5. Una carta de dos páginas conserva «Página 1 de 2» encima de cada página, y el resumen dice que lo quitó](#h5) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [6. Problemas conocidos reciben el consejo falso «ábrelo y guárdalo de nuevo», y otros consejos no siguen la herramienta](#h6) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [7. Revisar no avisa qué PDF puede detenerse por tardar demasiado](#h7) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [8. En los PDF, los párrafos con sangría, las bibliografías y las listas «a)» se funden en un solo bloque](#h8) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [9. Una fracción corta sin número cambia de significado sin aviso (1/2 sale como «1 2»)](#h9) |
| 🔴 Alta | medio | medio | ◐ Parcial | [10. Guardar un ajuste fija valores que la persona nunca eligió, y el atajo de Dividir cambia sus opciones](#h10) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [11. La App Moderna, la recomendada para lectores de pantalla, no dice dónde está ni cuándo terminó, y la Clásica no avisa de ella](#h11) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [12. Lo oculto en Word, Excel, PowerPoint y páginas web pasa entero al Markdown, sin aviso](#h12) |
| 🟠 Media | alto | pequeño | ✅ Confirmada | [13. El aviso «se quitaron encabezados y pies» está clasificado como buena noticia, aunque puede ser falso o esconder títulos perdidos](#h13) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [14. Mensajes que no dicen lo que pasó: «dividido» con una sola parte, «Nada que convertir» con código 0, un README desactualizado](#h14) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [15. La línea sobre el título muestra el estado del lote anterior en otras páginas](#h15) |
| 🟠 Media | alto | pequeño | ◐ Parcial | [16. Con la escala de Windows al 150 % o más, el botón principal puede quedar oculto y la App Clásica verse borrosa](#h16) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [17. Archivos que no piden nada quitan el mensaje de éxito y reciben el consejo «Hazlo visible»](#h17) |
| 🟠 Media | medio | medio | ✅ Confirmada | [18. El filtro de enlaces peligrosos falla si el texto del enlace lleva corchetes](#h18) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [19. Contrastes bajos y teclado desigual entre las tres ventanas](#h19) |
| 🟠 Media | alto | pequeño | ✅ Confirmada | [20. La página de descarga es larga y mezcla idiomas, y no explica el bloqueo del navegador](#h20) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [21. La ayuda de la terminal está a medio traducir, dice que Dividir es solo para PDF y muestra el nombre equivocado](#h21) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [22. Resultados no nombra el resumen ni dice cómo abrir un .md; la app no dice que es para la IA ni cómo actualizarla](#h22) |
| 🟠 Media | medio | medio | ✅ Confirmada | [23. Paso 1 cargado de opciones sin explicar, y rutas cortadas por el lado equivocado](#h23) |
| 🟠 Media | medio | medio | ✅ Confirmada | [24. Unir PDF grandes, partes abiertas en otro programa y nombres «(pdf)» que cambian](#h24) |
| 🟠 Media | medio | medio | ✅ Confirmada | [25. Los PDF densos avanzan lento y la barra se queda quieta al principio](#h25) |
| 🟠 Media | medio | medio | ✅ Confirmada | [26. Fidelidad para la IA: títulos sueltos al dividir, subtítulos de Word, capítulos LaTeX duplicados, números de Excel](#h26) |
| ⚪ Baja | bajo | pequeño | ✅ Confirmada | [27. Mejoras menores: empaquetado, políticas, CI, íconos pequeños, textos y gestos sin respuesta](#h27) |

<a id="h1"></a>

### 8.1 La pantalla de Resultados dice «todo bien» aunque un documento tenga avisos que piden revisarlo

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · F5-01, F1-08*

- **Lo que siente la persona:** La app me dijo que todo se convirtió y me abrió la carpeta. Después la IA me respondió sin la mitad del documento.
- **Recomendación:** Usar en la pantalla la regla que ya existe y que separa los avisos que solo informan de los que piden revisar. Esos documentos aparecen como «Convertido, pero: …», en tono de aviso. El estado pasa a «Terminado con problemas» y la carpeta no se abre sola. Hay que probarlo con un PDF de 2 páginas donde una es una imagen.
- **Comprobación de la conciliadora:** Lo leí en el código: presenter/screens/results.py se salta todo lo convertido con 'continue', y el presentador nunca consulta outcome.notes. Además, por esta misma causa, el aviso de «página completa» que decidió la junta de dudas 2 (D2) llega al resumen, pero no a la ventana.

<a id="h2"></a>

### 8.2 Un resultado vacío todavía cuenta como «convertido», «unido» o «dividido»

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B5-01, B1-05, B1-06*

- **Lo que siente la persona:** Me dijo que mi presentación se convirtió, pero el archivo no tiene nada.
- **Recomendación:** Crear una sola regla de «sin texto» para Convertir, Dividir y Unir. Antes de medir, quita lo que agrega el propio programa (el número de diapositiva, el nombre de la hoja, los comentarios). Hay que probarla con una diapositiva vacía, un Excel vacío, un .md de solo espacios y un PDF escaneado al dividir pidiendo «solo Markdown».
- **Comprobación de la conciliadora:** C1 lo reprodujo. La causa está en child.py: 'not markdown.strip()' mide un texto que ya trae marcas del programa. Esto rompe la decisión del dueño (un resultado sin texto falla, con código 1) y las notas de la 2.13.

<a id="h3"></a>

### 8.3 Dividir un Excel se salta las revisiones previas de Convertir: archivo trampa, contraseña y memoria

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B2-02, B1-09, B1-08*

- **Lo que siente la persona:** Con Convertir no me dejó abrir ese Excel por seguridad. Con Dividir lo aceptó, y el computador se quedó trabado varios minutos.
- **Recomendación:** Una sola puerta de revisiones previas por formato (archivo trampa, contraseña, vacío y memoria medida sobre el tamaño ya descomprimido), por la que pasen las tres herramientas antes de separarse. Una prueba por herramienta con el archivo trampa.
- **Comprobación de la conciliadora:** C1 lo reprodujo con la simulación de Dividir. En planning.py:134-144, la rama de Dividir termina en 'continue' antes de la revisión ZIP. El factor de memoria lo midió un solo auditor.

<a id="h4"></a>

### 8.4 Las partes de un CSV cambian su codificación y Excel muestra los acentos rotos

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B1-02*

- **Lo que siente la persona:** Dividí mi lista de clientes y salen nombres como «JosÃ©». Parece que ClearMD me dañó los datos.
- **Recomendación:** Escribir cada parte con la misma codificación, la misma marca inicial (BOM) y los mismos saltos de línea que el original, como promete ADR-0047. Probarlo con cp1252, saltos CRLF y un campo que tenga un salto de línea.
- **Comprobación de la conciliadora:** C1 lo reprodujo con od -c. Yo comprobé que el reparto en filas ya es correcto (4 partes de 101 líneas con una comilla de pulgadas). Lo que falla es solo la codificación.

<a id="h5"></a>

### 8.5 Una carta de dos páginas conserva «Página 1 de 2» encima de cada página, y el resumen dice que lo quitó

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · C-1, B3-02*

- **Lo que siente la persona:** El resumen dice que se quitaron los números de página, pero mi carta los tiene arriba de cada página.
- **Recomendación:** Ordenar las líneas de cada página por su altura antes de buscar encabezados y pies. Así se cumple la enmienda de ADR-0030 sin importar en qué orden el programa dibujó el PDF. La nota debe listar los textos quitados. La prueba debe usar el orden encabezado, luego pie, luego cuerpo, en 2 páginas y en 6.
- **Comprobación de la conciliadora:** Lo reproduje yo (C-1). Hice un PDF sintético de 2 páginas con tests/support/pdf_builder.py: membrete arriba, «Page N of 2» abajo y el cuerpo, en ese orden de dibujo. El membrete se quita, pero «Page 1 of 2» queda encima del cuerpo, y el resumen dice 'headers, footers and page numbers … were left out'. Si se dibuja primero el pie, sale bien. B3-02 lo vio solo en 6 páginas.

<a id="h6"></a>

### 8.6 Problemas conocidos reciben el consejo falso «ábrelo y guárdalo de nuevo», y otros consejos no siguen la herramienta

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B5-11, B1-01*

- **Lo que siente la persona:** Volví a guardar el Excel tres veces como me dijo y siguió fallando.
- **Recomendación:** Dividir reparte solo las hojas visibles y conserva las ocultas en cada parte (ADR-0047). Cada causa conocida (hoja oculta, contraseña, tamaño total al unir) tiene su propio texto. Dentro de Dividir no se aconseja «divídelo». Una prueba falla si un caso conocido recibe el mensaje genérico.
- **Comprobación de la conciliadora:** C1 reprodujo la hoja oculta. Comprobé en en.toml que error.timed_out.action y error.out_of_memory.action aconsejan dividir sin mirar la herramienta activa.

<a id="h7"></a>

### 8.7 Revisar no avisa qué PDF puede detenerse por tardar demasiado

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · F5-03*

- **Lo que siente la persona:** Decía «Listo para convertir». Esperé diez minutos y al final salió «Detenido».
- **Recomendación:** Marcar con un aviso la fila de ese archivo («puede tardar más de X y detenerse; te conviene dividirlo») y nombrarlo en el botón cuando es uno solo. La terminal ya da este aviso.
- **Comprobación de la conciliadora:** screens/review.py nunca lee plan.warnings (C1 y F1 lo comprobaron con grep).

<a id="h8"></a>

### 8.8 En los PDF, los párrafos con sangría, las bibliografías y las listas «a)» se funden en un solo bloque

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B3-01*

- **Lo que siente la persona:** La IA no distingue una referencia de otra: le llegó toda la bibliografía como un solo párrafo.
- **Recomendación:** Tomar como señal de párrafo nuevo la sangría de primera línea, la sangría francesa y una línea corta que termina en punto. Aceptar listas «a)» e «i.». Probarlo con el gemelo sintético de una bibliografía.
- **Comprobación de la conciliadora:** No lo reproduje. La evidencia es concreta y usa PDF sintéticos. C2 lo dejó fuera de su lista sin decirlo, y yo lo rescato.

<a id="h9"></a>

### 8.9 Una fracción corta sin número cambia de significado sin aviso (1/2 sale como «1 2»)

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B3-04*

- **Lo que siente la persona:** La IA leyó «p = 12» donde mi apunte decía un medio.
- **Recomendación:** Reconocer las rayas de fracción cortas y varias en la misma línea. Si queda una raya con texto arriba y abajo sin reconstruir, avisar «ecuación para revisar» con su página.
- **Comprobación de la conciliadora:** No lo reproduje. La prueba que existe (test_015) usa el caso fácil, una raya de 30 pt. Es la lección XIII.1.

<a id="h10"></a>

### 8.10 Guardar un ajuste fija valores que la persona nunca eligió, y el atajo de Dividir cambia sus opciones

*🔴 Alta · valor medio · esfuerzo medio · ◐ Parcial · F4-01, F1-01, F1-02*

- **Lo que siente la persona:** Antes Dividir me guardaba las partes en PDF. Un día dejó de hacerlo, y yo nunca toqué esa opción.
- **Recomendación:** A partir de ahora, guardar solo lo que la persona eligió, y mantener las opciones «solo para esta tarea» en una capa que nunca se escribe en disco. Al volver a Convertir, sumar la lista en vez de reemplazarla. NO cambiar el «Página completa» ya guardado: ADR-0025 (línea 95) y la junta de dudas 2 (D2) lo descartaron, y el aviso en el resumen ya está aplicado.
- **Comprobación de la conciliadora:** serialize_settings escribe todos los campos, y tools.py escribe los valores temporales en s.settings. Esto se confirma. La migración que piden F4-01, C1 y C2 la rechazo, porque contradice una decisión ya tomada y no trae evidencia nueva.

<a id="h11"></a>

### 8.11 La App Moderna, la recomendada para lectores de pantalla, no dice dónde está ni cuándo terminó, y la Clásica no avisa de ella

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · F2-01, F2-02*

- **Lo que siente la persona:** Uso un lector de pantalla. Al cambiar de paso no oigo nada, y nunca me entero de que la conversión terminó.
- **Recomendación:** Poner el foco en algo con nombre al cambiar de página. Anunciar el final con el mismo titular corregido de F5-01. Sacar los nombres del catálogo de textos. En la App Clásica, si Windows dice que hay un lector activo, mostrar una vez un cuadro nativo. Probarlo con NVDA o Narrador antes de llamarla «la que mejor funciona».
- **Comprobación de la conciliadora:** Me baso en la evidencia de código: el nombre literal «inputs» y ningún anuncio accesible. Esto respeta ADR-0017 (no se detecta el idioma) y mantiene la edición por defecto.

<a id="h12"></a>

### 8.12 Lo oculto en Word, Excel, PowerPoint y páginas web pasa entero al Markdown, sin aviso

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B2-01*

- **Lo que siente la persona:** Le pasé mi presupuesto a la IA y me citó la hoja de salarios que yo tenía escondida.
- **Recomendación:** Que el dueño decida extender el principio de ADR-0054. Lo escondido para que no se vea queda fuera, con aviso. Lo que el autor usa como apoyo (notas del orador, filas ocultas) va marcado, con aviso. Las partes .xlsx de Dividir no se tocan (ADR-0047).
- **Comprobación de la conciliadora:** Es una ampliación de una decisión del dueño, no un fallo del código. ADR-0054 se limita al PDF.

<a id="h13"></a>

### 8.13 El aviso «se quitaron encabezados y pies» está clasificado como buena noticia, aunque puede ser falso o esconder títulos perdidos

*🟠 Media · valor alto · esfuerzo pequeño · ✅ Confirmada · C-2, B3-03*

- **Lo que siente la persona:** En mi examen desaparecieron las preguntas, y el resumen lo contó como algo bueno, en la parte tranquila.
- **Recomendación:** Que la nota diga qué textos quitó. Si quitó líneas en negrita del tamaño del texto, o líneas con un número que avanza con la página, la nota pasa a «conviene revisar» y llega a la pantalla cuando se arregle F5-01. No quitar una línea en negrita del tamaño del cuerpo (B3-03).
- **Comprobación de la conciliadora:** Lo leí en el código (C-2): schemas/notes.py pone PDF_RUNNING_REMOVED en INFORMATION, es decir, «buenas noticias, nunca 'necesita atención'». Con el arreglo de F5-01 tal como está propuesto, esta nota tampoco llegaría a la ventana.

<a id="h14"></a>

### 8.14 Mensajes que no dicen lo que pasó: «dividido» con una sola parte, «Nada que convertir» con código 0, un README desactualizado

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B5-03, B5-02, B5-04, F4-10*

- **Lo que siente la persona:** El README dice una cosa y el programa hace otra. ¿En cuál confío?
- **Recomendación:** Dar un titular honesto cuando queda una sola parte. Cada «nada que hacer» dice el motivo, usa el verbo de la herramienta y termina con código 2. Corregir en el README el valor por defecto de --html, quitar «en construcción» y verificar la tabla de opciones contra el código.
- **Comprobación de la conciliadora:** C1 reprodujo la carpeta vacía con exit=0. README.md:222 dice 'the whole page (default)', y en settings.py es 'article'.

<a id="h15"></a>

### 8.15 La línea sobre el título muestra el estado del lote anterior en otras páginas

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F3-03, F1-09*

- **Lo que siente la persona:** Estoy eligiendo archivos nuevos y arriba dice en naranja «Terminado con problemas».
- **Recomendación:** Mostrar el estado solo en su página. En las demás, solo «Paso n de 4».
- **Comprobación de la conciliadora:** Lo releí: chrome/header.py:26-27 agrega el estado siempre que no sea READY.

<a id="h16"></a>

### 8.16 Con la escala de Windows al 150 % o más, el botón principal puede quedar oculto y la App Clásica verse borrosa

*🟠 Media · valor alto · esfuerzo pequeño · ◐ Parcial · F3-01, F2-07, F3-02*

- **Lo que siente la persona:** No encuentro el botón para seguir, y las letras se ven borrosas.
- **Recomendación:** Primero, una captura en el CI de Windows al 150 %. Después, ajustar la ventana al área libre de la pantalla, dejar la barra de botones siempre visible y declarar el soporte de alta resolución en Tk.
- **Comprobación de la conciliadora:** La cuenta es correcta, pero nadie lo probó en Windows. Si la captura lo confirma, sube a alta.

<a id="h17"></a>

### 8.17 Archivos que no piden nada quitan el mensaje de éxito y reciben el consejo «Hazlo visible»

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F5-02*

- **Lo que siente la persona:** Me dice que algo necesita mi atención y me aconseja mostrar un archivo del sistema que no conozco.
- **Recomendación:** Si todo lo pendiente solo informa, mostrar la tarjeta de éxito con una línea plegable debajo. No ignorar en silencio (UX §3). Cambiar el consejo de los archivos de sistema.
- **Comprobación de la conciliadora:** Los colores ya están corregidos (review.py: INFORMING, neutro). Falta la tarjeta de éxito y es.toml:95.

<a id="h18"></a>

### 8.18 El filtro de enlaces peligrosos falla si el texto del enlace lleva corchetes

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · B2-03*

- **Lo que siente la persona:** Hice clic en un enlace del documento convertido y se abrió algo raro en mi equipo.
- **Recomendación:** Neutralizar cualquier destino file:, javascript: o \\servidor sin importar el texto del enlace, dentro de la misma puerta de salida, probado con markdown-it-py.
- **Comprobación de la conciliadora:** Lo reproduje: safe_output('[a [b] c](javascript:alert(1))') y una imagen dentro de un enlace a file: devuelven 0 cambios, mientras que '[x](file:///…)' sí se limpia.

<a id="h19"></a>

### 8.19 Contrastes bajos y teclado desigual entre las tres ventanas

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F2-03, F2-05, F2-06, F2-04, F2-08, F1-07, F2-09*

- **Lo que siente la persona:** Con la vista cansada no veo en qué fila estoy, y Ctrl+0 funciona en una ventana y en otra no.
- **Recomendación:** En la App Clásica, una barra de acento de 2 px para la fila con foco. Texto informativo en el gris normal. Un borde de campo con contraste de al menos 3:1. Una tabla única de atajos en el presentador. Sacar del tabulador la parada invisible de Qt.
- **Comprobación de la conciliadora:** Los cálculos de contraste son coherentes con la paleta, y pyside/window/inputs.py:33 empieza en 1.

<a id="h20"></a>

### 8.20 La página de descarga es larga y mezcla idiomas, y no explica el bloqueo del navegador

*🟠 Media · valor alto · esfuerzo pequeño · ✅ Confirmada · F4-02, B5-07, F4-03*

- **Lo que siente la persona:** Quería descargar y me encontré un texto larguísimo sobre «la cuarta auditoría».
- **Recomendación:** Publicar una copia sin número de versión, enlazada directo. Arriba, qué descargar y dos pasos para los avisos del navegador y de Windows. Las novedades plegadas, un bloque por idioma y sin palabras internas.
- **Comprobación de la conciliadora:** RELEASE_NOTES.md nombra las auditorías. El bloqueo del navegador es un comportamiento conocido, pero no se probó aquí.

<a id="h21"></a>

### 8.21 La ayuda de la terminal está a medio traducir, dice que Dividir es solo para PDF y muestra el nombre equivocado

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B5-05, B1-10, F4-11, B5-06*

- **Lo que siente la persona:** Copié el comando de la ayuda y Windows me dijo que no existe.
- **Recomendación:** Traducir la ayuda completa. Decir qué formatos acepta cada forma de dividir. Mostrar el nombre del programa que de verdad se ejecuta. Poner la lista de formatos en la ayuda.
- **Comprobación de la conciliadora:** parser.py usa prog='clearmd', y el instalador enseña 'clearmd-cli'.

<a id="h22"></a>

### 8.22 Resultados no nombra el resumen ni dice cómo abrir un .md; la app no dice que es para la IA ni cómo actualizarla

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F5-04, F4-07, B5-10, F4-04, F4-06*

- **Lo que siente la persona:** Se me abrieron cuatro ventanas y no sé cuál es el resumen. Windows me pregunta con qué abrirlo.
- **Recomendación:** Nombrar el resumen en Resultados y explicar «clic derecho → Abrir con → Bloc de notas». Un botón con el número de carpetas. Una línea de «Actualizaciones» en la Ayuda, sin conectarse a internet. El propósito «para tu IA» en el subtítulo. El valor por defecto «Markdown + PDF» queda para el dueño (ADR-0031).
- **Comprobación de la conciliadora:** Ninguna clave de [gui.result] nombra Resumen_ClearMD.

<a id="h23"></a>

### 8.23 Paso 1 cargado de opciones sin explicar, y rutas cortadas por el lado equivocado

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · F3-04, F4-09, F5-06, F3-05*

- **Lo que siente la persona:** Antes de agregar mi primer archivo ya me piden decidir cosas que no entiendo, y todas las rutas dicen «C:\Users\…».
- **Recomendación:** Plegar Imágenes y Resumen dentro del paso 1, en una línea con palabras y un «Cambiar». No sacarlos del paso 1 (ADR-0031 y ADR-0033). Cortar las rutas por la izquierda, igual en las tres ventanas.
- **Comprobación de la conciliadora:** Se ve en las capturas 018 y 007 a 800 px.

<a id="h24"></a>

### 8.24 Unir PDF grandes, partes abiertas en otro programa y nombres «(pdf)» que cambian

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · B1-03, B1-04, B1-07*

- **Lo que siente la persona:** Mis tres escaneos están bien, pero la app dice que los tres están dañados.
- **Recomendación:** Sumar los tamaños al planificar la unión, con un motivo propio. Deshacer el movimiento de las partes si una falla. Reutilizar el nombre anterior del mismo original.
- **Comprobación de la conciliadora:** La evidencia es concreta pero no la reproduje. B1-04 es una causa nueva, distinta de la mejora 6 de la v4, que sí está resuelta.

<a id="h25"></a>

### 8.25 Los PDF densos avanzan lento y la barra se queda quieta al principio

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · B4-04, B4-03*

- **Lo que siente la persona:** La barra se queda en «página 0» y creo que la app se colgó.
- **Recomendación:** Contar la primera pasada en la barra. Cargar cada conversor la primera vez que se usa, sin dejar vivo el trabajador entre tareas (decisión del dueño).
- **Comprobación de la conciliadora:** Las mediciones son del auditor.

<a id="h26"></a>

### 8.26 Fidelidad para la IA: títulos sueltos al dividir, subtítulos de Word, capítulos LaTeX duplicados, números de Excel

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · B3-05, B3-06, B3-07, B3-08*

- **Lo que siente la persona:** La IA leyó «0.125» donde mi hoja dice «12,5 %».
- **Recomendación:** Mantener cada título con su bloque. No agregar la línea de contexto a partes de Markdown (ADR-0045, D3). Bajar el umbral de título. Aplicar el formato visible en Excel. Lo de LaTeX necesita enmendar ADR-0022:27.
- **Comprobación de la conciliadora:** HEADING_RATIO es 1.2. Lo demás viene de salidas concretas.

<a id="h27"></a>

### 8.27 Mejoras menores: empaquetado, políticas, CI, íconos pequeños, textos y gestos sin respuesta

*⚪ Baja · valor bajo · esfuerzo pequeño · ✅ Confirmada · B2-04, B2-05, B2-06, B2-07, B2-08, B5-08, B4-01, B4-05, B4-02, B4-06, B4-07, B4-08, B3-09, B3-10, F3-06, F2-10, F3-07, F3-08, F3-09, F3-10, F5-07, F5-08, F5-09, F4-05, F4-08, F1-03, F1-04, F1-05, F1-06*

- **Lo que siente la persona:** No entiendo qué es «ttk», y arrastré un archivo y no pasó nada.
- **Recomendación:** Atenderlas en lote cuando haya tiempo. Las listas de PowerPoint esperan a la 3.0.0. El archivo ligero para Linux necesita enmendar ADR-0038. La descarga de flet por pip se resuelve antes de publicar en PyPI.
- **Comprobación de la conciliadora:** Confirmé ICON = 16 en Qt y flet, y la licencia en clearmd.iss:53. Lo demás viene de C1.

## 9. Los informes de cada auditor (tras el debate)

### Backend · Lógica y robustez — 6,5/10

Mantengo el juicio de la ronda 1 y lo endurezco un poco. Convertir es sólido: escribe de forma segura, los nombres no chocan, cancela limpio y aísla el trabajador. Las herramientas nuevas (Dividir y Unir) y los casos difíciles de oficina siguen siendo el punto débil. El debate confirmó un patrón de fondo que en la ronda 1 vi solo en parte: el camino de Dividir se salta las revisiones previas que Convertir sí hace. Pasa con las bombas ZIP (B2-02, que verifiqué en planning.py), con la contraseña (B1-09) y con la estimación de memoria (B1-08). Además, la regla de 'resultado sin texto = con error' se queda corta en varios lugares: Unir (B1-05), 'conservar Markdown' de Dividir (B1-06) y, como mostró B5-01 y comprobé yo mismo, una presentación con una diapositiva vacía o un Excel vacío, que salen 'convertidos' con código 0. También comprobé que 'Nada que convertir' termina con código 0 (B5-02). Ninguno de estos problemas es catastrófico, pero rompen promesas escritas de los ADR y de las notas de la 2.13. La raíz común tiene arreglo barato: una sola puerta de revisiones previas y una sola función de 'resultado vacío' que usen las tres herramientas.

**Fortalezas que vio:**

- Escritura segura: atomic_write_bytes usa un temporal único creado en exclusiva más os.replace, revisa cada carpeta sin seguir enlaces ni junctions y nunca deja archivos a medio escribir (use_cases/output_files.py).
- Dividir prepara las partes aparte (PartStage) y solo borra el corte anterior cuando el nuevo está completo. Reconoce las partes anteriores en los dos idiomas y no toca los archivos propios del usuario.
- Reglas honestas en Convertir: 0 bytes es 'archivo vacío', y un PDF escaneado falla con su motivo y código 1 (worker/child.py:88-112). Un docx o un xlsx cifrado se reconoce como protegido con contraseña.
- El proceso trabajador está aislado y tiene límites reales: el tiempo se cuenta desde el último avance con un techo de 6x, la memoria se vigila, los procesos hijos se eliminan y la cancelación es inmediata (services/worker/processes.py).
- Los nombres no chocan sin distinguir mayúsculas ni forma Unicode, el orden es natural y estable, y los nombres largos se recortan sin cortar un carácter (use_cases/paths.py).
- El barrido de temporales solo borra lo que tiene más de 24 h, y al cerrar la ventana durante una tarea se cancela y se espera, en las tres ventanas.
- El decodificador de texto prueba primero cp1252 y no se deja engañar por un detector con textos cortos (tex/source.py _as_western).

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B1-01 | 🔴 Alta | pequeño | alta | Dividir un Excel con una hoja oculta falla el archivo entero, con un consejo equivocado |
| B1-02 | 🔴 Alta | pequeño | alta | Las partes de un CSV o de un texto cambian de codificación, y Excel muestra los acentos rotos |
| B1-03 | 🔴 Alta | medio | alta | Unir PDF sanos que juntos pasan de 512 MiB hace fallar a todos con 'ábralo y guárdelo de nuevo' |
| B1-06 | 🟠 Media | pequeño | alta | Dividir pidiendo solo Markdown de un PDF escaneado da 'dividido' y código 0, sin ningún Markdown |
| B1-05 | 🟠 Media | pequeño | alta | Unir cuenta como 'unidos' los Markdown vacíos o en blanco |
| B1-04 | 🟠 Media | medio | alta | Si una parte está abierta en otro programa, volver a dividir deja la carpeta con partes de dos cortes |
| B1-07 | 🟠 Media | medio | alta | Los nombres con etiqueta '(pdf)' dependen de la tanda y crean resultados duplicados o huérfanos |
| B1-08 | 🟠 Media | pequeño | media | Dividir un Excel calcula la memoria muy por debajo de lo real y se detiene tarde, después de minutos |
| B1-09 | ⚪ Baja | pequeño | alta | Dividir un Excel protegido con contraseña dice 'ábralo y guárdelo' en vez de 'tiene contraseña' |
| B1-10 | ⚪ Baja | pequeño | alta | La ayuda de la línea de comandos dice que Dividir es solo para PDF |

<details><summary>Detalle técnico y evidencia</summary>

- **B1-01 — Dividir un Excel con una hoja oculta falla el archivo entero, con un consejo equivocado**
  - *Impacto:* Muchas plantillas de oficina tienen una hoja oculta de listas o de cálculos. La persona pide '2 partes' y recibe 'No se pudo convertir este archivo. Ábralo en su programa y guárdelo de nuevo'. Guardarlo no arregla nada, porque el archivo está sano.
  - *Evidencia:* services/split/xlsx_cut.py:28-45 reparte workbook.worksheets sin mirar sheet_state y fija workbook.active = 0. Gemelo sintético: libro con 'Datos' (299 filas) y 'Listas' oculta (5 filas), `clearmd --split-parts 2 --keep both` → '0 split · 1 failed', con 'ValueError: The only worksheet of a workbook cannot be hidden'. En tests/ no hay ninguna prueba con sheet_state.
  - *Recomendación:* Repartir solo las hojas visibles. Las ocultas deben ir con todas las partes (suelen alimentar listas y fórmulas), y la hoja activa debe ser siempre una visible. Agregar una prueba con un libro de dos hojas, una de ellas oculta. Si se adopta B2-01 (dejar lo oculto fuera del Markdown), debe aplicarse solo al Markdown y nunca a las partes .xlsx, que según ADR-0047 no cambian por dentro.
- **B1-02 — Las partes de un CSV o de un texto cambian de codificación, y Excel muestra los acentos rotos**
  - *Impacto:* Una persona divide un CSV exportado desde Excel en español y abre una parte con doble clic: ve 'JosÃ©' y 'BogotÃ¡'. Parece que ClearMD le dañó los datos. Esto rompe la promesa del ADR-0047: 'nada dentro cambia'.
  - *Evidencia:* worker/pages.py:33-41 decodifica con decode_source, que quita el BOM y adivina cp1252. split_formats.py:53 escribe con atomic_write: UTF-8 sin BOM y LF (output_files.py:76-80). Prueba con CSV sintéticos en cp1252 y en UTF-8 con BOM, `--split-parts 2 --keep pdf`: las 4 partes quedan en UTF-8 sin BOM.
  - *Recomendación:* Escribir cada parte con los mismos bytes base que su original: la misma codificación, el mismo BOM y los mismos saltos de línea. Probar con el caso difícil: cp1252, CRLF y un campo entre comillas que tenga un salto de línea.
- **B1-03 — Unir PDF sanos que juntos pasan de 512 MiB hace fallar a todos con 'ábralo y guárdelo de nuevo'**
  - *Impacto:* Tres PDF escaneados de unos 190 MB, cada uno por debajo del límite, se marcan los tres como dañados. La persona revisa archivos que están bien y no se entera de que el problema era el tamaño total.
  - *Evidencia:* worker/pages.py:79-83 compara el PDF unido con max_result_chars (512 MiB) y devuelve CONVERSION_FAILED. merging.py:203-210 reparte ese error a todos los documentos. Prueba: 3 copias de un PDF sintético de 192 MB, `--merge pdf` → '0 merged · 3 failed', 'part too large: 576921065 bytes'.
  - *Recomendación:* Sumar los tamaños al planificar la unión en PDF y, si se pasan del límite, dar un motivo propio y comprensible ('juntos pesan 576 MB; el máximo es 512 MB'). Mejor aún: que el trabajador escriba el PDF unido directamente en un temporal de OutputUnif.
- **B1-06 — Dividir pidiendo solo Markdown de un PDF escaneado da 'dividido' y código 0, sin ningún Markdown**
  - *Impacto:* La persona pide 'conservar: Markdown' para dárselo a una IA, no sale ningún Markdown y el resultado aparece como logrado. En la línea de comandos el código de salida es 0. Es la misma familia de problemas que B5-03: Dividir dice 'se dividió' cuando no entregó lo pedido.
  - *Evidencia:* split_notes.py:43-51 se traga el ConversionError y devuelve None; splitting.py:166 siempre devuelve CONVERTED. PDF sintético de 4 páginas, solo imágenes, `--split-parts 2 --keep markdown` → '1 split · 0 failed', exit=0, y solo 2 PDF en la carpeta.
  - *Recomendación:* Si se pidió Markdown y no salió de ninguna parte, el resultado es 'con error' (o 'detenido'), con el motivo real y código 1. Si faltó en algunas partes, anotar el motivo de cada una. Usar la misma función de 'resultado vacío' que B1-05 y B5-01.
- **B1-05 — Unir cuenta como 'unidos' los Markdown vacíos o en blanco**
  - *Impacto:* Al unir tres .md de los que dos están vacíos, el resumen dice '3 unidos', y el archivo unido trae títulos sin nada debajo. Con un solo documento real no salta la regla de 'hacen falta dos'.
  - *Evidencia:* merging.py:96-98 lee el Markdown con cutter.read_text y lo agrega sin comprobar si tiene texto. Prueba: vacio.md (0 bytes), blancos.md y uno.md, `--merge markdown` → '3 merged · 0 failed'.
  - *Recomendación:* Usar en Unir la misma regla de vacío que Convertir (EMPTY_FILE o EMPTY_RESULT), y volver a contar los documentos válidos antes de exigir dos. Prueba: un .md de solo espacios, y una unión en la que queda un único documento real.
- **B1-04 — Si una parte está abierta en otro programa, volver a dividir deja la carpeta con partes de dos cortes**
  - *Impacto:* En Windows, Excel o el lector de PDF bloquean el archivo abierto. ClearMD dice 'no se pudo guardar', pero la carpeta ya mezcla partes del corte nuevo con partes del viejo. Una IA que lea la carpeta recibe contenido duplicado o desactualizado.
  - *Evidencia:* use_cases/part_stage.py:40-58: commit() hace os.replace parte por parte y no deshace si una falla. Simulación con PermissionError en la 2.ª parte: queda 'part 1 of 3' junto a las 4 'of 4' viejas.
  - *Recomendación:* Comprobar antes de mover que cada parte que se va a reemplazar se puede reemplazar. Si un movimiento falla, deshacer los ya hechos. Agregar una prueba con un archivo bloqueado en el CI de Windows.
- **B1-07 — Los nombres con etiqueta '(pdf)' dependen de la tanda y crean resultados duplicados o huérfanos**
  - *Impacto:* Con informe.pdf e informe.docx en la carpeta, los resultados llevan etiqueta. Si luego se borra el .docx y se convierte de nuevo con 'Conservar', aparece 'informe.md' junto a 'informe (pdf).md': la IA recibe duplicados, y 'Reemplazar si cambió' no funciona.
  - *Evidencia:* paths.py:93-121 pone la etiqueta solo si hay un choque dentro de la tanda, y planning.py:177 mira exists() sobre el nombre nuevo. Lo reproduje en dos ejecuciones con copias de tests/fixtures/documents/sample.*.
  - *Recomendación:* Antes de dar el nombre, buscar un resultado anterior del mismo original (con o sin etiqueta) y reutilizar ese nombre. Si el nombre cambia, decirlo. Probar en dos ejecuciones seguidas.
- **B1-08 — Dividir un Excel calcula la memoria muy por debajo de lo real y se detiene tarde, después de minutos**
  - *Impacto:* Un Excel mediano pasa el control del plan, trabaja varios minutos y termina 'detenido: sin memoria'. Es la misma puerta que deja pasar la bomba ZIP de B2-02: el control de Dividir usa el tamaño comprimido y un factor medido con el lector de solo lectura.
  - *Evidencia:* splitting.py:62-69 usa estimated_memory(XLSX) = 4 MiB por MiB, pero xlsx_cut.py:37 hace una carga completa con openpyxl una vez por parte. Medido: un xlsx sintético de 7,9 MB llega a 782 MiB de pico (~100 MiB por MiB) y `--split-parts 3` tarda 65 s contra ~7 s estimados. Volví a comprobar en planning.py:134-144 que la rama de Dividir termina en 'continue' antes de inspect_archive.
  - *Recomendación:* Usar un factor propio para cortar un Excel, aplicado al tamaño descomprimido (con inspect_archive, igual que en Convertir), y cargar el libro una sola vez por corte. Guardar la medición en docs/benchmarks.
- **B1-09 — Dividir un Excel protegido con contraseña dice 'ábralo y guárdelo' en vez de 'tiene contraseña'**
  - *Impacto:* Al convertirlo, el mismo archivo dice bien 'protegido con contraseña'. Al dividirlo dice que está dañado, y la persona no sabe que el problema es la contraseña.
  - *Evidencia:* xlsx_cut.py:18 y :38 llaman a openpyxl sin la revisión OLE/EncryptedPackage de conversion/xlsx.py:103-107. Con un gemelo sintético, `--split-parts 2` → 'BadZipFile'.
  - *Recomendación:* Juntarlo con B2-02 y B1-08 en una sola puerta de revisiones previas por formato (cifrado, OLE, bomba ZIP, memoria) que usen Convertir, Dividir y Unir.
- **B1-10 — La ayuda de la línea de comandos dice que Dividir es solo para PDF**
  - *Impacto:* Quien lee la ayuda cree que su CSV no se puede dividir, o no entiende por qué un Excel queda fuera con '--split-pages'.
  - *Evidencia:* `clearmd --help`: '--split-parts N split each PDF into N parts…'. En cambio, use_cases/splitting.py:47-57 (split_skip) acepta TXT, CSV y XLSX.
  - *Recomendación:* Corregir en.toml y es.toml con los formatos que acepta cada corte, y agregar una prueba que compare la ayuda con split_skip. Puede ir junto con la traducción de la ayuda de B5-05.

</details>

### Backend · Seguridad y privacidad — 7/10

Después de leer a los otros nueve auditores mantengo mi diagnóstico: la seguridad de ClearMD es muy superior a la media, y los huecos están en las herramientas nuevas (Dividir y Unir) y en los formatos distintos del PDF. El debate confirma un patrón que va más allá de mi lente: cada control nació en Convertir y no se copió a las otras puertas. Dividir un Excel no pasa por la revisión de bombas ZIP (B2-02), tampoco por la de cifrado (B1-09) y usa un factor de memoria muy bajo (B1-08). Unir acepta Markdown vacíos (B1-05). Volví a comprobar en el código que la rama de Dividir de planning.py termina en 'continue' antes de la revisión ZIP, que xlsx_cut.py abre el libro completo sin mirar si está cifrado ni qué hojas están ocultas, y que el 'p()' de la línea de comandos solo escapa los caracteres de control, sin ocultar rutas. No subo ninguna severidad. Mantengo mis 8 hallazgos y amplío B2-01 con el caso de Dividir que encontró B1-01: una hoja muy oculta puede terminar como una 'parte' propia. Nota 7/10.

**Fortalezas que vio:**

- Lecturas seguras de documentos no confiables: open_regular_file con O_NOFOLLOW y comprobación de archivo regular (backend/services/conversion/safe_files.py).
- Escrituras que resisten enlaces plantados: lstat por carpeta, mkstemp más os.replace, detección de uniones de Windows y un barrido que nunca entra en un enlace (use_cases/output_files.py). B1 llegó a la misma conclusión por su cuenta.
- Control de bombas ZIP antes de abrir, en Convertir: entradas, índice, expansión y tamaños declarados imposibles, con un mensaje claro (use_cases/archive.py).
- Un proceso de conversión nuevo en cada tarea, con límites de arranque, de tiempo por progreso, de memoria y de tamaño del resultado; sus procesos hijos mueren con él.
- Los convertidores de markitdown se llaman uno por uno, nunca MarkItDown(): no hay fallback a ZipConverter ni a exiftool.
- El XML propio rechaza DOCTYPE y entidades (xmltree.py), y EML se procesa en memoria.
- Una sola puerta de salida (safe_output): las imágenes remotas, UNC o con ruta absoluta pasan a texto y el HTML activo se escapa. El modo artículo deja los enlaces peligrosos como código visible.
- Las imágenes reciben nombres propios, se validan por sus bytes y tienen topes.
- Privacidad al reportar: Copiar Detalles pasa por without_paths y el texto pide revisar antes de enviar.
- Cadena de suministro de los ejecutables: acciones fijadas por SHA, uv sync --locked, la regla de dos semanas, el cliente flet con SHA-256 fijado y PyPI por Trusted Publishing.
- Instalador por usuario y sin administrador; el desinstalador pregunta antes de borrar los ajustes.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B2-01 | 🔴 Alta | medio | alta | Lo oculto en Word, Excel, PowerPoint y páginas web llega completo al Markdown, y al dividir un Excel, sin aviso |
| B2-02 | 🔴 Alta | pequeño | alta | Dividir un Excel se salta la protección contra bombas ZIP |
| B2-03 | 🟠 Media | medio | alta | El filtro de enlaces peligrosos falla si el texto del enlace lleva corchetes |
| B2-04 | 🟠 Media | pequeño | alta | La ventana flet instalada con pip o uv descarga un programa de internet al primer uso |
| B2-05 | ⚪ Baja | pequeño | alta | Ocultar rutas y nombres al reportar tiene huecos, y la línea de comandos no oculta nada |
| B2-06 | ⚪ Baja | medio | media | En Windows el proceso de conversión no tiene un tope de memoria duro |
| B2-07 | ⚪ Baja | pequeño | media | Quien instala con pip o uv tool no recibe las versiones revisadas del lock |
| B2-08 | ⚪ Baja | pequeño | alta | La suma SHA256SUMS no prueba de dónde viene la descarga |

<details><summary>Detalle técnico y evidencia</summary>

- **B2-01 — Lo oculto en Word, Excel, PowerPoint y páginas web llega completo al Markdown, y al dividir un Excel, sin aviso**
  - *Impacto:* Una persona convierte un Excel, una presentación o una carta para dárselos a una IA y le entrega también, sin saberlo, hojas muy ocultas (por ejemplo, salarios), filas y columnas ocultas, texto oculto de Word, notas del orador y diapositivas ocultas. En una página web pasa el texto oculto con hidden o con letra de tamaño 0, y en modo página completa también el que tiene display:none. Al dividir un Excel, una hoja muy oculta puede quedar como una 'parte' propia, o como la hoja activa de una parte. Es la misma vía de filtración y de instrucciones escondidas que el ADR-0054 cerró solo para PDF, y el resumen no dice nada.
  - *Evidencia:* Gemelos sintéticos de la ronda 1 (/tmp/audit-security/hidden e /tmp/audit-security/hidhtml en el contenedor): budget.xlsx con la columna C oculta, la fila 3 oculta y una hoja veryHidden: las tres llegan al .md. plan.pptx: las notas del orador y la diapositiva show=0 llegan al .md (markitdown/_pptx_converter.py:139-146). letter.docx: el texto con <w:vanish/> llega al .md. page.html: hidden y font-size:0 pasan en modo artículo, y display:none además en modo full. xlsx.py no menciona sheet_state. En la ronda 2 volví a revisar services/split/xlsx_cut.py:28-45: reparte workbook.worksheets sin mirar sheet_state y fija workbook.active = 0. Contraste: ODT sí trata lo oculto (odt/styles.py:132).
  - *Recomendación:* Extender el principio del ADR-0054 ('el Markdown contiene lo que la persona ve') a todos los formatos y a las tres herramientas, con un aviso en el resumen. Lo que se oculta para no mostrarlo (hojas muy ocultas, texto oculto de Word, HTML con hidden o display:none, letra de tamaño 0) se deja fuera y se avisa. Para las filas, columnas y hojas ocultas comunes, las notas del orador y las diapositivas ocultas, el dueño decide si quedan fuera o se incluyen marcadas, pero siempre con aviso. Al dividir, las hojas ocultas nunca son una parte propia ni la hoja activa (esto coincide con B1-01). Tests con el caso difícil: una hoja veryHidden, una sola columna oculta en medio y una sola nota del orador.
- **B2-02 — Dividir un Excel se salta la protección contra bombas ZIP**
  - *Impacto:* Si la persona elige Dividir, un Excel de 1,3 MB recibido por correo tiene la computadora ocupada unos 3 minutos y llega a 4 GB de memoria antes de detenerse. Con Convertir, el mismo archivo se rechaza al instante 'por seguridad'. El mensaje final además le aconseja 'dividirlo en archivos más pequeños' justo cuando estaba dividiendo. En Windows no hay un tope duro (B2-06), así que el equipo puede ponerse lento para todo lo demás.
  - *Evidencia:* Lo comprobé de nuevo en la ronda 2: en backend/use_cases/planning.py:134-144, la rama 'if split is not None' termina en 'continue' antes de 'if detection.format in ZIP_BASED: inspect_archive/unsafe_reason' (líneas 146-152). split_memory estima con el tamaño comprimido. xlsx_cut.py:37 carga el libro completo, una vez por parte. Ronda 1: con la bomba sintética (un xlsx de 1.308.655 bytes, con sheet1.xml de unos 380 MB), '--dry-run' la deja fuera ('grows 293 times'), pero '--dry-run --split-parts 2' responde 'would be split'. La ejecución real se detuvo por memoria a los 185 s. B1-08 midió por su cuenta que el factor de memoria de Dividir un Excel es unas 25 veces más bajo de lo real, lo que agrava este hueco.
  - *Recomendación:* Un único punto de control previo por formato (ZIP, cifrado, vacío) que pase antes de bifurcar entre Convertir, Dividir y Unir, con un test por herramienta que use la bomba sintética. Corregir el consejo del mensaje cuando la tarea es Dividir.
- **B2-03 — El filtro de enlaces peligrosos falla si el texto del enlace lleva corchetes**
  - *Impacto:* Un enlace cuyo texto lleva corchetes, o que envuelve una imagen, conserva su destino file:, javascript: o de carpeta compartida (\\servidor). En un visor de Markdown permisivo, un clic puede abrir un programa local o mandar las credenciales de Windows a otro equipo. Pasa con las páginas web en modo página completa, con los .txt y con el Markdown que se une.
  - *Evidencia:* Lo comprobé de nuevo en la ronda 2: en safe_output.py:24, _LINK = r"(?<!!)\[([^\]\n]*)\]" + _TARGET no admite ']' dentro del texto. En la ronda 1 salieron sin cambios '[![x](images/a.png)](file:///C:/...calc.exe)', '[a [b] c](javascript:alert(1))' y una definición de referencia en dos líneas. Extremo a extremo con '--html full': '[Open [the] form](file:///C%3A/Windows/System32/calc.exe)'.
  - *Recomendación:* Localizar enlaces, imágenes y definiciones con un analizador CommonMark real, o neutralizar cualquier '](' o ']:' seguido de file:, javascript:, vbscript:, data: o \\, sin mirar el texto que va antes. Agregar los cuatro casos como tests de la puerta única.
- **B2-04 — La ventana flet instalada con pip o uv descarga un programa de internet al primer uso**
  - *Impacto:* La promesa de no usar nunca internet se rompe para quien instala desde el repositorio, o pronto desde PyPI, con el extra flet: al abrir clearmd-flet se descarga el cliente Flutter desde GitHub, sin comprobar su suma. En Windows, ese cliente se comunica además por un puerto local sin contraseña.
  - *Evidencia:* flet_desktop/__init__.py:334-362 (ensure_client_cached → urlopen, sin hash). FLET_VIEW_PATH solo se fija en packaging/launch_flet.py. pyproject.toml:75 publica clearmd-flet. ADR-0042: 'nothing downloaded at run time'. flet_socket_server.py:100-108.
  - *Recomendación:* Si falta el cliente, no descargarlo: dar un mensaje claro o pedir permiso explícito. Documentarlo antes de publicar en PyPI y anotar el puerto local en SECURITY.md como límite conocido.
- **B2-05 — Ocultar rutas y nombres al reportar tiene huecos, y la línea de comandos no oculta nada**
  - *Impacto:* Al pegar los detalles de un error en la comunidad pública pueden quedar el nombre de una persona o la ruta de una carpeta privada, por ejemplo entre corchetes, empezando por ~/ o en el nombre de un archivo interno. En la línea de comandos, un error inesperado muestra la ruta completa.
  - *Evidencia:* Pruebas de la ronda 1 sobre privacy.without_paths: '[/srv/clientes/<nombre>/...]', '~/Documentos/...' y 'Informe_<nombre>.pdf' sin comillas salen intactos. Lo comprobé de nuevo en la ronda 2: frontend/cli/app.py:29 envuelve el detalle en p(), y p() (cli/report.py:51-53) solo escapa los caracteres de control; no llama a without_paths.
  - *Recomendación:* Aplicar without_paths en la línea de comandos. Aceptar '[' y ':' como inicio de ruta, igual que '~/'. Ocultar las palabras con extensión de documento aunque no lleven comillas. Pasar también los nombres omitidos. Agregar tests adversarios.
- **B2-06 — En Windows el proceso de conversión no tiene un tope de memoria duro**
  - *Impacto:* En Windows, la memoria solo se vigila cada 0,1 s. Una reserva grande y repentina puede volver lento el equipo entero antes de que ClearMD reaccione.
  - *Evidencia:* worker/child.py:51-65: apply_memory_cap usa RLIMIT_AS y no hace nada si no existe resource. El código no tiene ningún Job Object.
  - *Recomendación:* Usar un Job Object con JOB_OBJECT_LIMIT_PROCESS_MEMORY en Windows y probarlo con la bomba de B2-02 en el CI de Windows.
- **B2-07 — Quien instala con pip o uv tool no recibe las versiones revisadas del lock**
  - *Impacto:* Quien instala fuera de los ejecutables recibe la versión más nueva de cada dependencia, sin la regla de dos semanas que protege contra paquetes comprometidos.
  - *Evidencia:* pyproject.toml:29-50: rangos abiertos. constraint-dependencies y uv.lock solo aplican a uv sync. README recomienda 'uv tool install git+…'.
  - *Recomendación:* Publicar con cada versión un constraints.txt o un pylock.toml exportado del lock y documentar cómo usarlo.
- **B2-08 — La suma SHA256SUMS no prueba de dónde viene la descarga**
  - *Impacto:* La suma se publica en el mismo lugar que los archivos: detecta un archivo dañado, pero no uno reemplazado. El ejemplo de SECURITY.md usa la versión 1.2.0.
  - *Evidencia:* release.yml:230 genera SHA256SUMS.txt en el mismo job. No hay attest ni provenance. SECURITY.md: 'Get-FileHash .\ClearMD-Setup-1.2.0.exe'.
  - *Recomendación:* Agregar actions/attest-build-provenance (fijada por SHA) y explicar 'gh attestation verify' en SECURITY.md, con un nombre de archivo genérico. Es compatible con la firma por SignPath.

</details>

### Backend · Fidelidad del contenido para la IA — 6,5/10

Después del debate, mantengo el diagnóstico: ClearMD es muy bueno en tablas, fórmulas de ODT y LaTeX, el modo artículo y la unión de documentos. Su punto débil para la IA está en el lector de PDF cuando el documento no viene «de libro»: los párrafos se funden, los pies de página dibujados en segundo lugar se quedan, los títulos numerados se borran y las fracciones cortas cambian de significado sin aviso. Los colegas me hicieron ver dos agravantes que confirmé en el código. Primero, las notas que deberían avisar de estos problemas ni siquiera llegan a la pantalla de Resultados (F5-01): las ventanas muestran «todo bien» aunque el resumen diga «Necesita Tu Atención». Así, cualquier aviso honesto del lector queda escondido para quien no abre el resumen. Segundo, la regla de «sin texto = con error» decide sobre el Markdown que ya trae marcas del propio conversor (B5-01), y Excel pasa a la IA las hojas, filas y columnas ocultas (B2-01). Eso significa que la IA recibe lo que la persona no ve y que la persona no ve lo que la IA no recibe. Bajo un hallazgo propio (B3-03) de alta a media, porque el caso que lo dispara es más acotado de lo que lo califiqué. Nota: 6,5/10.

**Fortalezas que vio:**

- Tablas de PDF sin líneas reconstruidas con exactitud: 12 filas × 5 columnas sin perder ni inventar nada, una celda vacía respetada, una celda partida en dos líneas que se vuelve a unir y una tabla de dos páginas cuyo encabezado se repite en cada una.
- Ecuaciones numeradas reconstruidas como LaTeX con su número (\tag{4}); las que no logra reconstruir se avisan con sus páginas. Es honesto y no inventa.
- Fórmulas de ODT y LaTeX como LaTeX limpio, notas al pie como notas de Markdown, listas anidadas, citas y bloques de código conservados.
- Unir marca claramente dónde empieza cada documento y renumera las notas al pie para que no choquen (d2-1). Es lo que una IA necesita para no mezclar fuentes.
- El modo artículo quita cookies, menú, barra lateral y pie de página, y conserva títulos, listas, tablas y código.
- Al dividir Markdown, las partes juntas reproducen el archivo exacto y nunca se corta una tabla ni un bloque de código por la mitad.
- Los avisos de LaTeX y ODT nombran lo concreto (macros desconocidas, inclusiones no seguidas, celdas combinadas, comentarios omitidos).
- El CSV con punto y coma, decimales con coma y saltos de línea entre comillas sale como tabla correcta.
- El contenido hostil (HTML, enlaces javascript:, marcas de Markdown escritas como texto) se neutraliza y sigue siendo legible en modo artículo.
- La regla «sin texto = con error» se aplica después de safe_output, en un solo punto del trabajador (child.py:109-112). Es el lugar correcto; solo hay que afinar qué cuenta como texto.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B3-01 | 🔴 Alta | medio | alta | En los PDF, los párrafos solo se separan cuando hay un espacio en blanco: sangrías, bibliografías, títulos cortos y listas «a)» se funden en un solo bloque |
| B3-02 | 🔴 Alta | medio | alta | Un pie de página dibujado después del encabezado no se quita, aparece arriba de cada página, y el resumen dice que sí se quitó; además, la nota nunca dice qué textos tocó |
| B3-04 | 🔴 Alta | medio | alta | Una fracción sencilla sin número de ecuación cambia de significado sin aviso (1/2 sale como «1 2»; a/b + c/d sale como «a b + c d») |
| B3-03 | 🟠 Media | pequeño | alta | Se borran títulos numerados al inicio de páginas seguidas («Pregunta 1, 2, 3», «Capítulo N») porque se toman por encabezados repetidos |
| B3-05 | 🟠 Media | pequeño | alta | Al dividir por palabras, un título puede quedar suelto al final de una parte y su contenido empieza la siguiente sin contexto |
| B3-06 | 🟠 Media | pequeño | media | Los subtítulos con los tamaños normales de Word (13 y 12 pt sobre texto de 11 pt) no se reconocen como títulos |
| B3-08 | 🟠 Media | medio | alta | Excel pierde el formato de los números (12,5 % llega como 0.125) y toma la fila del título como encabezado; además, lo oculto de la hoja llega a la IA |
| B3-07 | 🟠 Media | medio | alta | Al convertir la carpeta de un proyecto LaTeX, los capítulos salen dos veces, con avisos falsos y un archivo de macros «con error»; las referencias a ecuaciones quedan sin destino |
| B3-09 | ⚪ Baja | pequeño | media | El modo artículo de las páginas web descarta el autor y la fecha de la noticia |
| B3-10 | ⚪ Baja | pequeño | alta | Las listas anidadas de PDF y PowerPoint pierden sus niveles |

<details><summary>Detalle técnico y evidencia</summary>

- **B3-01 — En los PDF, los párrafos solo se separan cuando hay un espacio en blanco: sangrías, bibliografías, títulos cortos y listas «a)» se funden en un solo bloque**
  - *Impacto:* Un libro, un documento legal o la bibliografía de un trabajo académico llegan a la IA como uno o dos bloques gigantes. La IA no sabe dónde termina una referencia ni dónde empieza un párrafo, y un título queda pegado a la primera frase del texto que le sigue. Los resúmenes, las citas y las búsquedas salen peor, y la persona no recibe ningún aviso.
  - *Evidencia:* CLI 2.13.0 sobre PDF sintéticos hechos con tests/support/pdf_builder.py: (a) 4 párrafos con la primera línea sangrada (x=90) y sin espacio extra → salen en UN párrafo; (b) 8 referencias con sangría francesa → UNA línea de ~900 caracteres; (c) 'Question 1' en negrita queda pegado a la frase siguiente; (d) pdf/F_lists.pdf: '- Second bullet a) letter item b) another letter item' (items.py:11 y 22-26 exigen mayúscula después de 'a)' y no reconocen números romanos). Un PDF académico real (privado) tiene un párrafo de 3.125 caracteres con ~18 referencias; su gemelo sintético es el (b). Raíz: el corte depende de PARAGRAPH_GAP (cleaner/params.py:7) y del final de frase.
  - *Recomendación:* Agregar tres señales de cambio de párrafo: sangría de primera línea, sangría francesa y una línea anterior que termina en punto y es claramente más corta que la columna. Tratar una línea corta en negrita y sin punto como párrafo aparte o título. Aceptar «a)», «b)» con minúscula cuando hay al menos dos seguidos, y «i.», «ii.». Probar con sangría sin espacio, bibliografía con sangría francesa y una lista «a) el arrendatario…».
- **B3-02 — Un pie de página dibujado después del encabezado no se quita, aparece arriba de cada página, y el resumen dice que sí se quitó; además, la nota nunca dice qué textos tocó**
  - *Impacto:* En extractos, facturas e informes hechos por programas, «Página 1 de 6» o «Confidencial» se repite dentro del texto, encima de cada página o en medio de una frase. El resumen asegura que los pies se quitaron, y eso no es verdad. Como la nota no dice qué textos se quitaron, la persona tampoco puede comprobar nada cuando sí se quitan.
  - *Evidencia:* PDF sintético de 6 páginas: encabezado en y=760, pie 'Page N of 6' en y=40, dibujados en ese orden, y después el cuerpo. La salida repite 'Page 1 of 6' arriba de cada página. Con 'Confidential - do not share' pasa igual. En C_table_two_pages.pdf queda '…over th Page 2 of 4' en medio del párrafo. El resumen dice 'headers, footers and page numbers repeated on the pages were left out'. Si el pie se dibuja primero, sí se quita. Raíz: cleaner/running.py usa el orden de dibujo (_apart, líneas 37-47; page_number solo mira el índice 0 o el último, líneas 96-99 y 111-112). La clave pdf_running_removed (en.toml:305) no lleva {items}.
  - *Recomendación:* Ordenar las líneas de cada página por su posición vertical antes de buscar encabezados y pies, y poner el pie al final de la página. La nota debe listar los textos quitados (por ejemplo, los tres primeros) para que nunca afirme algo que no hizo. La prueba debe usar el orden encabezado → pie → cuerpo.
- **B3-04 — Una fracción sencilla sin número de ecuación cambia de significado sin aviso (1/2 sale como «1 2»; a/b + c/d sale como «a b + c d»)**
  - *Impacto:* La IA lee «p = 1 2» como «p = 12» y «a b + c d» como una multiplicación. El contenido no llega desordenado: llega cambiado. Como no hay aviso, ni la persona ni la IA tienen motivo para dudar. En apuntes, exámenes y fórmulas de negocio (márgenes, tasas) esto da respuestas equivocadas.
  - *Evidencia:* PDF sintético con 'p =' y '1' sobre '2' separados por una raya de 14 pt → 'p = 1 2'. 'y = a/b + c/d' con dos rayas de 14 pt → 'y = a b + c d'. En ninguno aparece pdf_equations_as_text en el resumen. Con '(4)' a la derecha sí sale '\frac{a}{b} + \frac{c}{d} \tag{4}'. tests/acceptance/test_015_equations_as_latex.py:26-37 usa una raya de 30 pt con 'a + b' arriba: es el caso fácil (lecciones XIII.1). Detección: equations/bars.py:22-80.
  - *Recomendación:* Aceptar rayas cortas (una o dos letras arriba y abajo) y varias rayas en la misma línea. Como red de seguridad, si hay una raya con texto justo arriba y justo abajo que no se convirtió, agregar la nota «ecuaciones que conviene revisar» con la página. Probar con 1/2 y con a/b + c/d sin número.
- **B3-03 — Se borran títulos numerados al inicio de páginas seguidas («Pregunta 1, 2, 3», «Capítulo N») porque se toman por encabezados repetidos**
  - *Impacto:* En un examen, un formulario o un libro con un capítulo por página, la IA recibe el contenido sin los títulos que lo ordenan y no sabe qué respuesta va con qué pregunta. La persona solo lee «se omitieron encabezados y pies repetidos».
  - *Evidencia:* PDF sintético de 10 páginas con 'Question 1..3' en negrita, 11 pt, en y=740 de las páginas 1 a 3: se ELIMINAN. pdf/H_chapters.pdf: los 8 'Chapter N' desaparecen. Raíz: cleaner/running.py:52-62 (_running_keys) toma como encabezado repetido una línea cuyo número avanza con la página, y con 3 páginas basta (MIN_RUNNING_PAGES=3, línea 17). Solo se protege una línea más grande que el cuerpo (HEADING_RATIO), no la negrita. Bajo la severidad de alta a media: hace falta que el número coincida con el avance de las páginas, un caso más acotado que B3-01, B3-02 y B3-04.
  - *Recomendación:* Quitar una línea con número como encabezado repetido solo si es más pequeña que el cuerpo o es un número de página reconocido, nunca si es una línea en negrita del tamaño del cuerpo. La nota debe listar lo quitado (ver B3-02). Probar con «Pregunta 1-3» en las páginas 1-3 de un documento de 10.
- **B3-05 — Al dividir por palabras, un título puede quedar suelto al final de una parte y su contenido empieza la siguiente sin contexto**
  - *Impacto:* Si la persona le da a la IA la parte 3, la IA lee el texto de la «Sección 2» sin saber que lo es, y la parte 2 termina con un título vacío.
  - *Evidencia:* Markdown sintético de 2.696 palabras y 3 secciones, con --split-words 500: la parte 2 termina con '## Section 2' y la parte 3 empieza con el texto de esa sección. split/markdown_cut.py:_by_words (desde la línea 59). ADR-0045:30 promete que 'los cortes caen en los títulos'.
  - *Recomendación:* Mantener un título siempre unido al bloque que le sigue: si el corte cae justo después de un título, moverlo antes del título. La línea de contexto al inicio de cada parte se puede evaluar como comentario HTML, enmendando ADR-0045. Probar con un título exactamente en el punto de corte.
- **B3-06 — Los subtítulos con los tamaños normales de Word (13 y 12 pt sobre texto de 11 pt) no se reconocen como títulos**
  - *Impacto:* La mayoría de los documentos salen de Word con sus estilos de siempre. Solo los títulos principales quedan marcados, y la IA pierde la estructura de las secciones.
  - *Evidencia:* PDF sintético con 28/16/13/12 pt sobre 11 pt: los de 13 pt salen como párrafos y el de 12 pt en negrita queda pegado al texto. cleaner/params.py:5 HEADING_RATIO = 1.2 (13/11 = 1,18). La excepción por negrita en cleaner/headings.py:46-56 solo vale con número delante.
  - *Recomendación:* Bajar el umbral a ~1,15, o aceptar como título una línea corta, sola, sin punto, con espacio arriba, más grande o en negrita. Probar con 16/13/12 sobre 11.
- **B3-08 — Excel pierde el formato de los números (12,5 % llega como 0.125) y toma la fila del título como encabezado; además, lo oculto de la hoja llega a la IA**
  - *Impacto:* La IA lee «0.125» donde la persona ve «12,5 %» y «1234.5» donde ve «1.234,50 USD», así que puede responder mal sobre porcentajes y dinero. Con un título arriba, la tabla queda con el encabezado equivocado. Y, como confirmó B2-01, las filas, columnas y hojas ocultas pasan a la IA sin aviso: la IA recibe una tabla que la persona no ve.
  - *Evidencia:* Libro sintético: C4 con formato '0.0%' y valor 0.125; D4 '#,##0.00 [$USD]' con 1234.5; título en A1 y encabezado real en la fila 3 → '\| R0 \| 2026-01-01 \| 0.125 \| 1234.5 \|' y encabezado '\| Quarterly sales report \| …'. services/conversion/xlsx.py:63 recorre iter_rows(values_only=True) sin mirar number_format, ni column_dimensions/row_dimensions .hidden, ni sheet_state (grep de hidden/sheet_state: sin resultados). Una fórmula sin valor guardado sale vacía y sin aviso.
  - *Recomendación:* Aplicar los formatos básicos que openpyxl ya da (porcentaje, miles, decimales fijos, moneda, fecha), o al menos el porcentaje. Usar como título de la hoja una primera fila con una sola celda sobre una fila más ancha. Tratar lo oculto según la regla común que propone B2-01, con aviso. Avisar de las fórmulas sin valor guardado.
- **B3-07 — Al convertir la carpeta de un proyecto LaTeX, los capítulos salen dos veces, con avisos falsos y un archivo de macros «con error»; las referencias a ecuaciones quedan sin destino**
  - *Impacto:* Quien convierte la carpeta de su tesis le entrega a la IA cada capítulo dos veces: dentro del principal (bien) y suelto (con comandos sin expandir). La persona ve una ❌ en un archivo de macros normal y avisos de «no encontrado» que no son ciertos. Y «ver la ecuación (eq:pit)» apunta a una ecuación sin número.
  - *Evidencia:* tests/fixtures/tex/thesis: main.md incluye ch1, ch2 y deeper, pero también se escriben chapters/ch1.md (con '\R', '\norm{x}' sin expandir y una imagen no encontrada), ch2.md (aviso falso 'chapters/sections/deeper (not found)') y deeper.md; macros.tex sale '❌ … found no text to read'. paper.tex: '(eq:pit)' con la ecuación sin número.
  - *Recomendación:* En una misma tarea, un .tex incluido por otro que también se convierte va a «Dejados fuera: es parte de main.tex», y un archivo que solo tiene macros tampoco se marca como fallido. Numerar las ecuaciones con etiqueta (\tag{1}) y convertir \ref y \eqref a ese número.
- **B3-09 — El modo artículo de las páginas web descarta el autor y la fecha de la noticia**
  - *Impacto:* La fecha cambia el sentido de una noticia para una IA, y hoy se pierde sin aviso.
  - *Evidencia:* HTML sintético con '<p class="byline">By A. Writer, 3 March 2026</p>' debajo del h1: la salida elimina la línea y el resumen no trae ninguna nota. trafilatura ya extrae el autor y la fecha (ADR-0025:72, htmldate).
  - *Recomendación:* Debajo del «# Título», escribir en cursiva el autor y la fecha cuando el extractor los encuentre, como ya se hace con el autor de un .tex.
- **B3-10 — Las listas anidadas de PDF y PowerPoint pierden sus niveles**
  - *Impacto:* Un sub-punto llega a la IA al mismo nivel que su punto principal, y se pierde qué depende de qué.
  - *Evidencia:* pdf/F_lists.pdf: 'o Nested bullet' (x=90) sale como '- Nested bullet' al mismo nivel (cleaner/items.py:10 reconoce la viñeta, pero no la sangría). En un .pptx sintético, el nivel 1 sale como 'First point\nSub point', que en Markdown se junta en un solo párrafo (markitdown).
  - *Recomendación:* PDF: usar la sangría de la viñeta para anidar. PowerPoint: anotarlo como requisito del reemplazo de markitdown en 3.0.0, sin tocarlo en 2.x.

</details>

### Backend · Eficiencia y empaquetado — 7/10

Después del debate mantengo los ocho hallazgos y cambio el orden y dos severidades. Primero van los que una persona nota al usar la app: el lector de PDF denso es lento y pasa un tercio del tiempo sin mostrar progreso (B4-04), y el worker importa todos los conversores en cada tarea (B4-03). Bajo B4-01 (la descarga única de 235 MB en Linux) de alta a media, porque el público principal está en Windows, donde ya existe un instalador ligero de 30 MB. Los colegas confirmaron en el código tres problemas de mi lente que no vi en la ronda 1 y que comprobé yo mismo. (1) Dividir no pasa por el control de bombas ZIP: la rama de Dividir termina con un 'continue' antes de ese control (planning.py). (2) Dividir un Excel carga el libro completo con openpyxl una vez por cada parte (xlsx_cut.py:36), y la estimación de memoria no lo refleja. (3) Unir PDF devuelve el PDF entero por la tubería del worker, con un tope de 512 MiB y un mensaje equivocado. Con el mismo grep que hizo B2 confirmé otro: la app flet instalada con pip descarga su cliente de internet, porque FLET_VIEW_PATH solo se fija en el ejecutable empaquetado. Ninguno de estos problemas rompe resultados correctos, pero todos cuestan tiempo, memoria o confianza a una persona no técnica. Nota: 7/10, sin cambios.

**Fortalezas que vio:**

- El instalador ligero de Windows pesa 30 MB y la CI pone topes de tamaño a cada programa (packaging/check_executables.sh; ADR-0052). Hay que mantener esos topes.
- Los ejecutables dejan fuera magika, onnxruntime, numpy y pandas, y la CI lo comprueba en la lista de módulos.
- Las ventanas no cargan los conversores: el trabajo pesado vive solo en el worker y el backend añade unos 0,1 s al arranque de la ventana.
- La memoria del PDF está contenida: 300 páginas densas con unos 50 MiB de pico, porque el lector va página por página.
- Dividir un PDF es rápido y no infla las partes, y con --keep both el documento se convierte una sola vez.
- La estimación del CSV es realista (estimado 2,4 s y 379 MiB; medido 1,54 s y 436 MiB).
- La CI sube un JUnit con el tiempo de cada test, lo que permite perfilarla sin adivinar.
- El cliente flet del ejecutable va fijado por SHA-256 y el launcher apunta a él (packaging/launch_flet.py): en el ejecutable no se descarga nada.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B4-04 | 🟠 Media | medio | alta | Leer PDF con mucho texto es lento y durante un tercio del tiempo no se muestra progreso |
| B4-03 | 🟠 Media | medio | alta | El worker carga todos los conversores al arrancar, aunque solo vaya a convertir un PDF |
| B4-01 | 🟠 Media | pequeño | alta | En Linux solo hay una descarga de 235 MB con las cuatro apps; no existe una versión ligera |
| B4-05 | 🟠 Media | medio | media | El instalador completo y el archivo de Linux llevan el mismo Python y las mismas librerías tres veces |
| B4-02 | 🟠 Media | pequeño | alta | La limpieza de memoria después de cada test sigue corriendo en casi mil tests que no abren ninguna ventana |
| B4-07 | ⚪ Baja | pequeño | alta | Instalado desde PyPI, el worker carga magika y onnxruntime sin usarlos |
| B4-06 | ⚪ Baja | medio | media | La CI corre todo en serie y Windows marca el ritmo, en parte por tests que escriben muchos archivos |
| B4-08 | ⚪ Baja | pequeño | alta | Los límites de tiempo de arranque en la CI son tan amplios que no detectan una regresión |

<details><summary>Detalle técnico y evidencia</summary>

- **B4-04 — Leer PDF con mucho texto es lento y durante un tercio del tiempo no se muestra progreso**
  - *Impacto:* Un informe o libro largo con páginas llenas de texto avanza a unas 22–26 páginas por segundo en un equipo potente, y más despacio en un portátil. Durante la primera pasada la barra se queda en 'página 0 de N' varios segundos, y la persona puede creer que la app se colgó.
  - *Evidencia:* Gemelo sintético: PDF de 300 páginas (tests/fixtures/builders/pdf.py:minimal_pdf, 42 líneas de unos 85 caracteres por página, 1,26 MB). Conversión: 11,5 s; con la CLI: 13,5 s. La primera pasada (fonts.count) tarda 3,6 s de 10,8 s, y pdf/reader.py:32-35 no llama a report() hasta la segunda pasada. cProfile: 2.056.750 llamadas a ctypes.cast (fonts.py:52). Estimación limits.py:24 = 4 s/MiB; lo medido en texto denso es 9–16 s/MiB.
  - *Recomendación:* Mostrar la primera pasada en el progreso ('Leyendo fuentes… página X de N'). No convertir el puntero en cada carácter: comparar el objeto de texto solo cuando cambia. Añadir este PDF denso a los benchmarks con un mínimo de páginas por segundo.
- **B4-03 — El worker carga todos los conversores al arrancar, aunque solo vaya a convertir un PDF**
  - *Impacto:* Cada tarea espera más de un segundo antes del primer archivo, y más en Windows. Como el worker se arranca nuevo en cada tarea (decisión del dueño), esa espera se paga siempre. El cálculo del 'tiempo restante' parte de un arranque de 0,7 s que ya no es real.
  - *Evidencia:* registry.py:56-71: build_registry importa siempre markitdown, trafilatura, ODT, TeX, Excel, RTF, EML y subtítulos (lo volví a leer en la ronda 2). En el contenedor, el worker está listo en 1,35 s; build_registry completo tarda 0,89–1,0 s y solo PDF más safe_output, 0,36–0,45 s. limits.py:86 worker_startup_seconds = 0.7. Windows CI: unos 5,8 s hasta el primer archivo, frente a 2,0 s en Linux.
  - *Recomendación:* Mantener un worker nuevo por tarea, pero crear cada conversor la primera vez que se use (una fábrica por formato). Medir 'worker listo' con el ejecutable en la CI de Windows y actualizar worker_startup_seconds.
- **B4-01 — En Linux solo hay una descarga de 235 MB con las cuatro apps; no existe una versión ligera**
  - *Impacto:* En Linux, quien quiere solo la App Clásica descarga 235 MB, unas 8 veces lo que se descarga en Windows por lo mismo. Con una conexión lenta o con datos medidos, es una mala primera impresión. Bajo la severidad: el público principal usa Windows, donde ya hay instalador ligero.
  - *Evidencia:* Release v2.12.0: ClearMD-v2.12.0-linux.tar.gz = 235.296.790 bytes (Qt _internal 203 MB, Flet 83 MB, flet-client 41 MB, ClearMD 44,7 MB, clearmd-cli 44,7 MB). packaging/package.sh:41-46 mete en el mismo tar las carpetas Qt, Flet y las demás (releído en la ronda 2). ADR-0038:19.
  - *Recomendación:* Aplicar ADR-0052 también en Linux: un tar.gz ligero con la App Clásica (unos 45 MB) y archivos aparte para las demás apps y la línea de comandos, con su tope en check_executables.sh.
- **B4-05 — El instalador completo y el archivo de Linux llevan el mismo Python y las mismas librerías tres veces**
  - *Impacto:* La edición completa pesa 167 MB, de los que unos 40–50 MB son copias idénticas. El tope de la CI (190 MB) está cerca, así que cualquier librería nueva lo rompe.
  - *Evidencia:* Los zips de Windows v2.12.0 comparten 55,5 MB idénticos (nombre y CRC) entre Qt y Flet: python313.dll, pdfium.dll, libcrypto, lxml y PIL. En Linux comparten 80,7 MB. PIL/_avif (7,9 MB) va en cada copia y nunca se carga. clearmd.iss:65-66: lzma2 sólido con el diccionario por defecto.
  - *Recomendación:* Opción barata: subir LZMADictionarySize, agrupar las copias y medir la ganancia. Opción de fondo: una carpeta de runtime compartida. Quitar los plugins de Pillow que no se usan, con un test de iconos.
- **B4-02 — La limpieza de memoria después de cada test sigue corriendo en casi mil tests que no abren ninguna ventana**
  - *Impacto:* Indirecto: cada arreglo y cada release esperan de 2 a 3 minutos más de CI por trabajo, y los ciclos de arreglar y reintentar se alargan.
  - *Evidencia:* tests/conftest.py:57-70 (releído en la ronda 2): gc.collect() cuando la ruta contiene 'gui', 'frontend', 'window'... El JUnit del 2026-11-10 da 975 tests que coinciden, con mediana de 0,212 s, frente a 0,006 s del resto. test_gui_layers.py suma 77 s en Linux y 92 s en Windows sin abrir ninguna ventana.
  - *Recomendación:* Hacer la limpieza solo según el fixture que pide el test ('display' o 'window') o cuando de verdad se creó un objeto Tk, no según la ruta. Ahorro esperado: unos 100–150 s por trabajo.
- **B4-07 — Instalado desde PyPI, el worker carga magika y onnxruntime sin usarlos**
  - *Impacto:* Quien instala con pip lleva unos 100 MB de librerías que no usa, y cada worker ocupa unos 21 MiB más.
  - *Evidencia:* Después de build_registry, onnxruntime aparece en sys.modules y la memoria (RSS) es de 107 MiB; con la sustitución de packaging/no_magika.py, 86 MiB. ADR-0032: nunca se crea MarkItDown().
  - *Recomendación:* Aplicar la misma sustitución vacía en worker/child.py antes de importar markitdown.
- **B4-06 — La CI corre todo en serie y Windows marca el ritmo, en parte por tests que escriben muchos archivos**
  - *Impacto:* Indirecto: los arreglos tardan más en llegar; las rondas de Windows duran de 16 a 18 minutos.
  - *Evidencia:* Run del 2026-11-10: Linux 11,5 min, Windows 16 min. ci.yml:52 sin -n. html/test_output_guarantee tarda 65 s en Windows frente a 4,3 s en Linux. Hipótesis sin verificar: el antivirus del runner.
  - *Recomendación:* Primero B4-02. Después, pytest-xdist solo para el backend, y que las pruebas de garantía de HTML trabajen en memoria.
- **B4-08 — Los límites de tiempo de arranque en la CI son tan amplios que no detectan una regresión**
  - *Impacto:* Si el arranque se vuelve el doble de lento, nada avisa; la persona lo nota antes que el equipo.
  - *Evidencia:* check_executables.sh:35 SLOW_SECONDS=30, con valores reales de 3,5 a 7,8 s. No se mide el tiempo hasta el primer archivo convertido.
  - *Recomendación:* Guardar una línea base por sistema y fallar si se supera 1,5 veces; medir también 'lanzar → primer archivo convertido'.

</details>

### Backend · Claridad es cariño — 6,5/10

Después del debate mantengo el diagnóstico: el tono de ClearMD es amable y casi siempre útil, pero en los bordes los mensajes prometen algo falso o no llevan a ningún lado. El debate confirmó, con lo que revisé en el código, un patrón que en la primera ronda vi solo en parte. Muchos fallos que no son un archivo dañado (una hoja oculta al dividir, un Excel con contraseña al dividir, una unión que pasa de 512 MiB) caen en el código genérico CONVERSION_FAILED y reciben el consejo "Ábrelo en su programa y guárdalo de nuevo" (es.toml:17), que no los arregla. Otros consejos no siguen la herramienta activa: dicen "divídelo" a quien ya está dividiendo, o "Hazlo visible" para un archivo de sistema. Lo agrego como hallazgo propio (B5-11). Confirmo también que la ventana de Resultados no muestra las notas (F5-01), que la línea de comandos termina con código 0 cuando no hizo nada (B5-02) y que Unir cuenta como "unidos" los Markdown vacíos (B1-05), un caso más de la misma promesa sin cumplir que B5-01. Uní B5-09 con B5-08: las dos tratan de páginas públicas de política. Nota: 6,5/10, sin cambios.

**Fortalezas que vio:**

- Cada archivo que falla o se omite trae la causa y qué hacer, en tono amable y sin culpar ('Este archivo está vacío… revisa que se haya descargado completo', 'por seguridad no se abre'): es.toml [error] y [skip_action].
- Un solo canal para reportar (la comunidad o un correo, sin exigir cuenta de GitHub), con aviso de privacidad: 'copia solo el detalle técnico, nunca el resumen completo'.
- El resumen tiene un titular humano ('Se convirtieron 2 de 5 documentos. 3 cosas necesitan tu atención'), dice dónde están los archivos y separa lo que falló de lo que se dejó fuera a propósito.
- Los plurales están bien en los dos idiomas y un test verifica que los dos catálogos tengan las mismas claves.
- La Copia de Detalles reconoce sus límites ('Intentamos ocultar los nombres… revisa que no quede ninguno'). Es honestidad que no hay que perder.
- El instalador usa nombres sencillos, es honesto sobre el lector de pantalla y los tamaños, y aclara que desinstalar nunca toca los documentos.
- Un PDF escaneado falla con su razón y un paso siguiente concreto (OCR), con código de salida 1 (child.py:110-112).
- Cuando un error se debe a algo que la persona sí puede arreglar (vacío, contraseña en Convertir, bomba ZIP), el mensaje es específico. El problema aparece solo cuando el código cae en el mensaje genérico.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B5-01 | 🔴 Alta | pequeño | alta | La promesa de la 2.13 de que 'un resultado en blanco falla' no se cumple en los casos reales: presentación con una diapositiva vacía, Excel vacío, Unir con Markdown vacíos |
| B5-02 | 🔴 Alta | pequeño | alta | La línea de comandos dice 'Nada que convertir' y termina como si todo hubiera salido bien |
| B5-11 | 🟠 Media | medio | alta | Muchos fallos que no son un archivo dañado reciben el consejo 'ábrelo y guárdalo de nuevo', y otros consejos no siguen la herramienta activa |
| B5-03 | 🟠 Media | pequeño | alta | Dividir dice 'se dividió' cuando dejó una sola parte, y 'dividido' cuando no salió el Markdown pedido |
| B5-04 | 🟠 Media | pequeño | alta | El README (español e inglés) contradice al producto en varios puntos que ve el público |
| B5-05 | 🟠 Media | pequeño | alta | La ayuda de la línea de comandos en español está a medio traducir y dice que Dividir es solo para PDF |
| B5-06 | 🟠 Media | pequeño | alta | Algunos pasos siguientes no llevan a ningún lado o no corresponden al archivo |
| B5-07 | 🟠 Media | pequeño | alta | Las notas de versión le hablan al público del proceso interno y mezclan los idiomas en cada viñeta |
| B5-10 | ⚪ Baja | medio | media | El resumen en español mezcla inglés y deja ver etiquetas HTML |
| B5-08 | ⚪ Baja | pequeño | alta | Las páginas de política (seguridad, firma) y los formularios no acompañan a quien lee en español, tienen ejemplos viejos y hablan de una firma que no existe |

<details><summary>Detalle técnico y evidencia</summary>

- **B5-01 — La promesa de la 2.13 de que 'un resultado en blanco falla' no se cumple en los casos reales: presentación con una diapositiva vacía, Excel vacío, Unir con Markdown vacíos**
  - *Impacto:* Una presentación nueva siempre trae al menos una diapositiva y un Excel nuevo siempre trae una hoja. Si están vacíos, ClearMD dice 'convertido' y deja un Markdown sin contenido. Al unir, los .md vacíos cuentan como 'unidos' y el archivo unido trae títulos sin nada debajo. La persona se lo da a su IA creyendo que lleva el documento, aunque las notas de la 2.13.0 prometen lo contrario.
  - *Evidencia:* child.py:110 `if not markdown.strip()`: el comentario `<!-- Slide number: 1 -->` o el `## Sheet` que pone el conversor cuentan como texto. Casos sintéticos (python-pptx/openpyxl, /tmp/audit-b5 del contenedor): pptx con una diapositiva vacía → '1 convertido'; libro vacío → 'convertido'. Solo la presentación de cero diapositivas falla. merging.py:96-98: un Markdown se lee con cutter.read_text sin comprobar si tiene texto (lo revisé yo; B1-05 lo midió). test_040_promises_kept.py:41-46 solo usa un PDF escaneado.
  - *Recomendación:* Una sola regla de 'sin texto' para las tres herramientas, que mida lo que vería una persona: quitar primero los comentarios y los encabezados que pone el propio conversor (nombre de hoja, número de diapositiva). Prueba de aceptación con el caso difícil: una diapositiva vacía, un libro vacío, un HTML con solo espacios y una unión con un .md de solo espacios.
- **B5-02 — La línea de comandos dice 'Nada que convertir' y termina como si todo hubiera salido bien**
  - *Impacto:* Con una carpeta vacía, o al unir en PDF archivos que no son PDF, la persona solo lee 'Nada que convertir.', sin razón, sin paso siguiente y con el verbo equivocado si estaba uniendo. El programa termina con código 0 ('todo convertido'), así que un script o un acceso directo creen que funcionó.
  - *Evidencia:* frontend/cli/flow.py:80-87: si plan.is_empty y hay omitidos, imprime cli.nothing_to_split o cli.nothing_to_convert (no hay variante para Unir) y devuelve EXIT_OK. Ejecutado: `clearmd e --lang es` (carpeta vacía) → 'Nada que convertir.', exit=0. `clearmd m/a.md m/b.md --merge pdf` → 'Nothing to convert.' y los motivos DESPUÉS, exit=0. El README documenta el 2 para 'ninguna entrada válida'.
  - *Recomendación:* Que cada 'nada que hacer' diga por qué y qué hacer, use el verbo de la herramienta, ponga el motivo antes de la conclusión y termine con código 2. Un test por herramienta con carpeta vacía y con 'todo omitido'.
- **B5-11 — Muchos fallos que no son un archivo dañado reciben el consejo 'ábrelo y guárdalo de nuevo', y otros consejos no siguen la herramienta activa**
  - *Impacto:* La persona revisa y vuelve a guardar archivos que están sanos, sin saber que el problema era una hoja oculta, una contraseña o el tamaño total de la unión. A quien ya está dividiendo se le aconseja 'divídelo en partes', y a quien tiene un desktop.ini de sistema, 'Hazlo visible'. El mensaje que debía ayudar la deja sin salida.
  - *Evidencia:* es.toml:17 (error genérico) 'Ábrelo en su programa original y guárdalo de nuevo'. A ese código CONVERSION_FAILED llegan casos que mis colegas midieron y cuyo camino confirmé leyendo el código: la hoja oculta al dividir (B1-01, ValueError de openpyxl), el xlsx con contraseña al dividir (B1-09; xlsx_cut.py no tiene la revisión OLE de xlsx.py) y una unión de más de 512 MiB (B1-03; pages.py devuelve CONVERSION_FAILED). Consejos que ignoran la herramienta: en.toml:33 y :38 'Try splitting it into smaller…' también al dividir (B2-02 lo vio en una tarea de Dividir); es.toml:95 skip_action.hidden 'Hazlo visible para convertirlo.' aplicado a archivos de sistema (scan_rules.py, F5-02).
  - *Recomendación:* Regla de catálogo: el consejo 'guárdalo de nuevo' solo para un archivo que de verdad no se pudo leer. Cada causa conocida tiene su propio código y texto (hoja oculta, contraseña, tamaño total de la unión). Los consejos dependen de la herramienta activa (nunca 'divídelo' dentro de Dividir). Un test que recorra los casos sintéticos de B1-01, B1-03 y B1-09 y falle si el texto que sale es el genérico.
- **B5-03 — Dividir dice 'se dividió' cuando dejó una sola parte, y 'dividido' cuando no salió el Markdown pedido**
  - *Impacto:* Quien pide 3 partes y recibe una lee 'El documento se dividió', '1 dividido' y, en la terminal, 'convertido con notas'. Quien pide 'conservar: Markdown' de un PDF escaneado recibe 'dividido' con código 0 y ningún Markdown. En los dos casos el titular de éxito tapa la explicación real.
  - *Evidencia:* `clearmd one/a.md --split-parts 3 --lang es` → 'ℹ a.md — convertido con notas', '1 dividido', exit=0; resumen '⚠️ **El documento se dividió.**' con '3 → 1', y una carpeta OutputMD/ vacía. Claves: cli.converted_with_notes, summary.split_headline.all.one, note.parts_fewer. El caso del Markdown que no sale lo midió B1-06 (split_notes.py:43-51 se traga el error). Lo confirmé en el código.
  - *Recomendación:* Con una sola parte, un titular que diga la verdad ('No se pudo dividir en 3: el documento es corto, queda entero'). Si se pidió Markdown y no salió de ninguna parte, 'con error' con el motivo real y código 1 (B1-06). En la terminal, un texto propio de Dividir, la cifra en palabras y sin carpetas vacías.
- **B5-04 — El README (español e inglés) contradice al producto en varios puntos que ve el público**
  - *Impacto:* Lo primero que lee alguien que llega al proyecto le dice que las páginas web se convierten completas por defecto (es al revés), le muestra mensajes y tablas que ya no existen, no menciona Dividir ni Unir en la línea de comandos y sigue diciendo 'en construcción'. Cada contradicción le resta confianza a todo lo demás.
  - *Evidencia:* README.es.md y README.md: '`--html {full,article}` \| la página completa (por defecto)', frente a schemas/settings.py:17 html_strategy='article' y `clearmd --help`. El ejemplo de bomba ZIP dice 'posible bomba ZIP' y la salida real dice 'por seguridad no se abre'. La tabla del resumen tiene columnas viejas. Dice '23'/'25' ADRs y hay 55. Faltan --split-*, --merge, --changed, --images y --summary-pdf, y OutputSep/OutputUnif. F4-10 lo confirmó de forma independiente.
  - *Recomendación:* Generar o verificar desde el código la tabla de opciones y los ejemplos de salida, con un test. Corregir --html, sumar las tres herramientas, quitar 'en construcción' y llamar la sección 'Cómo usarla'.
- **B5-05 — La ayuda de la línea de comandos en español está a medio traducir y dice que Dividir es solo para PDF**
  - *Impacto:* Quien pide ayuda en español ve 'usage:', 'positional arguments', 'options'. Si escribe mal una opción, el error sale entero en inglés. La ayuda dice 'divide cada PDF…', así que quien tiene un CSV o un Excel cree que no puede dividirlo. El instalador enseña `clearmd-cli` y la ayuda dice `clearmd`.
  - *Evidencia:* `clearmd --help --lang es`: envoltorio de argparse en inglés. `--split-words 100` → 'clearmd: error: argument --split-words: must be from 500 to 1000000: 100'. es.toml:140-142: split_parts/split_pages 'divide cada PDF…', split_words 'cada PDF o Markdown' (revisado), mientras splitting.py:47-57 acepta TXT, CSV y XLSX (B1-10). Formas verbales mezcladas en [cli.help]. parser.py:14 prog='clearmd' frente a clearmd.iss:146 'clearmd-cli'.
  - *Recomendación:* Traducir el envoltorio de argparse y sus errores, con causa y ejemplo. Usar una sola forma verbal. Decir qué formatos acepta cada corte, con un test contra split_skip. Que el nombre del programa sea el que se ejecuta. Que la descripción nombre las tres herramientas.
- **B5-06 — Algunos pasos siguientes no llevan a ningún lado o no corresponden al archivo**
  - *Impacto:* 'Revisa los formatos compatibles en la ayuda', pero la ayuda de la terminal no lista formatos. Una página web o una presentación sin texto reciben el consejo de OCR para 'páginas escaneadas'. 'Quítale la contraseña' no dice cómo.
  - *Evidencia:* `clearmd in --lang es`: 'formato no soportado por ClearMD. Revisa los formatos compatibles en la ayuda.' (es.toml:103); `clearmd --help` no tiene lista de formatos (la lista está solo en la Ayuda de las ventanas). error.empty_result.action con OCR (es.toml:60) usado para .html y .pptx. error.password_protected.action sin instrucciones.
  - *Recomendación:* Lista de formatos en el epílogo de --help o dentro del mensaje. Consejo de OCR solo para PDF e imágenes. Instrucciones concretas para quitar la contraseña.
- **B5-07 — Las notas de versión le hablan al público del proceso interno y mezclan los idiomas en cada viñeta**
  - *Impacto:* En la página de descarga, quien lee 'las mejoras de la cuarta auditoría', 'ADR-0050' o 'Trusted Publishing' puede entender que el producto tuvo problemas graves, o simplemente no entender. Las viñetas inglés/español pegadas duplican la lectura justo antes de descargar.
  - *Evidencia:* packaging/RELEASE_NOTES.md: '**New in 2.13.0 / Novedades de la 2.13.0** — the fourth audit's improvements / las mejoras de la cuarta auditoría' (y lo mismo en 2.9.0–2.12.0); 2.7.0 menciona 'PyPI' y 'ADR-0050'. F4-02 midió 906 palabras en el cuerpo de v2.12.0.
  - *Recomendación:* Encabezar cada versión con lo que gana la persona, sin 'auditoría' ni ADR. Un bloque por idioma. Junto con F4-02: la tabla 'Qué Descargar' arriba y las novedades plegadas.
- **B5-10 — El resumen en español mezcla inglés y deja ver etiquetas HTML**
  - *Impacto:* Un resumen en español muestra 'BadZipFile: File is not a zip file' sin explicar que es un detalle técnico, y el historial trae líneas en inglés de una ejecución anterior. Quien lo abre en el Bloc de notas ve `<details><summary>` y `<!-- clearmd:history -->`, que parecen código.
  - *Evidencia:* /tmp/audit-b5/one/ClearMD_Output/Resumen_ClearMD.md (contenedor): historial en dos idiomas. '<details><summary>Detalle Técnico</summary>PDFium could not open it (error 4)</details>'. schemas/settings.py:20 summary_format='markdown'. ADR-0031:29 eligió `<details>`.
  - *Recomendación:* Guardar el historial como datos y escribirlo en el idioma del resumen actual. Una frase en español antes de cada detalle en inglés ('detalle para quien te ayude'). Decidir de forma consciente qué ve quien abre el .md en el Bloc de notas, sin revertir ADR-0031 salvo que el dueño lo decida.
- **B5-08 — Las páginas de política (seguridad, firma) y los formularios no acompañan a quien lee en español, tienen ejemplos viejos y hablan de una firma que no existe**
  - *Impacto:* El README en español manda a 'cómo comprobar una descarga' y el enlace lleva a una página solo en inglés, con un ejemplo de la versión 1.2.0. CODE_SIGNING.md habla en presente ('What is signed') de una firma que aún no existe, mientras el README dice que no está firmado. El formulario de ideas está solo en inglés.
  - *Evidencia:* SECURITY.md solo en inglés, `Get-FileHash .\ClearMD-Setup-1.2.0.exe`. README.es.md enlaza a './SECURITY.md#checking-a-download'. CODE_SIGNING.md:1-12 en presente. feature_request.yml y config.yml solo en inglés. bug_report.yml con el ejemplo '1.2.0'.
  - *Recomendación:* Una sección en español, paso a paso, para comprobar la descarga, con un nombre genérico. Una línea de 'Estado' al comienzo de CODE_SIGNING.md y las secciones en futuro hasta que SignPath esté activo. Formularios bilingües con el ejemplo '2.x.y'.

</details>

### Frontend · Lógica y estados — 7/10

Después de leer los informes de mis colegas, mantengo lo central: el presentador es sólido. Hay un solo presentador para las tres ventanas, los estados son explícitos, el trabajo en segundo plano está protegido por "generaciones" y nunca encontré un estado sin salida. Los fallos están en los caminos de ida y vuelta y en lo que cada estado le dice a la persona. Dos hallazgos de colegas que comprobé en el código entran en mi lente y los incorporo. (1) Resultados nunca mira las notas de conversión: un documento "convertido con notas" cuenta como éxito limpio, el estado queda "Terminado" y la carpeta se abre sola, mientras el resumen escrito dice "Necesita Tu Atención" (aporte de F5-01). (2) La línea sobre el título añade el estado del lote en cualquier página, y en flet además la pinta de naranja (aporte de F3-03). También confirmé que guardar ajustes escribe el objeto entero (F4-01). Ese mismo patrón está en la raíz de mi F1-01: lo temporal y lo no elegido acaban fijados en disco. Bajo la nota de 7,5 a 7, porque la pantalla final, la que más tranquilidad debería dar, puede decir lo contrario que el resumen.

**Fortalezas que vio:**

- Un solo presentador (ADR-0026) decide estados, textos, acción principal, cierre y pausa anti doble clic para las tres ventanas. La lógica no se reparte en tres copias.
- Cada trabajo en segundo plano lleva una 'generación': se descarta lo que devuelve tarde un análisis cancelado (background.py). Cancelar es inmediato y nunca cuelga la ventana.
- Cerrar durante una tarea pregunta una sola vez, con 'Seguir Trabajando' por defecto, y espera a que se escriba el resumen. Cancelar nunca pregunta, como decidió el dueño.
- La carpeta de resultados solo se abre sola cuando todo salió bien (conversion.py:166-169), así no tapa la lista de errores.
- Editar la lista o la salida descarta el plan viejo y lo dice cuando había resultado (ADR-0029).
- 'Vaciar Todo' se puede deshacer con el orden incluido. Unir avisa antes de empezar si queda un solo documento.
- Un error inesperado durante la conversión lleva a Resultados con las carpetas que pueden tener archivos, nunca a '0 convertidos'.
- Lo que solo informa ya va con un tono neutro y después de lo que pide algo (results.py:41). Es un primer paso correcto que hay que completar, no deshacer.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F1-01 | 🔴 Alta | medio | alta | "Dividir los PDF grandes" cambia en silencio las opciones guardadas de Dividir, y deshace las que la persona eligió |
| F1-08 | 🔴 Alta | pequeño | alta | Resultados ignora las notas de conversión: un documento con problemas aparece como éxito limpio y la carpeta se abre sola |
| F1-02 | 🟠 Media | pequeño | alta | Al volver a Convertir, la lista se reemplaza aunque la persona haya pedido empezar vacía o haya armado otra lista |
| F1-09 | 🟠 Media | pequeño | alta | La línea sobre el título muestra el estado del lote en páginas donde no corresponde |
| F1-03 | 🟠 Media | pequeño | alta | Cambiar ciertos Ajustes desde Revisar o Convertir devuelve al paso 1 sin decir por qué |
| F1-04 | 🟠 Media | pequeño | alta | Un error durante el análisis dice "lo ya convertido se conserva" cuando todavía no se convirtió nada |
| F1-05 | ⚪ Baja | pequeño | media | La pregunta "¿Cerrar ClearMD? Hay una tarea en curso" sigue abierta cuando la tarea ya terminó |
| F1-06 | ⚪ Baja | pequeño | media | Agregar un archivo que ya está en la lista, o soltarlo durante una tarea, no hace nada y no dice nada |
| F1-07 | ⚪ Baja | pequeño | alta | Las tres ventanas no tienen los mismos atajos: Ctrl+0 (Inicio) falta en la App Moderna (Qt), y la Ayuda no lo menciona |

<details><summary>Detalle técnico y evidencia</summary>

- **F1-01 — "Dividir los PDF grandes" cambia en silencio las opciones guardadas de Dividir, y deshace las que la persona eligió**
  - *Impacto:* Después del atajo, si la persona cambia cualquier ajuste durante esa tarea, Dividir queda para siempre con el número de partes de aquella tarea y guardando solo el Markdown: deja de conservar los PDF y nadie se lo dice. Pasa también lo contrario: lo que la persona eligió a propósito durante esa tarea se pierde al volver a Convertir.
  - *Evidencia:* tools.py:76-80 escribe los valores temporales en s.settings (split_parts=N, split_keep='markdown'). preferences.save_settings, choose_summary_format, inputs.choose_output_folder y Ajustes guardan s.settings completo, y serialize_settings (backend/use_cases/settings.py:54-70) escribe todos los campos. tools._give_back (89-97) restaura solo en memoria. Lo ejecuté con FakeBackend (/tmp/audit-logic/h1.py, h2.py). Disco antes: 2/both. Después de split_large y choose_summary_format: 4/markdown. Caso inverso: choose_split(7, 'both') y luego volver a Convertir y guardar: 2/both. Las pruebas test_039:51 y test_025:82 solo verifican el momento del atajo.
  - *Recomendación:* Guardar las opciones 'solo para esta tarea' en una capa temporal aparte, que se aplique al armar el plan y nunca se escriba en disco. Al volver a Convertir, respetar lo que la persona eligió a propósito. Agregar una prueba por cada vía de guardado dentro de una tarea iniciada con el atajo. Se arregla junto con F4-01 (guardar solo lo que la persona eligió).
- **F1-08 — Resultados ignora las notas de conversión: un documento con problemas aparece como éxito limpio y la carpeta se abre sola**
  - *Impacto:* Un PDF con páginas sin texto o una página web convertida entera aparece en la ventana como 'Todos los archivos se convirtieron', el estado es 'Terminado' y la carpeta se abre como si todo estuviera perfecto. El resumen escrito al lado dice 'Necesita Tu Atención'. La persona le pasa a su IA un texto incompleto sin enterarse.
  - *Evidencia:* Comprobado de nuevo: presenter/screens/results.py:33-34 hace 'continue' con lo convertido sin mirar outcome.notes. intents/conversion.py:146-163 calcula FINISHED_WITH_PROBLEMS solo con FAILED, STOPPED o unwritten_summaries. backend/schemas/models.py:153 ya tiene la propiedad que separa las notas que solo informan de las que piden revisar (any(not note.kind.informs ...)), pero el frontend no la usa: grep de 'notes' en frontend/presenter no da resultados. Hallazgo original de F5-01; lo verifiqué en el código.
  - *Recomendación:* Usar la propiedad que ya existe en el backend. Si un documento tiene una nota que pide revisar, se muestra como fila 'Convertido, pero:' con tono de aviso, el estado pasa a 'Terminado con problemas' y la carpeta no se abre sola. Hacer una prueba de presentador con un PDF de dos páginas, una de ellas imagen, y comprobar que no aparece la tarjeta 'todo bien'.
- **F1-02 — Al volver a Convertir, la lista se reemplaza aunque la persona haya pedido empezar vacía o haya armado otra lista**
  - *Impacto:* Ocurre después de 'Dividir los PDF grandes'. Si la persona desmarca 'Conservar los archivos que elegiste' y elige Convertir, reaparecen los archivos de antes. Si armó una lista en Unir y luego va a Convertir, pierde esa lista, y el aviso parece una buena noticia.
  - *Evidencia:* navigation.continue_with: convert_more(keep=False) vacía la lista y choose_tool(CONVERT) llama a _give_back, que hace s.inputs = list(s.back_to_convert) (tools.py:89). back_to_convert solo se borra en _give_back y sobrevive a un desvío por Unir. Lo ejecuté (/tmp/audit-logic/h1.py, h2.py).
  - *Recomendación:* Devolver la lista solo si la persona vuelve directamente desde la tarea de Dividir que abrió el atajo, y sumarla a lo que haya en vez de reemplazarlo. Olvidar back_to_convert al cambiar de herramienta o al desmarcar 'Conservar'.
- **F1-09 — La línea sobre el título muestra el estado del lote en páginas donde no corresponde**
  - *Impacto:* Tras un lote con errores, al volver al paso 1 la persona lee 'PASO 1 DE 4 · TERMINADO CON PROBLEMAS' (en flet, además en naranja) mientras elige archivos nuevos. No sabe si algo sigue mal ni si tiene que decidir algo en esa pantalla.
  - *Evidencia:* Comprobado de nuevo: presenter/chrome/header.py:27-28 añade state.label siempre que el estado no sea READY, sin comparar la página con la del estado. flet/window/view.py:172 pinta warning=True con FINISHED_WITH_PROBLEMS en cualquier página. Capturas 016/1-choose-compact-dark-es.png y 018/1-choose-compact-light-es.png. Hallazgo original de F3-03.
  - *Recomendación:* Añadir el estado solo cuando la página es la del estado (análisis y decisión en Revisar, trabajo en Convertir, final en Resultados), y lo mismo para el color de aviso. Agregar una prueba en header_of por cada pareja de estado y página.
- **F1-03 — Cambiar ciertos Ajustes desde Revisar o Convertir devuelve al paso 1 sin decir por qué**
  - *Impacto:* Al guardar Ajustes con 'Incluir Subcarpetas' o 'Páginas Web' cambiados, o al pulsar 'Restaurar valores', la ventana salta al paso 1 sin ningún mensaje. La persona puede creer que algo falló.
  - *Evidencia:* preferences.save_settings llama a editable() cuando cambian recursive o html_strategy (66-69). reset.editable pone page=1, pero el aviso solo aparece 'if had_result' (reset.py:31). Lo ejecuté (/tmp/audit-logic/h3.py): de waiting_decision en página 2 pasa a ready en página 1, sin mensajes.
  - *Recomendación:* Dar un aviso corto también cuando se descarta un plan, o rehacer el análisis y quedarse en Revisar.
- **F1-04 — Un error durante el análisis dice "lo ya convertido se conserva" cuando todavía no se convirtió nada**
  - *Impacto:* Si algo falla mientras se revisan los archivos, el mensaje promete resultados que no existen. La persona puede buscarlos o creer que la conversión ya empezó.
  - *Evidencia:* reset.unexpected usa siempre gui.app.unexpected_error (en.toml:514), en ANALYZING y en CONVERTING. Lo ejecuté: FakeBackend(plan_error=RuntimeError) da ese mensaje.
  - *Recomendación:* Usar un texto por fase ('No se escribió nada todavía; tus documentos no cambiaron') y una prueba por fase.
- **F1-05 — La pregunta "¿Cerrar ClearMD? Hay una tarea en curso" sigue abierta cuando la tarea ya terminó**
  - *Impacto:* Si la tarea termina mientras la persona lee la pregunta, el diálogo sigue diciendo que hay una tarea en curso, aunque detrás ya se ven los Resultados.
  - *Evidencia:* dialog_host.confirm_close (ttk:100, Qt:85, flet:41) abre el diálogo, pero ningún cambio de estado lo cierra. conversion._converted puede abrir la carpeta porque shutting_down sigue en falso hasta que la persona confirma. Lo revisé leyendo el código.
  - *Recomendación:* Cuando el estado sale de CONVERTING, cerrar la pregunta o cambiar su texto, y no abrir la carpeta mientras esté abierta.
- **F1-06 — Agregar un archivo que ya está en la lista, o soltarlo durante una tarea, no hace nada y no dice nada**
  - *Impacto:* La persona arrastra un archivo y no ve ninguna respuesta. Puede creer que la aplicación no funciona.
  - *Evidencia:* inputs.add_paths: 'if not new or not editable(...): return' (inputs.py:34), sin mensaje. ttk window/inputs.dropped (50-53) descarta en silencio. No hay clave de catálogo para 'ya está en la lista'.
  - *Recomendación:* Dar un aviso corto ('Ya estaba en la lista: …' o 'Espera a que termine la tarea') y, en ttk, rechazar visualmente que se suelte el archivo, como ya hace Qt.
- **F1-07 — Las tres ventanas no tienen los mismos atajos: Ctrl+0 (Inicio) falta en la App Moderna (Qt), y la Ayuda no lo menciona**
  - *Impacto:* Quien usa el teclado vuelve a Inicio con Ctrl+0 en la App Clásica y en flet, pero no en la App Moderna, que es justo la recomendada para lectores de pantalla. La Ayuda solo menciona Ctrl+1 a Ctrl+4.
  - *Evidencia:* pyside/window/inputs.py:33 range(1, len(STEPS)+1); ttk/window/inputs.py:44 range(5); flet keys.py STEP_KEYS desde HOME. en.toml:501. F2-09 lo amplía a las flechas y al tabulador.
  - *Recomendación:* Definir la tabla de atajos una sola vez en el presentador, generar a partir de ella la línea de la Ayuda y agregar Ctrl+0 en Qt. Una sola prueba compara la tabla con lo que registra cada ventana y con lo que dice la Ayuda.

</details>

### Frontend · Accesibilidad — 6/10

Después de leer los diez informes mantengo mi diagnóstico y lo ajusto en dos puntos. La base visual y de teclado es buena: la paleta pasa la norma, el color nunca va solo, los botones miden 44 px, el contrato de teclado está escrito y el producto es honesto sobre los lectores de pantalla. El hueco sigue en el mismo lugar. La App Moderna, que se recomienda a quien usa lector de pantalla, no le dice al lector dónde está ni cuándo termina la tarea, y la App Clásica no tiene ningún camino audible hacia ella. Los colegas me hicieron ver dos cosas. Primero, mi hallazgo sobre la ventana a 175–200 % es el mismo problema que F3-01 (la ventana de 720 px no se ajusta a la pantalla), y además F3-02 (Tk sin soporte de alta resolución) lo agrava: los fusiono, sin subir la severidad. Segundo, F1-07 confirma con el código que Ctrl+0 falta en Qt. Lo comprobé en pyside/window/inputs.py:33 y lo uno a mi F2-09. También incorporo, dentro de mi lente, que los íconos de formato a 16 px (F3-06) dejan solo el color para distinguir Word de OpenDocument, y que el resultado 'con notas' que no se ve en pantalla (F5-01) tampoco se anunciaría. Nota: 6/10, sin cambios.

**Fortalezas que vio:**

- Los 15 pares de colores de la paleta pasan WCAG AA (4,5:1) en los dos temas, y un test lo vigila (tests/unit/frontend/ttk/test_brand.py).
- El color nunca va solo: cada fila con problema empieza con una palabra («Con error:», «Omitido:»). Otros cinco auditores lo destacan también.
- Botones de 44 px y texto de al menos 14 px, como medidas comunes a las tres ventanas (metrics.py, typography.py).
- El contrato de teclado está escrito (ux.md §6), es coherente y lo implementan las tres ventanas: Enter pulsa donde está el foco, Esc cierra, Ctrl+1…4 lleva a cada paso.
- En Qt y flet los anillos de foco miden 2 px, contrastan bien y se distinguen del borde de «último usado».
- Honestidad: el instalador, el README y la Ayuda dicen qué ventana usar con lector de pantalla, sin prometer de más.
- Las tarjetas de Inicio en Qt tienen nombre y descripción accesibles, y en Ajustes cada etiqueta está asociada a su control (setBuddy).

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F2-01 | 🔴 Alta | medio | alta | La App Moderna, la recomendada para lectores de pantalla, no da al lector lo que necesita |
| F2-02 | 🔴 Alta | pequeño | alta | Quien usa lector de pantalla con la App Clásica no tiene dentro de la app ningún camino audible hacia la Moderna |
| F2-07 | 🟠 Media | medio | media | Con escala del 150–200 % la ventana no cabe en la pantalla y el botón principal queda escondido (fusionado con F3-01 y F3-02) |
| F2-03 | 🟠 Media | pequeño | alta | En la App Clásica casi no se ve qué fila de la lista tiene el foco del teclado |
| F2-04 | 🟠 Media | pequeño | alta | En la App Moderna hay una parada del tabulador invisible en cada página con desplazamiento |
| F2-05 | 🟠 Media | pequeño | alta | El texto atenuado queda en 3,6:1 en tema claro, por debajo del 4,5:1 del contrato UX (incluye la línea del paso en naranja de F3-03) |
| F2-06 | 🟠 Media | pequeño | alta | Los bordes de los campos, las listas y la barra de desplazamiento casi no se ven (1,2–1,3:1) |
| F2-08 | 🟠 Media | medio | media | En la App Estilo Móvil las flechas dejan de recorrer la lista en cuanto se usa el tabulador, y hay controles sin nombre |
| F2-09 | ⚪ Baja | pequeño | alta | Los atajos de teclado no son iguales en las tres ventanas y la Ayuda no los dice todos: Ctrl+0 falta en Qt (fusionado con F1-07) |
| F2-10 | ⚪ Baja | pequeño | alta | Los íconos de formato en Qt y flet distinguen Word de OpenDocument solo por el color (aportado por F3-06) |

<details><summary>Detalle técnico y evidencia</summary>

- **F2-01 — La App Moderna, la recomendada para lectores de pantalla, no da al lector lo que necesita**
  - *Impacto:* Una persona ciega elige la App Moderna, como le aconseja el instalador. Al cambiar de página el lector no dice nada útil, porque el foco cae en un panel sin nombre. Al terminar la conversión no oye «Terminado» ni «Terminado con problemas». La lista de archivos se llama «inputs», en inglés, también en español. Las casillas de número de Dividir solo dicen un número, y las opciones redondas no dicen a qué pregunta responden.
  - *Evidencia:* pyside/window/view.py:87-90 rest_focus() pone el foco en self._panel (un QFrame sin accessibleName). pyside/components/inputs_card.py:51 setAccessibleName("inputs"), un literal sin traducir. Las listas de Revisar y Resultados no tienen nombre. split_choice.py:39-50: QSpinBox sin nombre ni buddy. Los QButtonGroup no tienen nombre de grupo. grep de QAccessible/announce en frontend: 0 resultados, aunque PySide6 6.12 trae QAccessibleAnnouncementEvent. Sonda offscreen: 13 controles enfocables sin accessibleName en Elegir.
  - *Recomendación:* 1) Al cambiar de página, poner el foco en el título o dar al panel el nombre «Paso N de 4 · título». 2) Anunciar el fin de la tarea con QAccessibleAnnouncementEvent, usando el mismo titular que vea la pantalla (ver F5-01: si hay notas, «Terminado con avisos»). 3) Sacar los nombres de las listas del catálogo y nombrar las de Revisar y Resultados. 4) Nombrar cada casilla de número y cada grupo de opciones. 5) Probar una vez con NVDA o Narrador el recorrido de Elegir a Resultados antes de volver a decir que es «la que mejor funciona».
- **F2-02 — Quien usa lector de pantalla con la App Clásica no tiene dentro de la app ningún camino audible hacia la Moderna**
  - *Impacto:* La App Clásica es la que se instala por defecto y la del ejecutable portable, y un lector de pantalla no puede leerla. El único aviso que hay dentro está en su propia Ayuda, que la persona no puede oír. Quien usa el portable nunca ve el texto del instalador.
  - *Evidencia:* i18n/en.toml:501 y es.toml:502: el aviso está en la Ayuda de la ventana Tk. ADR-0026:56: «Tk exposes none to screen readers». clearmd.iss:97-98: el aviso del instalador solo sale en su página final y no llega al portable.
  - *Recomendación:* Mantener la edición por defecto. En Windows, al abrir la App Clásica, consultar SPI_GETSCREENREADER. Si hay un lector activo, mostrar una sola vez un cuadro de mensaje nativo de Windows, que el lector sí lee, con el nombre de la App Moderna y dónde descargarla.
- **F2-07 — Con escala del 150–200 % la ventana no cabe en la pantalla y el botón principal queda escondido (fusionado con F3-01 y F3-02)**
  - *Impacto:* Quien ve poco pone Windows al 175 % o 200 %, y muchos portátiles vienen al 150 % de fábrica. La ventana abre a 1080×720 sin medir la pantalla y su mínimo es 800×624. Así, «Siguiente» o «Convertir» quedan debajo de la barra de tareas. La App Clásica, además, probablemente se ve borrosa al escalar, y dentro de la app no hay forma de agrandar el texto.
  - *Evidencia:* Lo revisé otra vez: design/metrics.py:14-16 MIN 800×624 y START 1080×720. Ninguna ventana usa availableGeometry ni winfo_screenheight (también lo vio F3-01). No hay ninguna llamada a SetProcessDpiAwareness ni a tk scaling (F3-02). Aritmética: 1080/1,5=720, 1080/1,75≈617 y 1080/2=540, todo antes de restar la barra de tareas y el título. No lo ejecuté en Windows con escalado.
  - *Recomendación:* 1) Ajustar el tamaño inicial al área de trabajo del monitor (F3-01). 2) Bajar la altura mínima para que quepa en unos 960×500, con la barra de acciones siempre visible. 3) Declarar el soporte de alta resolución en Tk (F3-02). 4) Añadir a ux.md casos de aceptación con 1920×1080 al 200 % y 1366×768 al 125 %. 5) Valorar un ajuste de tamaño del texto, lo que obligaría a enmendar ADR-0012.
- **F2-03 — En la App Clásica casi no se ve qué fila de la lista tiene el foco del teclado**
  - *Impacto:* Quien recorre la lista con las flechas en la App Clásica apenas ve en qué fila está. Si la fila además está marcada, la marca de foco desaparece del todo. Es fácil quitar el archivo equivocado.
  - *Evidencia:* ttk/components/list_focus.py:12 _TINT=0.12: la fila con foco contrasta 1,18:1 con la tarjeta en tema claro y 1,28:1 en oscuro (WCAG pide 3:1). ttk/visuals/styles.py:143: el fondo de selección se impone al de la marca de foco.
  - *Recomendación:* Marcar la fila con foco con una barra o un borde de acento de 2 px, o con un tinte de al menos 3:1. Probar el caso de una fila con foco y marcada en tema claro.
- **F2-04 — En la App Moderna hay una parada del tabulador invisible en cada página con desplazamiento**
  - *Impacto:* Después de Ayuda, el tabulador cae en un sitio donde no se ve nada enfocado y el lector no dice nada. La persona cree que el teclado se perdió.
  - *Evidencia:* Sonda offscreen: «ScrollPage '' acc=''» está en el orden de tabulación. scroll_page.py:8 hereda de QScrollArea con StrongFocus. stylesheet.py:192 no tiene regla :focus.
  - *Recomendación:* Usar setFocusPolicy(NoFocus), o un anillo visible más un nombre. Añadir un test que recorra cada página con Tab y falle si algún control enfocable no tiene texto ni nombre.
- **F2-05 — El texto atenuado queda en 3,6:1 en tema claro, por debajo del 4,5:1 del contrato UX (incluye la línea del paso en naranja de F3-03)**
  - *Impacto:* Hay información que se lee mal en tema claro: dónde quedarán los resultados en la tarjeta atenuada, los nombres de las cifras en espera y la línea de estado en naranja sobre la forma de fondo.
  - *Evidencia:* DIM_TEXT=0.8: #7A848D sobre #F8FAFB da 3,64:1 (styles.py:35-36; igual en Qt y flet). F3-03 calcula 4,14:1 para el naranja sobre la forma; no lo volví a medir, pero test_brand.py no prueba los colores mezclados con blend() ni los que van sobre la forma, así que ningún test lo atraparía. ux.md:62 exige 4,5:1.
  - *Recomendación:* Usar muted (5,85:1) para el texto atenuado y atenuar solo el fondo. Ampliar el test de contraste a todo color derivado que se pinta como texto, también sobre la forma de fondo.
- **F2-06 — Los bordes de los campos, las listas y la barra de desplazamiento casi no se ven (1,2–1,3:1)**
  - *Impacto:* A una persona con vista cansada le cuesta ver dónde se escribe un número o que hay una barra para desplazarse.
  - *Evidencia:* border #DCE2E7 sobre #FFFFFF = 1,31:1, y #2E3B47 sobre #202B36 = 1,26:1. Se usa en QSpinBox/QComboBox y en el asa de QScrollBar (stylesheet.py:147-166), en TSpinbox (styles.py:147-151) y en NumberField de flet. Captura 018/1-choose-split-light-es.png. WCAG 1.4.11 pide 3:1.
  - *Recomendación:* Crear un token field_border de al menos 3:1 para campos y barras de desplazamiento, y dejar el borde pálido solo en lo decorativo.
- **F2-08 — En la App Estilo Móvil las flechas dejan de recorrer la lista en cuanto se usa el tabulador, y hay controles sin nombre**
  - *Impacto:* Después de un solo Tab, las flechas no hacen nada y no hay forma de devolver el foco a la lista. Las casillas de cada archivo y los campos de número no dicen qué son.
  - *Evidencia:* flet/window/keys.py:56-57 (las flechas solo actúan si ningún control tiene el foco). list_line.py:78-88: las filas son Container con on_click y no pueden recibir foco. list_line.py:73: Checkbox sin label. number_field.py:23-36: sin semantics_label. Lo vi en el código, sin ejecutar.
  - *Recomendación:* Que la lista pueda recibir el foco con Tab y que las flechas funcionen mientras lo tiene. Nombrar cada casilla con su archivo y cada campo con su unidad. Hacer un test que pulse Tab hasta un botón y luego las flechas.
- **F2-09 — Los atajos de teclado no son iguales en las tres ventanas y la Ayuda no los dice todos: Ctrl+0 falta en Qt (fusionado con F1-07)**
  - *Impacto:* Quien usa el teclado no sabe que Ctrl+0 vuelve al Inicio ni que las flechas recorren las listas. En la App Moderna, justo la recomendada a quien no usa el ratón, Ctrl+0 ni siquiera funciona.
  - *Evidencia:* Lo confirmé: pyside/window/inputs.py:33 recorre range(1, len(STEPS)+1), sin el 0. ttk/window/inputs.py:44 usa range(5) y flet keys.py arranca STEP_KEYS desde HOME. en.toml:501 solo nombra Ctrl+1…4.
  - *Recomendación:* Definir una tabla única de atajos en el presentador y que cada ventana la aplique. Agregar Ctrl+0 en Qt, ampliar la línea de teclado de la Ayuda (Ctrl+0, Tab, flechas) y añadir un test que compare los atajos registrados con los que nombra la Ayuda.
- **F2-10 — Los íconos de formato en Qt y flet distinguen Word de OpenDocument solo por el color (aportado por F3-06)**
  - *Impacto:* A 16 px la inicial del ícono no se lee. Quien no distingue bien el azul del índigo, o ve poco, no sabe qué formato tiene cada fila sin leer la extensión. Es información que queda solo en el color.
  - *Evidencia:* Lo comprobé: pyside/layout/units.py:6 y flet/layout/units.py:9 tienen ICON = 16, mientras que los recursos están dibujados a 28 y 56 px. En ttk el ícono se ve a 24 px. Capturas 018/1-choose-light-es.png frente a 007/1-choose-light-es.png. Mitigación parcial: la fila también muestra el nombre del archivo con su extensión, por eso la severidad es baja.
  - *Recomendación:* Hacer el tamaño del ícono un token compartido de 24 px y comprobar que, a ese tamaño, la letra distingue cada par de colores parecidos.

</details>

### Frontend · Estilo visual UI/UX — 7/10

Después del debate mantengo la nota (7/10) y los diez hallazgos. Ninguno se retira y no subo ninguna severidad. Los colegas confirman, con otros caminos, tres de mis puntos. F2-07 llega al mismo borde que F3-01: la ventana no se adapta a la pantalla real y el botón principal puede quedar fuera de la vista. F5-05 coincide con F3-05: las rutas se cortan por el lado equivocado. F4-09 y F5-06 coinciden con F3-04: el paso 1 está sobrecargado. Volví a revisar en el código y en los números: la paleta tiene bordes de 1,2–1,31:1 (F2-06); el naranja de aviso queda a 4,14:1 sobre la forma de fondo (F3-03); en `header_of` el estado se añade en cualquier página; Resultados salta los convertidos sin mirar sus notas (F5-01); en Qt y flet los íconos miden 16 px; y no hay ninguna declaración de alta resolución en el frontend. En lo visual, el fondo sigue igual. La identidad compartida es fuerte, pero se pierde en el borde de la pantalla real: escala de Windows, rutas largas, listas que se desbordan y pequeñas diferencias entre las tres ventanas. Lo más importante para el público: que el botón principal se vea siempre y que la ventana sea nítida a la escala de fábrica. Una advertencia del debate: varias propuestas de otros (explicar cada opción en el paso 1, más avisos, más líneas de ayuda) suman texto en la pantalla que ya está más cargada. La solución visual es resumir, no agregar.

**Fortalezas que vio:**

- Una sola identidad visual compartida de verdad: la paleta, las medidas y la cuadrícula de 8 px salen de frontend/design (metrics.py, palette.py, colors.py), y las tres ventanas la respetan. Esta base no debe perderse.
- El riel con los cuatro pasos numerados y el paso actual resaltado dice dónde está la persona sin que tenga que leer nada, en tema claro y en oscuro.
- Las tarjetas de cifras de Revisar y Resultados dan la respuesta antes del detalle, con colores que significan algo y siempre acompañados de una palabra («Con error:», «Omitido:»).
- La paleta pasa AA en los textos principales (el gris atenuado sobre la tarjeta da 5,85:1 en claro y 6,37:1 en oscuro, recalculado), y un test la vigila.
- La pantalla de Inicio, con tres tarjetas grandes (Convertir / Dividir / Unir), es clara para quien nunca usó la app.
- El estado vacío de flet (dos tarjetas grandes de Agregar con su explicación) es la mejor versión del paso 1 y debería ser la referencia para las otras dos ventanas.
- Hay un solo botón principal por pantalla y los secundarios se ven secundarios (UX §5).
- Cada versión trae capturas de cada pantalla en los dos temas, los dos idiomas y dos tamaños. Eso permite auditar sin instalar y debe mantenerse.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F3-01 | 🔴 Alta | pequeño | media | La ventana puede abrir más alta que la pantalla y esconder el botón principal |
| F3-02 | 🔴 Alta | medio | media | La edición clásica (ttk), la recomendada, probablemente se ve borrosa en pantallas con escala |
| F3-03 | 🟠 Media | pequeño | alta | La línea sobre el título mezcla el paso con el estado del lote anterior, y su naranja no llega a AA sobre la forma de fondo |
| F3-04 | 🟠 Media | medio | alta | En el paso 1 las opciones le quitan espacio a la lista y se agrupan de forma confusa |
| F3-05 | 🟠 Media | medio | alta | Las rutas de carpeta se cortan por el lado equivocado o desaparecen |
| F3-06 | 🟠 Media | pequeño | alta | Los íconos de formato son tan pequeños en Qt y flet que su letra no se lee |
| F3-07 | 🟠 Media | pequeño | media | En flet no se ve la barra de desplazamiento: las listas y Ajustes parecen terminar donde no terminan |
| F3-08 | 🟠 Media | medio | alta | La misma pantalla se ve distinta en cada ventana |
| F3-09 | ⚪ Baja | pequeño | alta | El riel trata Ajustes y Ayuda distinto al resto y en modo compacto quedan diminutos |
| F3-10 | ⚪ Baja | pequeño | alta | El mensaje de privacidad se repite hasta cuatro veces por pantalla y ocupa la línea de explicación |

<details><summary>Detalle técnico y evidencia</summary>

- **F3-01 — La ventana puede abrir más alta que la pantalla y esconder el botón principal**
  - *Impacto:* En un portátil Full HD con Windows al 150 % de escala (la configuración de fábrica de muchos equipos de 14-15") quedan unos 1280×672 puntos útiles. La ventana abre con 720 de alto más la barra de título, así que lo de abajo queda debajo de la barra de tareas, y ahí están Siguiente, Convertir y Abrir Carpeta de Resultados. Con escala del 175–200 % (F2-07) ni siquiera cabe el tamaño mínimo de 800×624. La persona no ve cómo avanzar y no sabe que tiene que mover o maximizar la ventana.
  - *Evidencia:* design/metrics.py:15-17 MIN_WIDTH=800, MIN_HEIGHT=624, START_WIDTH, START_HEIGHT=1080, 720 (revisado de nuevo en la ronda 2). ttk/window/toolkit.py:42 root.geometry(START_SIZE), pyside/window/qt_window.py:27 resize(START_*), flet/window/flet_page.py:27 START_*+FRAME_*. Ninguna ventana consulta availableGeometry ni winfo_screenheight. Cálculo: 720 + ~31 > 672. F2-07 llega por otro camino a la misma aritmética para 1080/1,75 y 1080/2. No se probó en Windows real.
  - *Recomendación:* Al abrir, medir el área de trabajo del monitor (sin la barra de tareas), usar el mínimo entre 1080×720 y ese espacio menos un margen, y centrar la ventana. Si no cabe ni el mínimo, abrir maximizada y bajar MIN_HEIGHT, como propone F2-07: el contenido ya se desplaza (feature 032). La barra de acciones debe quedar siempre visible, fija abajo y fuera del área que se desplaza. Agregar capturas que simulen 1280×672 y 960×500.
- **F3-02 — La edición clásica (ttk), la recomendada, probablemente se ve borrosa en pantallas con escala**
  - *Impacto:* En Windows al 125 % o al 150 %, un programa Tk que no se declara compatible con alta resolución lo agranda Windows como si fuera una imagen: las letras y los bordes redondeados se ven borrosos. Es la edición que el instalador marca como RECOMENDADA, así que es la primera impresión de la mayoría. El instalador dice que la App Moderna es «más nítida», pero no explica por qué.
  - *Evidencia:* En la ronda 2 repetí `grep -ri 'SetProcessDpi\|dpi\|scaling'` en src/clearmd/frontend y en packaging/clearmd.spec, sin resultados. spec/features/005_presenter-and-ttk-gui/spec.md:104-105 deja abierta la pregunta sobre alta resolución en Windows. packaging/installer/clearmd.iss:144 («más nítida en pantallas de alta resolución»). Captura docs/screenshots/019/06-parts-spanish.png (ttk RECOMENDADA). F2-07 lo cita como indicio. No se verificó en Windows: depende del manifiesto que genere PyInstaller.
  - *Recomendación:* Al iniciar ttk en Windows, declarar el proceso compatible con alta resolución por monitor antes de crear Tk, y ajustar 'tk scaling' a los puntos por pulgada reales. Tomar capturas al 100 %, 125 % y 150 % en el CI de Windows y cerrar la pregunta abierta de la spec 005. Se mantiene ttk como edición por defecto (decisión del dueño).
- **F3-03 — La línea sobre el título mezcla el paso con el estado del lote anterior, y su naranja no llega a AA sobre la forma de fondo**
  - *Impacto:* Después de un lote con errores, al volver al paso 1 para elegir archivos nuevos, arriba se lee en naranja «PASO 1 DE 4 · TERMINADO CON PROBLEMAS». Al volver de Revisar se lee «ESPERANDO TU DECISIÓN». Es el texto más visible de la página y dice algo que no corresponde a esa página. Además, donde cae sobre la forma decorativa se lee peor.
  - *Evidencia:* presenter/chrome/header.py:27-28 (releído en la ronda 2): `if state.state is not AppState.READY: eyebrow = f"{eyebrow} · {state.label}"`, sin comparar la página con el paso del estado. flet/window/view.py:172 aplica el color de aviso sin mirar la página. Capturas 016/1-choose-compact-dark-es.png y 018/1-choose-compact-light-es.png. Recalculado con la paleta real: warning sobre shape = 4,14:1 en claro (por debajo de 4,5:1) y 4,59:1 sobre ground.
  - *Recomendación:* Mostrar el estado junto al paso solo cuando la página es la del estado; en las demás, solo «PASO n DE 4». Si conviene recordar el lote anterior, poner un punto de color en el paso 4 del riel. Recortar la forma de fondo para que nunca quede debajo de la línea superior.
- **F3-04 — En el paso 1 las opciones le quitan espacio a la lista y se agrupan de forma confusa**
  - *Impacto:* La lista de archivos es lo principal del paso 1, pero a 1080×720 se ven 2-4 filas (en Dividir, una). En Dividir y Unir, «Los Resultados Van» queda en la misma línea que las opciones del resumen, y parece que «Markdown / Markdown + PDF / Solo PDF» es el destino. A 800 px las opciones quedan recortadas dentro de una tarjeta con su propia barra de desplazamiento. F4-09 y F5-06 describen la misma carga desde el primer uso y la claridad de los textos.
  - *Evidencia:* Capturas 018/1-choose-split-dark-es.png, 018/1-choose-merge-light-es.png, 007/1-choose-split-800-dark-es.png, 016/1-choose-split-800-light-es.png y 016/1-choose-split-light-es.png. flet/components/output_card.py:45-73 (fila _beside). El formato del resumen también está en Ajustes (es.toml:459).
  - *Recomendación:* Cada etiqueta encima o a la izquierda de sus propias opciones, nunca junto a las de otro grupo. Dejar visible lo que cambia esta tarea y resumir Imágenes y Resumen en una línea («Resumen: Markdown · Imágenes: no — Cambiar») que despliegue el detalle con su explicación de una línea. Así se cumple F5-06 sin sumar texto a la vista inicial. Garantizar al menos 4 filas visibles en la lista y evitar una barra de desplazamiento dentro de otra.
- **F3-05 — Las rutas de carpeta se cortan por el lado equivocado o desaparecen**
  - *Impacto:* En el paso 1, la columna Carpeta corta por el final y se pierde justo el nombre de la carpeta, que es lo único que la persona reconoce. En Revisar se muestra solo la última carpeta, así que la misma fila se ve distinta de un paso a otro. En Resultados, en ttk, las rutas largas esconden líneas y la persona puede no ver dónde quedó parte de su trabajo. F5-05 confirma el primer caso.
  - *Evidencia:* flet/components/list_line.py:64 (max_lines=1, ELLIPSIS al final; la ruta completa solo en el tooltip, contra UX §4). presenter/screens/choose.py:56-60 (str(path.parent)) frente a review.py:57 (folder_name()). Capturas 018/1-choose-light-es.png. ttk/components/where_text.py:30 calcula el alto por saltos de línea. Ejecutado con xvfb en el contenedor (/tmp/audit-f3/t.py): con 3 rutas sintéticas tipo OneDrive, el cuadro mide 4 líneas pero necesita 7 líneas visuales y la tercera carpeta queda oculta. flet/views/results.py:43-48 crece sin límite.
  - *Recomendación:* Usar en las tres ventanas una sola utilidad de presentación de rutas en el presentador: corte por la izquierda o por el medio («…\Documentos\Tesis»), igual en Elegir y en Revisar, con la ruta completa en la línea de detalle al seleccionar la fila. En Resultados, una fila por carpeta; si son más de 3, «y N carpetas más» dentro de un área con desplazamiento. En ttk, medir con count displaylines.
- **F3-06 — Los íconos de formato son tan pequeños en Qt y flet que su letra no se lee**
  - *Impacto:* ADR-0027 identifica cada formato por su color y su inicial. A 16 px la inicial no se lee y solo queda el color: Word (azul) y OpenDocument (índigo) casi no se distinguen, menos aún para quien tiene dificultad con los colores. En ttk el mismo ícono va a 24 px y sí se lee.
  - *Evidencia:* Releído en la ronda 2: pyside/layout/units.py:6 ICON = 16 y flet/layout/units.py:9 ICON = 16. Los recursos están dibujados a 28 y 56 px (assets/icons/pdf.png, pdf@2x.png). Capturas 016/2-review-split-offer-dark-es.png y 018/1-choose-light-es.png frente a 007/1-choose-light-es.png.
  - *Recomendación:* Subir el ícono de fila a 24 px en Qt y flet y declararlo como token compartido en design/metrics.py. Revisar que los pares de colores parecidos se distingan también por la letra.
- **F3-07 — En flet no se ve la barra de desplazamiento: las listas y Ajustes parecen terminar donde no terminan**
  - *Impacto:* En flet, la lista de Resultados muestra dos filas y media, y en Ajustes la descripción de Imágenes queda cortada, sin ninguna barra que indique que hay más abajo. Alguien no técnico puede creer que las opciones de Dividir y Unir no existen.
  - *Evidencia:* Recomprobado en la ronda 2: flet/components/dialog.py:33 y views/dialogs/help.py:33 usan ft.ScrollMode.AUTO. Capturas 018/6-settings-light-es.png, 018/4-results-light-es.png y 018/1-choose-light-es.png, frente a las de Qt (016/6-settings-1366x768-dark-es.png) y ttk (007/6-settings-light-es.png), donde la barra sí se ve.
  - *Recomendación:* Usar en flet el modo de desplazamiento siempre visible en las listas y los diálogos que pueden desbordarse, o un degradado o la línea «más abajo ↓» al pie. Revisar en la matriz de capturas que toda lista desbordada muestre su barra, y que esa barra tenga un contraste de al menos 3:1 (ver F2-06).
- **F3-08 — La misma pantalla se ve distinta en cada ventana**
  - *Impacto:* Quien lee la Ayuda o una captura de una edición y abre otra encuentra diferencias que hacen dudar. En Inicio, ttk y Qt ponen una tarjeta dentro de otra. En el paso 1 vacío, flet muestra tarjetas grandes y ttk y Qt botones pequeños con «Deseleccionar Todo» activo. Los títulos de diálogo tienen tamaños distintos. En Qt las tres opciones de «ya existe» quedan repartidas 2+1. F1-07 (Ctrl+0 falta en Qt) es la misma deriva, del lado del teclado.
  - *Evidencia:* 007/0-home-light-es.png y 016/0-home-light-es.png frente a 018/0-home-light-es.png. 018/1-choose-empty-light-es.png frente a 016/1-choose-empty-light-es.png. presenter/state.py:41-56 (no existe una acción DESELECT que se deshabilite). ttk/components/inputs_card.py:70 (raya solo en ttk). 018/6-settings-light-es.png frente a 007/6-settings-light-es.png. 016/2-review-split-offer-dark-es.png.
  - *Recomendación:* Tomar el estado vacío de flet como referencia. Quitar la tarjeta interna de Inicio. Deshabilitar «Deseleccionar Todo» cuando no haya nada marcado. Fijar en design/typography.py un tamaño común para los títulos de diálogo. Generar en el script de capturas una hoja comparativa ttk \| Qt \| flet por pantalla.
- **F3-09 — El riel trata Ajustes y Ayuda distinto al resto y en modo compacto quedan diminutos**
  - *Impacto:* En el riel ancho, Ajustes y Ayuda tienen un hueco vacío donde los pasos tienen su círculo, y se ven más brillantes que los pasos inactivos. En el riel compacto son «⚙» y «?» de unos 12 px junto a círculos de 24 px, y su nombre solo aparece al pasar el mouse.
  - *Evidencia:* flet/components/rail.py:150-156. Capturas 018/1-choose-light-es.png, 018/1-choose-compact-light-es.png y 016/1-choose-compact-dark-es.png.
  - *Recomendación:* Dibujar íconos propios de engranaje y de ayuda con la geometría de los círculos de los pasos (como tool_art), usarlos en los dos modos y dejar el texto en el gris de los pasos inactivos.
- **F3-10 — El mensaje de privacidad se repite hasta cuatro veces por pantalla y ocupa la línea de explicación**
  - *Impacto:* En Inicio y en cada paso 1, la promesa «en tu computador / nada sale de tu equipo» se repite y le quita al subtítulo su función de decir qué hacer. Además alterna «computador» y «equipo» (F5-09 confirma esta mezcla), y en el pie del riel en español «equipo» queda sola en una línea.
  - *Evidencia:* src/clearmd/i18n/es.toml:514, :570, :629, :662 y :709. Capturas 018/0-home-light-es.png y 018/1-choose-split-dark-es.png.
  - *Recomendación:* Dejar la promesa en un solo lugar fijo (el pie del riel, con un candado) y usar los subtítulos para decir qué hacer en ese paso. Usar «computador» en todo el catálogo en español.

</details>

### Frontend · Primer uso, instalación e idioma — 6,5/10

Tras el debate, mantengo el diagnóstico. Una vez dentro, la app recibe bien a quien la abre por primera vez. Los tropiezos están antes de abrirla (descarga e instalación) y al volver (ajustes y actualizaciones). Volví a comprobar en el código el hallazgo más grave: serialize_settings escribe todos los campos. En la 2.11 el valor por defecto era html_strategy="full", así que quien solo cerró la Bienvenida en esa versión quedó fijo en "página completa" sin haberlo elegido. Y no hay número de versión ni migración en el archivo de ajustes. Los colegas confirman y amplían varios puntos de mi lente. El README contradice el valor por defecto de las páginas web (B5-04, confirmado en README.md:222). Las notas de versión mezclan los idiomas y hablan de "auditorías" (B5-07). El atajo de línea de comandos del instalador enseña a escribir clearmd-cli, pero la ayuda dice "usage: clearmd" (B5-05, confirmado). La ventana flet instalada con pip descarga un componente al primer uso (B2-04, confirmado). La ventana abre a 1080×720 sin medir la pantalla (F3-01, confirmado). La App Clásica no avisa por un canal audible a quien usa lector de pantalla (F2-02, confirmado). Uno mi F4-09 a F3-04 y F5-06, que lo tratan mejor. Agrego un hallazgo menor sobre el nombre del programa en el atajo de línea de comandos. Nota: 6,5/10.

**Fortalezas que vio:**

- El instalador es por usuario, no pide administrador, deja desmarcados el acceso directo del escritorio y el PATH, y al desinstalar nunca toca los documentos; la carpeta de ajustes solo se borra si la persona lo pide (packaging/installer/clearmd.iss).
- El instalador liviano se niega a instalar encima de las otras ediciones y dice qué archivo usar (ADR-0052). Así nadie pierde la App Moderna por descargar el archivo más obvio.
- Si se instala en español, la app abre en español sin detectar el idioma del sistema (respeta ADR-0017) y nunca pisa un settings.toml que ya existe.
- La tabla 'Qué Descargar' empieza con 'A la mayoría le basta este', da un consejo de accesibilidad y explica cómo desinstalar cada archivo.
- El Inicio promete lo importante en una línea ('Tus originales nunca se modifican… ClearMD_Output') y el riel recuerda siempre '100 % local'.
- En la Bienvenida cada idioma aparece escrito en su propio idioma, y el cambio se aplica al momento.
- Resultados dice cómo entregar el trabajo a la IA ('adjunta el archivo .md o pega su texto; si lo dividiste, entrégale las partes en orden').
- El ejecutable de un solo archivo muestra una pantalla de carga mientras se desempaca, para que nadie crea que 'no abrió'.
- Los ejecutables fijan FLET_VIEW_PATH al cliente empaquetado (packaging/launch_flet.py), así que la descarga para Windows cumple la promesa de no usar internet.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F4-01 | 🔴 Alta | medio | alta | Guardar cualquier ajuste fija para siempre todos los valores por defecto, incluso los que la persona nunca eligió |
| F4-02 | 🔴 Alta | pequeño | alta | Para llegar al instalador hay que pasar unas 900 palabras bilingües, y no existe un enlace directo de descarga |
| F4-03 | 🔴 Alta | pequeño | media | No se avisa del bloqueo del navegador al descargar, y el aviso de Windows queda lejos del botón de descarga |
| F4-04 | 🟠 Media | pequeño | alta | Quien vuelve no tiene forma de saber que hay una versión nueva ni cómo actualizar |
| F4-05 | 🟠 Media | pequeño | alta | El instalador liviano tiene siete pantallas para una sola app, incluida una licencia en inglés que hay que aceptar |
| F4-06 | 🟠 Media | pequeño | alta | La primera decisión dice 'Markdown' sin decir para qué sirve: dentro de la app desaparece la promesa de 'para tu IA' |
| F4-07 | 🟠 Media | pequeño | media | El primer resultado, y el resumen que se pide leer primero, no se abren con doble clic en Windows y muestran código en el Bloc de notas |
| F4-08 | ⚪ Baja | pequeño | alta | La Bienvenida aparece en cada inicio y no indica qué idioma está activo |
| F4-10 | ⚪ Baja | pequeño | alta | La documentación del instalador y algunas imágenes del README describen versiones viejas |
| F4-11 | ⚪ Baja | pequeño | alta | El atajo 'Línea de Comandos' del instalador dice que se escriba clearmd-cli, pero la ayuda que muestra dice 'usage: clearmd' |

<details><summary>Detalle técnico y evidencia</summary>

- **F4-01 — Guardar cualquier ajuste fija para siempre todos los valores por defecto, incluso los que la persona nunca eligió**
  - *Impacto:* Pensemos en alguien que en la 2.11 o antes solo marcó 'No volver a mostrar' en la Bienvenida, o solo cambió el idioma. Su archivo de ajustes quedó con html_strategy = "full", el valor por defecto de entonces. Desde la 2.12 sigue convirtiendo páginas web completas, con menús y anuncios, y cada resumen le dice que 'eligió' guardar la página completa. Además, ninguna mejora futura de un valor por defecto le llegará a quien ya usó la app, que es justamente la persona que vuelve.
  - *Evidencia:* Comprobado de nuevo en esta ronda. src/clearmd/backend/use_cases/settings.py:54-70: serialize_settings recorre fields(Settings) y escribe todos los campos. `git show v2.11.0:src/clearmd/backend/schemas/settings.py` → línea 17 html_strategy: str = "full"; hoy schemas/settings.py:17 = "article". grep de settings_version o schema_version en backend: sin resultados, así que no hay versión de archivo ni migración. Lo que guarda: preferences.py:110-117 (dismiss_welcome) y la elección del idioma. En la ronda 1 ejecuté serialize_settings(replace(Settings(), show_welcome=False)) y salieron 16 líneas, html_strategy entre ellas.
  - *Recomendación:* Escribir en settings.toml solo los valores distintos del valor por defecto y agregar un número de versión del archivo. Para los archivos que ya existen, hacer una migración única: si el archivo no tiene versión y trae html_strategy="full", tratarlo como el valor por defecto viejo, aplicar el nuevo y decirlo una vez. La enmienda de ADR-0025 ('el valor guardado se respeta') sigue valiendo para quien de verdad eligió 'Página completa'. Pero un valor que la app escribió sola no es una elección. Pido al dueño acotar esa enmienda solo para este caso.
- **F4-02 — Para llegar al instalador hay que pasar unas 900 palabras bilingües, y no existe un enlace directo de descarga**
  - *Impacto:* El botón 'Descargar ClearMD' del README no descarga nada: lleva a una página de GitHub con unas 900 palabras que mezclan inglés y español en cada viñeta y hablan de 'la cuarta auditoría' (ver B5-07). Debajo hay una lista de 11 archivos con nombres técnicos, y el recomendado no es el primero. Es el momento de más abandono, y está lleno de lectura.
  - *Evidencia:* Ronda 1: `gh release view --json body` de v2.12.0 dio 906 palabras y 11 archivos, con nombres que unas veces llevan 'v' y otras no. README.md:22 enlaza a /releases/latest. .github/workflows/release.yml:176-177 publica solo nombres con versión. packaging/RELEASE_NOTES.md alterna viñetas 'EN / ES'. B5-07 confirma por su lado el vocabulario interno de esas notas.
  - *Recomendación:* Publicar en cada versión una copia sin número, 'ClearMD-Setup.exe', y hacer que el botón del README apunte a /releases/latest/download/ClearMD-Setup.exe: un clic y empieza la descarga. En la página de la versión, arriba: una frase, la tabla 'Qué Descargar' y los dos pasos para el aviso del navegador (F4-03). Las novedades van en un bloque plegable, con un bloque en español y otro en inglés, sin la palabra 'auditoría' (coincide con B5-07). Unificar los nombres de los archivos.
- **F4-03 — No se avisa del bloqueo del navegador al descargar, y el aviso de Windows queda lejos del botón de descarga**
  - *Impacto:* Como el instalador no está firmado y cada versión nueva empieza sin reputación, Edge o Chrome pueden bloquear la descarga ('no se descarga con frecuencia') antes de ejecutarla. Para conservarla hay que abrir menús escondidos. Las notas solo explican el aviso posterior de Windows. La página que explica la firma (CODE_SIGNING.md) habla en presente de una firma que no existe (B5-09), y la página para comprobar la descarga está solo en inglés (B5-08). Una persona no técnica lee 'puede ser peligroso' y abandona.
  - *Evidencia:* Ronda 1: grep de 'commonly' y 'Keep anyway' en README*, packaging/*.md y SECURITY.md: sin resultados. RELEASE_NOTES.md solo trae 'More info → Run anyway'. El aviso del README queda unas 180 líneas debajo del botón de la línea 22. `gh release list`: v2.8.1 a v2.12.0 salieron entre el 8 y el 9 de noviembre. No lo probé en Edge: es el comportamiento conocido de SmartScreen con archivos nuevos sin firma.
  - *Recomendación:* No vuelvo a proponer la firma: ya está planeada con SignPath. Mientras llega, poner justo debajo del botón de descarga y al principio de cada versión dos pasos con una imagen pequeña. '1) Si tu navegador dice que no se descarga con frecuencia: ⋯ → Conservar → Mostrar más → Conservar de todos modos.' '2) Si Windows dice que no lo reconoce: Más información → Ejecutar de todas formas.' Agregar una frase que tranquilice ('pasa porque ClearMD aún no está firmado') con un enlace a una explicación en español de cómo comprobar la suma (ver B5-08).
- **F4-04 — Quien vuelve no tiene forma de saber que hay una versión nueva ni cómo actualizar**
  - *Impacto:* ClearMD nunca usa internet, así que nunca avisa de versiones nuevas. Eso está bien, pero ningún texto le dice a la persona dónde mirar ni que basta con ejecutar el nuevo instalador encima. Los cambios de comportamiento (en la 2.12, artículo por defecto en las páginas web; en la 2.13, un resultado en blanco cuenta como 'falló') llegan sin aviso a quien actualiza.
  - *Evidencia:* Ronda 1: grep -i 'updat\|actualiz' en README.md, README.es.md, RELEASE_NOTES.md y en.toml: no hay ninguna guía de actualización. en.toml:499 gui.help.version = "ClearMD {version}". Que una actualización conserva los ajustes solo está documentado para mantenedores, en packaging/installer/README.md.
  - *Recomendación:* Agregar a la Ayuda una línea 'Actualizaciones' con la dirección escrita como texto, sin conectarse: 'Las versiones nuevas están en github.com/ClearNote97/ClearMD/releases; descarga el mismo archivo y ejecútalo, tus ajustes se conservan'. Guardar en los ajustes la última versión abierta y, si cambió, mostrar una sola vez un aviso local con los cambios de comportamiento. Ese aviso es también el lugar natural para la migración de F4-01.
- **F4-05 — El instalador liviano tiene siete pantallas para una sola app, incluida una licencia en inglés que hay que aceptar**
  - *Impacto:* Quien instala en español pasa por siete pantallas: idioma, Bienvenida, una licencia legal en inglés con 'No acepto' marcado y 'Siguiente' bloqueado, la carpeta de instalación, las tareas, 'Listo para instalar' y la final. La licencia en otro idioma y la pregunta por la carpeta son justo los momentos de duda de alguien que nunca instaló nada.
  - *Evidencia:* Comprobado de nuevo: packaging/installer/clearmd.iss:53 `LicenseFile={#Root}\LICENSE` (un solo archivo, MIT, en inglés). grep de DisableDirPage, DisableReadyPage y ShowLanguageDialog en clearmd.iss: no aparece ninguno, así que rigen los valores por defecto de Inno. Los mensajes RemoveSettings no cierran la pregunta con '?'. No compilé el instalador.
  - *Recomendación:* En la edición liviana, quitar la página de licencia: la MIT no exige aceptarla y el archivo LICENSE se sigue instalando. Agregar DisableDirPage=yes (o auto) y DisableReadyPage=yes. Así queda Bienvenida → Instalar → Listo. Corregir los signos de pregunta de RemoveSettings y la frase sobre el idioma en el README del instalador.
- **F4-06 — La primera decisión dice 'Markdown' sin decir para qué sirve: dentro de la app desaparece la promesa de 'para tu IA'**
  - *Impacto:* La persona descargó 'Prepara tus documentos para la IA'. Al abrir la app lee 'Documentos a Markdown', 'Convierte, divide o une tus documentos' y 'Convertir a Markdown'. La IA no aparece en ninguna de esas tres frases, y 'Markdown' solo se explica dentro de la Ayuda. Quien no conoce la palabra duda en el primer clic.
  - *Evidencia:* en.toml:625-635 (gui.home.convert = "Convert to Markdown", convert_body = "PDF, Word, Excel, PowerPoint, HTML and more"); gui.app.subtitle = "Documents to Markdown, on your computer"; gui.welcome.intro. La explicación solo está en gui.help.markdown (en.toml:482). Capturas docs/screenshots/018/0-home-light-es.png y 007/0-welcome-light-es.png.
  - *Recomendación:* Repetir el propósito en el primer contacto, sin renombrar las herramientas ni romper el Title Case. Subtítulo: 'Prepara tus documentos para la IA, en tu computador'. Texto de la tarjeta: 'Para que tu IA lo lea bien: PDF, Word, Excel…'. En la Bienvenida, una línea: 'Markdown es texto ordenado que las IA leen mejor que un PDF'. Esto encaja con F3-10: la línea que se repite sobre privacidad podría dejar su lugar a esta.
- **F4-07 — El primer resultado, y el resumen que se pide leer primero, no se abren con doble clic en Windows y muestran código en el Bloc de notas**
  - *Impacto:* Al terminar se abre la carpeta. La Ayuda dice 'lee primero el resumen', pero Resumen_ClearMD.md no tiene un programa asignado en Windows: el doble clic pregunta '¿Cómo quieres abrir este archivo?'. Si la persona logra abrirlo en el Bloc de notas, ve etiquetas como <details><summary> y comentarios HTML (B5-10). El primer éxito termina en una duda.
  - *Evidencia:* Comprobado de nuevo: schemas/settings.py:20 summary_format = "markdown". ADR-0031:15 reconoce que hay 'people who will not open a .md'. en.toml:482 y :493. Las claves de [gui.result] en es.toml (líneas 404-428) no explican cómo abrir un .md. B5-10 muestra que el historial va dentro de <details>. No probé la asociación de archivos en Windows.
  - *Recomendación:* Agregar en Resultados y en la Ayuda una línea práctica: 'Para abrir un .md: clic derecho → Abrir con → Bloc de notas'. Que en las ventanas el resumen por defecto sea 'Markdown + PDF', y que la línea de comandos siga con Markdown. Esto cambia el valor por defecto de ADR-0031. Lo pido porque el propio ADR reconoce que su usuario principal no abre .md, y B5-10 muestra que, cuando lo abre, ve código.
- **F4-08 — La Bienvenida aparece en cada inicio y no indica qué idioma está activo**
  - *Impacto:* Quien vuelve encuentra cada vez una ventana encima del Inicio, hasta que descubre 'No volver a mostrar'. Los botones 'English' y 'Español' se ven iguales, así que no queda claro cuál está elegido. Y la casilla, al guardarse, dispara el problema de F4-01.
  - *Evidencia:* Comprobado de nuevo: schemas/settings.py:18 show_welcome = True; preferences.py:52 la muestra en cada inicio mientras sea True. spec/contracts/ux.md:51 dice 'On first run'. ttk/views/dialogs/welcome.py: los dos botones usan el mismo estilo, sin marca de selección.
  - *Recomendación:* Mostrarla solo en el primer inicio, o hasta que termine la primera tarea, como dice el contrato, y dejarla disponible desde la Ayuda. Marcar el idioma activo con relleno o un ✓, con un texto accesible que lo diga. Quitar la línea bilingüe 'Cambia el idioma en Ajustes…'.
- **F4-10 — La documentación del instalador y algunas imágenes del README describen versiones viejas**
  - *Impacto:* Quien lee el README o la página del instalador para decidir si confiar encuentra una insignia de 'en construcción', una animación de la 2.7, una captura del instalador sin la App Estilo Móvil y una App Clásica descrita como 'un solo archivo de 36 MB', cuando hoy es una carpeta. La parte del README sobre opciones y mensajes ya la cubre B5-04, y la doy por confirmada.
  - *Evidencia:* Comprobado de nuevo: README.md:222 '`--html {full,article}` \| Web pages: the whole page (default)', contra schemas/settings.py:17 "article" (coincide con B5-04). README.md:20 trae la insignia 'under construction'. docs/screenshots/007/flow-light-en.gif muestra la v2.7.0. packaging/installer/README.md dice 'one file, about 36 MB' (ADR-0053 lo cambió a carpeta). docs/screenshots/019/02-parts-light.png muestra las tarjetas viejas.
  - *Recomendación:* Actualizar la insignia, el GIF, la captura del instalador y la descripción de la App Clásica. Agregar una prueba que compare la versión que muestran las capturas y el GIF con la versión actual. Para la tabla de opciones, seguir B5-04: generarla desde el código.
- **F4-11 — El atajo 'Línea de Comandos' del instalador dice que se escriba clearmd-cli, pero la ayuda que muestra dice 'usage: clearmd'**
  - *Impacto:* La primera vez que alguien abre el atajo de línea de comandos ve la ayuda, que empieza con 'usage: clearmd …'. Debajo, la línea del instalador le dice 'Type: clearmd-cli "<folder or file>"'. Si copia lo que dice la ayuda, Windows responde que 'clearmd' no se reconoce como un comando. Es un tropiezo en el primer intento.
  - *Evidencia:* Comprobado en esta ronda: src/clearmd/frontend/cli/parser.py:14 prog="clearmd". packaging/installer/clearmd.iss:245 y :254: el atajo ejecuta clearmd-cli.exe --help y luego muestra 'Type: clearmd-cli …'. clearmd.iss:145-146 (CompareCli) también dice clearmd-cli. Lo señaló B5-05; aquí lo enfoco en el primer uso.
  - *Recomendación:* Que el nombre que muestra la ayuda sea el del programa que se está ejecutando, por ejemplo usando el nombre del ejecutable: 'clearmd-cli' en Windows y 'clearmd' desde pip. Agregar a la ayuda un ejemplo copiable con ese nombre.

</details>

### Frontend · Claridad es cariño — 7/10

Tras el debate mantengo el diagnóstico: el tono de las ventanas es cuidadoso y parejo en los dos idiomas, pero la pantalla final no siempre dice la verdad. Volví a revisar el código y lo confirmé. (1) Resultados se salta todo documento convertido, con o sin notas (presenter/screens/results.py:33-34), así que muestra "Todos los archivos se convirtieron" mientras el resumen escrito dice "Necesita Tu Atención". (2) Revisar nunca usa los avisos del plan (no hay ninguna referencia a "warnings" en screens/review.py): un PDF que puede detenerse aparece como "Listo". (3) Los archivos que solo informan tapan el mensaje de éxito y reciben consejos como "Hazlo visible para convertirlo" (es.toml:95). Los colegas confirmaron el mismo patrón en otros sitios: la línea de la cabecera repite el estado del lote anterior en cualquier página (F3-03, confirmado en header.py:26-27); un error durante la revisión promete que "lo ya convertido se conserva" (F1-04, confirmado en es.toml:515); la línea de comandos dice "Nada que convertir" con código 0 (B5-02); y Dividir anuncia "se dividió" cuando quedó una sola parte (B5-03). Fusioné mi hallazgo sobre las rutas cortadas con F3-05, que tiene evidencia más fuerte. Nota: 7/10. Tiene tono de cariño, pero le falta coherencia entre lo que pasó y lo que se dice.

**Fortalezas que vio:**

- Cada fila de Revisar y Resultados empieza con una palabra ('Omitido:', 'Con error:', 'Detenido:') y no solo con un color, y siempre trae el motivo y qué hacer (screens/review.py:24-28, screens/results.py:29-41).
- Hay frases que tranquilizan donde la persona duda: 'Tus originales nunca se modifican: ClearMD crea archivos nuevos en una carpeta ClearMD_Output' y 'Puedes cancelar cuando quieras: lo ya terminado se conserva'.
- El cierre durante una tarea explica qué se conserva y ofrece por defecto 'Seguir Trabajando'. Es claro y no da miedo.
- 'Para usarlo con tu IA: adjunta el archivo .md o pega su texto; si lo dividiste, entrégale las partes en orden' es justo la frase que necesita una persona no técnica.
- 'Copiar Detalles' reconoce sus límites con honestidad ('revisa que no quede ninguno').
- 'Quitar Todo' se puede deshacer y avisa cuántos quitaste.
- Los catálogos en inglés y español están parejos, y una prueba automática vigila el Title Case.
- Cada herramienta tiene su propio vocabulario ([tool.split], [tool.merge]), en vez de decir 'Convertir' en todas partes.
- El tono de lo que solo informa ya es neutro y no se pinta de alarma (review.py:61-70, skipped_tone). Solo falta que tampoco tape el mensaje de éxito.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F5-01 | 🔴 Alta | medio | alta | Resultados dice 'todo bien' aunque el documento se convirtió con problemas |
| F5-02 | 🔴 Alta | pequeño | alta | Archivos que solo informan borran el mensaje de éxito y dan consejos equivocados |
| F5-03 | 🔴 Alta | pequeño | alta | Revisar no dice qué PDF puede detenerse por tardar demasiado |
| F5-04 | 🟠 Media | pequeño | alta | Resultados no dice dónde está el resumen y 'Abrir Carpeta' abre todas las ventanas a la vez |
| F5-06 | 🟠 Media | pequeño | media | El paso 1 pide decidir 'Imágenes' y 'Resumen del Proceso' sin explicar qué son |
| F5-07 | ⚪ Baja | pequeño | alta | Revisar dice 'hasta que confirmes', pero ahí no hay nada que confirmar |
| F5-08 | ⚪ Baja | pequeño | media | Nombres técnicos a la vista de una persona no técnica: ttk, Qt, flet, LGPL, ClearMD-Setup-Full |
| F5-09 | ⚪ Baja | pequeño | alta | Detalles de español y de términos que restan claridad |

<details><summary>Detalle técnico y evidencia</summary>

- **F5-01 — Resultados dice 'todo bien' aunque el documento se convirtió con problemas**
  - *Impacto:* Puede pasar que un PDF tenga páginas escaneadas sin texto, que una página web se convierta entera en vez del artículo, que una ecuación quede como símbolos sueltos o que se quiten encabezados repetidos. En todos esos casos la ventana muestra 'Todos los archivos se convirtieron' y abre la carpeta como si todo estuviera perfecto. La persona le entrega a su IA un texto incompleto sin saberlo, mientras el resumen escrito al lado dice 'Necesita Tu Atención'. Esto también deja invisibles en la ventana los avisos que otros auditores piden mejorar (B3-03, B3-04, B2-01).
  - *Evidencia:* Lo volví a revisar. presenter/screens/results.py:33-34: 'else: # converted, and kept ... continue' se salta todo resultado convertido sin mirar outcome.notes. grep de 'notes' en frontend/presenter: ninguna referencia a las notas de conversión. es.toml:425 all_good = 'Todos los archivos se convirtieron…'. Caso sintético de la ronda 1: tests/fixtures/html/no_article.html + hostile.html + sample.docx. La CLI imprime 'convertido con notas' y Resumen_ClearMD.md trae '## Necesita Tu Atención' con 2 entradas.
  - *Recomendación:* Mostrar en 'Lo que Necesita Tu Atención' cada documento convertido con notas que piden revisar algo (páginas sin texto, ecuaciones, página completa, contenido quitado), con la palabra 'Convertido, pero:' y la nota principal, en tono de aviso. En ese caso, el estado debe ser 'Terminado con problemas'. Prueba con el caso difícil: un PDF de 2 páginas donde una es imagen; debe verificar que NO aparece la tarjeta 'todo bien'.
- **F5-02 — Archivos que solo informan borran el mensaje de éxito y dan consejos equivocados**
  - *Impacto:* En una carpeta normal de Windows es casi seguro que aparezca un desktop.ini, un archivo ~$ de Office o un .md. Cuando pasa, la pantalla no dice 'Todos los archivos se convirtieron': muestra 'Lo que Necesita Tu Atención' sobre filas que no piden nada. Para un archivo oculto del sistema aconseja 'Hazlo visible para convertirlo', algo que una persona no técnica no debe hacer.
  - *Evidencia:* Lo volví a revisar. results.py:36-46: lo INFORMING se agrega igual como fila (solo cambia a Tone.NEUTRAL). Con cualquier fila, las vistas ocultan all_good (flet/views/results.py:63-69; lo mismo en ttk y pyside). es.toml:95 [skip_action] hidden = 'Hazlo visible para convertirlo.' Caso sintético de la ronda 1: una carpeta con nota.txt, leeme.md, .oculto y desktop.ini, con `clearmd in --lang es` → '1 convertido · 3 omitidos', y desktop.ini aparece como 'formato no soportado… Revisa los formatos compatibles en la ayuda' (en Linux no está oculto). B5-06 confirma por su lado que esa ayuda no lista formatos.
  - *Recomendación:* Cuando todo lo pendiente es informativo, mostrar la tarjeta de éxito y debajo una línea discreta, por ejemplo 'Además, 3 archivos no se tocaron porque no hacía falta (ver lista)'. Para los archivos ocultos o de sistema, cambiar el consejo por 'archivo oculto del sistema: no se convierte'. Considerar ignorar en silencio desktop.ini, Thumbs.db y .DS_Store. Prueba con el caso difícil: un desktop.ini oculto y de sistema, un ~$ y un .md.
- **F5-03 — Revisar no dice qué PDF puede detenerse por tardar demasiado**
  - *Impacto:* Si un PDF probablemente va a pasarse del límite de tiempo, su fila en Revisar dice '✓ Listo para convertir · PDF'. Solo aparece un botón 'Dividir los PDF Muy Grandes (1)', sin decir cuál ni por qué. La persona pulsa Convertir, espera minutos y recibe 'Detenido'. La terminal sí avisa antes; la ventana, no. Con los demás formatos lentos ni siquiera aparece el botón.
  - *Evidencia:* Lo volví a revisar. screens/review.py:16-22: cada fila planeada usa 'gui.plan.ready' sin consultar plan.warnings. grep de 'warnings' en frontend/presenter: solo preferences.py (avisos de ajustes). La oferta de dividir sale de large_in_plan (review.py:56,78-80). Captura docs/screenshots/018/2-review-split-offer-light-es.png.
  - *Recomendación:* Poner la fila con aviso en tono de aviso y con un texto como '⚠ Puede tardar más de 10 min y detenerse · PDF. Te conviene dividirlo antes (botón abajo)'. Cuando el archivo es uno solo, nombrarlo en el botón. Para formatos que no son PDF, usar error.timed_out.action_other. Prueba con el caso difícil: el único archivo lento al final de una lista larga.
- **F5-04 — Resultados no dice dónde está el resumen y 'Abrir Carpeta' abre todas las ventanas a la vez**
  - *Impacto:* La Ayuda pide leer primero el resumen, pero Resultados nunca nombra Resumen_ClearMD. El botón está en singular y abre una ventana del Explorador por cada ClearMD_Output. La tarjeta de éxito dice 'la carpeta ClearMD_Output' aunque arriba se listan cuatro carpetas, y dice 'Todos los archivos se convirtieron' aunque uno solo se conservó.
  - *Evidencia:* es.toml [gui.result]: ninguna clave menciona Resumen_ClearMD (solo aparece en gui.settings.summary_help, línea 460, y en gui.help.where). intents/results.py:31-40: open_results recorre todas las result_folders. Captura 007/4-results-all-good-light-es.png ('5 Convertidos · 1 Conservado', 4 rutas, all_good en singular).
  - *Recomendación:* Agregar la línea 'En cada carpeta hay un resumen, Resumen_ClearMD, que dice qué pasó con cada archivo'. Con más de una carpeta, que el botón diga 'Abrir Carpetas de Resultados (4)', o abrir solo la primera. Que la tarjeta de éxito cuente: 'Se convirtieron 5; 1 ya existía y se conservó'. Esto se combina con F4-07 (cómo abrir un .md).
- **F5-06 — El paso 1 pide decidir 'Imágenes' y 'Resumen del Proceso' sin explicar qué son**
  - *Impacto:* En la primera pantalla de trabajo aparecen 'Imágenes: No incluir / En una carpeta' y 'Resumen del Proceso: Markdown / Markdown + PDF / Solo PDF', sin explicación. La persona todavía no ha visto ningún resumen. En Dividir, todo esto se suma al bloque de partes y la pantalla queda muy cargada. F3-04 y F4-09 confirman, desde lo visual, que esas opciones le quitan espacio a la lista.
  - *Evidencia:* es.toml gui.main.images_title / summary_title. Las explicaciones images_help (es.toml:465) y summary_help (es.toml:460) solo se usan en Ajustes. Capturas 018/1-choose-light-es.png y 018/1-choose-split-light-es.png.
  - *Recomendación:* Lo mínimo, sin enmendar ninguna decisión: una línea de explicación junto a cada opción. Si el dueño acepta la propuesta de F3-04 y F4-09 (una línea resumida con 'Cambiar'), esa línea debe decir en palabras qué se eligió ('Resumen: un archivo que cuenta qué pasó, en Markdown'), no solo el valor técnico.
- **F5-07 — Revisar dice 'hasta que confirmes', pero ahí no hay nada que confirmar**
  - *Impacto:* El subtítulo de Revisar promete una confirmación que no existe ahí: el botón dice 'Siguiente', y la persona busca un 'Confirmar'.
  - *Evidencia:* es.toml:572 review_subtitle = 'Nada se escribe hasta que confirmes.' Captura 018/2-review-light-es.png (botón 'Siguiente'). gui.plan.confirm no se usa en el código.
  - *Recomendación:* Cambiar el texto a 'Nada se escribe todavía: el último paso es Convertir' y borrar la clave que no se usa.
- **F5-08 — Nombres técnicos a la vista de una persona no técnica: ttk, Qt, flet, LGPL, ClearMD-Setup-Full**
  - *Impacto:* El instalador y la Ayuda piden elegir entre 'ClearMD (ttk)' y 'ClearMD (Qt)' y mencionan LGPL o el nombre de un archivo. Para el público general son ruido que da inseguridad al elegir.
  - *Evidencia:* Captura docs/screenshots/019/06-parts-spanish.png. es.toml gui.app.window_ttk/window_qt/window_flet y gui.help.keyboard ('está en ClearMD-Setup-Full').
  - *Recomendación:* Mostrar solo 'App Clásica', 'App Moderna' y 'App Estilo Móvil'. El nombre técnico va solo en el detalle de soporte, y en la Ayuda se dice 'la versión completa del instalador'.
- **F5-09 — Detalles de español y de términos que restan claridad**
  - *Impacto:* En un producto que presume de claridad, se notan varias cosas: 'computador' y 'equipo' en la misma pantalla, 'Los Resultados Van' como título incompleto, la opción 'Ambas' sin decir de qué, 'Guardar:' repetido con el botón de Ajustes, mayúsculas distintas después de 'Con error:' y 'Omitido:', 'Skipped' frente a 'Left out' en inglés, y '30000' sin punto de miles.
  - *Evidencia:* es.toml:599 output_title='Los Resultados Van', :650 keep_both='Ambas', :416 word_skipped='Omitido:'. Capturas 018/0-home-light-es.png, 018/4-results-light-es.png y 018/1-choose-split-light-es.png. F3-10 confirma por su lado la mezcla de 'computador' y 'equipo' (es.toml:514).
  - *Recomendación:* Usar una sola palabra ('computador'). Cambiar 'Los Resultados Van' por 'Dónde Guardar los Resultados' y 'Guardar:' por 'Qué conservar de cada parte:', con las opciones 'El PDF', 'El Markdown' y 'Los dos'. Unificar las mayúsculas después de la palabra de estado y 'Skipped' con 'Left out'. Dar formato al número según el idioma.

</details>

## 10. Lecciones para las plantillas

Las lecciones de esta quinta auditoría se incorporaron a
[`docs/lessons-learned.md`](../lessons-learned.md), Parte XVII (en inglés, como el resto de ese archivo).
Lo que propuso la conciliadora:

- Producto: cada protección (archivo trampa, contraseña, vacío, oculto, memoria) vive en una sola puerta previa por la que pasan todas las herramientas. Hay una prueba por herramienta con el caso difícil. En esta auditoría el mismo hueco apareció cuatro veces en Dividir y Unir.
- Producto: una sola función de «resultado vacío» que mide lo que vería una persona, sin las marcas que agrega el propio programa.
- Producto: la pantalla final se calcula con la misma información que el resumen escrito. Una prueba compara «Necesita Tu Atención» con lo que muestra la ventana, usando el mismo lote.
- Producto: clasificar un aviso como «buena noticia» exige que nunca pueda ser falso. Si una limpieza puede equivocarse, su aviso dice qué tocó y pide revisar.
- Producto: todo lo que trabaja con páginas razona por la posición en la página, nunca por el orden en que se dibujó el contenido.
- Aplicar una auditoría: cuando el dueño enmienda una ADR, la prueba que la cumple usa el caso más difícil de esa enmienda. Aquí, la carta de 2 páginas con el pie dibujado después del encabezado.
- Aplicar una auditoría: cada decisión de una junta de dudas se escribe también en la ADR, con la frase «no se hace X». Así la próxima junta la ve y no la vuelve a proponer (pasó con la migración del ajuste guardado).
- Aplicar una auditoría: la conciliadora de valor debe listar todo hallazgo de severidad alta que deja fuera, con su motivo. Aquí se perdió B3-01 sin decirlo.
- Método: cinco expertos por junta y tres conciliadoras funcionan, y en la quinta auditoría las mejoras anteriores quedaron casi todas resueltas (6 de 11, y 5 en parte). El rendimiento baja: cada ronda encuentra sobre todo bordes de lo nuevo. El tope de cinco auditorías por versión mayor es razonable.
- Método: dar a las juntas, además de las ADR, una lista corta de decisiones ya tomadas y de lo que no se hace, con la regla de que reabrir algo exige evidencia nueva.
- Método: pedir a la conciliadora de la verdad que reproduzca al menos un caso por cada ADR enmendada en el ciclo, no solo los hallazgos de las juntas.
- Método: limitar los grupos de la conciliación a temas que se puedan aceptar o rechazar juntos. Un grupo de seis temas distintos no se puede decidir.
