# Juntas de Auditoría de ClearMD 2.12.0 (Versión 4)

> **Fecha:** 2026-11-09 · **Versión auditada:** 2.12.0 · **Para:** el dueño del producto.
> Cuarta auditoría: agentes nuevos desde cero, cinco expertos por junta y tres conciliadoras con «Claridad es cariño». Anteriores: [primera](./2026-11-08-audit-boards.md), [segunda](./2026-11-09-audit-boards-v2.md) y [tercera](./2026-11-09-audit-boards-v3.md).
> Documento en español por excepción a ADR-0011: está escrito para que el dueño decida.
> Presentación ejecutiva: [ClearMD · Auditoría v4](https://claude.ai/artifact/Xh4hbWC7YZgCmY7tr29QpF) (privada del dueño).
> Datos completos de las tres rondas: [`2026-11-09-audit-boards-v4.json`](./2026-11-09-audit-boards-v4.json).

## Cómo leer este documento

- **Si tienes 5 minutos:** lee el resumen ejecutivo (sección 1) y las once mejoras recomendadas (sección 4).
- **Para decidir:** las secciones 5 (lo que no conviene hacer) y 6 (desacuerdos abiertos).
- **Para el detalle:** la sección 8 trae cada hallazgo verificado: qué siente la persona, qué se recomienda y
  qué comprobó la junta conciliadora. La sección 9 trae el informe de cada auditor.
- Las referencias técnicas (archivo:línea) quedan para quien implemente; no hace falta entenderlas para decidir.

## 1. Resumen ejecutivo

**Veredicto: 7 de 10**, igual que en la tercera auditoría. La 2.12.0 avanzó mucho, pero hizo
promesas nuevas y más grandes ("abrir un resultado no descarga nada", "lo que llega a tu IA es lo
que tú ves"), y en los casos más difíciles todavía no se cumplen del todo.

**Lo que mejoró de verdad con la 2.12.0:**

- Las notas y los CSV de Windows salen bien en casi todos los casos ("José;Bogotá;Medellín",
  "Canción de cuna…").
- Si una parte de Dividir falla, las partes buenas se conservan.
- Ya no aparece el aviso falso "puede tardar más de 10 minutos".
- Tras un error, Resultados dice "se detuvo: N de M terminados", y la carpeta se abre sola solo
  si todo salió bien.
- Una regla de teclado común en las tres ventanas, "Deshacer" al vaciar la lista, Ajustes que
  cabe en la pantalla, y un instalador que abre la app al terminar.
- El texto invisible de los PDF se quita y se avisa (ADR-0054), y las páginas web convierten su
  artículo por defecto.

**De las diez mejoras de la tercera auditoría:**

- 4 quedaron resueltas del todo.
- 6 quedaron en parte.
- Ninguna empeoró.

**De tus cinco decisiones:** el archivo vacío "falló" con su razón quedó cumplido. El artículo
por defecto, el canal de reporte y el ADR del texto oculto quedaron en parte. La firma de los
instaladores está lista en el flujo, pero espera a que SignPath esté configurado.

**Lo que todavía no es verdad, es decir, lo que una persona vería:**

- **Un resultado vacío se llama "convertido".** Un PDF escaneado o una presentación vacía dan un
  archivo en blanco, y ClearMD dice "El documento se convirtió".
- **"Copiar Detalles" todavía manda a GitHub Issues**, que pide cuenta, y no menciona el correo.
  Va contra tu decisión; se arregla con una línea.
- **La limpieza de la salida tiene huecos:** formas raras de escribir una imagen se escapan, y
  Unir no pasa por el filtro.
- **Notas de 2 a 5 letras siguen rotas:** "Sí" sale como un símbolo chino. Las notas de la
  versión prometían lo contrario.
- **Un logo apaga el filtro de texto invisible**, porque ADR-0054 lo dice así, al pie de la letra.
- **Al unir capítulos 1 a 11, el 10 queda justo después del 1.**
- **El "qué hacer" de cada archivo se corta** en Revisar y Resultados ("Quít…"), y algunas cifras
  y colores se contradicen.

**La buena noticia:** casi todas las mejoras nuevas son pequeñas, y cuatro de los problemas más
visibles se arreglan con una o dos líneas.

**Junta de dudas:** en este ciclo no hizo falta. Las decisiones que surgieron al aplicar las
mejoras estaban cubiertas por lo que ya decidiste o por las ADR, y quedaron anotadas como
lecciones (Parte XIV), por ejemplo decir que la App Moderna "funciona mejor" con un lector de
pantalla, en vez de afirmar algo que nadie había probado.

### Lo que tienes que decidir

1. **Si te acoges a las once mejoras** (sección 4). Recomendación: sí; la mayoría son pequeñas.
2. **Tres desacuerdos abiertos** (sección 6):
   - ¿un resultado sin texto cuenta como "falló", con su razón? (Recomendado: sí. Es tu misma regla
     del archivo vacío.)
   - ¿se enmienda ADR-0054, para que solo una imagen grande proteja el texto invisible? (Recomendado.)
   - ¿se enmienda ADR-0030, para quitar el membrete también en documentos de 2 o 3 páginas, solo
     con líneas idénticas en el mismo margen? (Recomendado.)
3. **Si confirmas la lista de lo que no conviene hacer** (sección 5): no subir aún el tope de
   250 MB de Dividir, no sacar Imágenes y Resumen del paso 1, y no poner un candado antes de las
   medidas baratas.
4. **Más adelante:** reemplazar markitdown en Word y PowerPoint (largo; exige enmendar ADR-0004).

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
   hallazgos de los demás. Fueron 127 intervenciones. Después corrigió su propio
   informe: 91 hallazgos tras el debate.
3. **Conciliación.** La junta conciliadora volvió al código y a las capturas, unió los duplicados y quedó con
   **26 hallazgos verificados**.

**Lecciones de la primera auditoría, aplicadas como reglas** (`docs/lessons-learned.md`, IX.16):

- Cada auditor leyó los ADR antes de recomendar algo que los contradijera, y lo citó.
- Cada hallazgo dice si su evidencia la comprobó el propio auditor.
- En el debate, subir una gravedad exigía volver a comprobarla en el código (`reverified`).
- La ronda 2 debía listar todo hallazgo propio que retiraba y por qué; la conciliadora comparó las dos rondas.
- Las juntas no leyeron la primera auditoría; solo la conciliadora, para decir qué se resolvió.
- Ningún informe nombra los documentos privados del dueño, y antes de publicar se revisó que así fuera.

**Comprobación de lo retirado:** Confirmo la comprobación de C1: entre las rondas 1 y 2 no se perdió nada. B3-10 pasó a B3-09, F4-10 a F4-03 y F5-08 a F5-07, todas con su evidencia. Encontré otra pérdida, pero entre auditorías y no entre rondas. La tercera auditoría resolvió que, antes de un candado, se aplicarían dos medidas baratas: barrer solo los temporales viejos y no contar como éxito una parte que falta. Nunca se hicieron (output_files.py:135-154), y B1-01 aparece hoy como si fuera nuevo (C-3). También C1 dejó fuera, al reagrupar, las citas de ADR-0030 (B3-02) y de ADR-0015/0010 (B1-02); las restituí.

**Lo que la conciliadora de la verdad reprodujo ella misma:**

- Resultado vacío: PDF de 2 páginas en blanco creado con pypdfium2 -> `clearmd --overwrite --lang es blank/escaneado.pdf`: .md de 1 byte, '1 convertido · 0 con error', EXIT=0; el resumen dice 'El documento se convirtió' con ⚠️ y una nota sin paso siguiente (B1-03/B3-05/B5-01/F5-11)
- Garantía de salida: n.txt con `![a [b] c](http://evil.example/p.png)` y `![x][r]` + `[r]: http://...` -> las dos salen intactas; la imagen simple sí se neutraliza (B2-01)
- Unir .md: `clearmd --merge markdown a.md b.md` deja `![p](https://tracker.example/a.gif)` intacta (B2-02) y cambia el código `[^0-9]` por `[^d1-0-9]` (B1-07)
- Orden al unir: 'Capitulo 1/2/3/10/11.txt' con `clearmd --merge markdown order` -> Documento 2 de 5 es 'Capitulo 10.txt' (B1-04)
- Notas cp1252 cortas: printf 'S\xed' y 'A\xf1o' -> '叭' (adivinado utf_16_be) y 'A隳' (big5); 'Niño pequeño' sale bien (B5-03/B3-11)
- PDF de 260 MB (truncate) con `clearmd --split-pages 50 --dry-run --lang es` -> 'Omitido… Divídelo en archivos más pequeños.' y 'Nada que dividir.' (B1-02)
- CSV de 400 filas con una celda '24" pulgadas' y `--split-parts 4 --keep pdf` -> partes de 3, 2, 2 y 397 líneas (B1-05)
- Fixture pública sample.html -> el resumen dice 'HTML (Artículo)' y a la vez 'se convirtió la página completa' (B5-08)
- `clearmd --lang es --help` -> 'usage:' en inglés; `clearmd --lang es nada.xyz` (archivo inexistente) -> EXIT=2 (matiz de B5-05/B5-06)

**Notas de la conciliadora de Claridad es cariño:** Criterio: puse primero lo que hace que la IA reciba algo falso o vacío sin que la persona lo note, porque eso rompe la confianza en ClearMD. Después, lo que la deja sin saber qué hacer. Al final, lo que solo se ve feo. Preferí corregir lo que no es cierto antes que agregar controles nuevos.

Valores que bajé:
- F1-01 («0 convertidos» tras guardar Ajustes): lo bajé de alto a medio. Solo pasa con un error a mitad de tarea seguido de un cambio de ajustes, un camino poco común. Por eso lo metí en el grupo de contradicciones del puesto 10, sin puesto propio.
- B1-01 (dos ventanas sobre la misma carpeta): es poco frecuente, pero lo mantengo alto porque el daño es silencioso y el resumen miente.
- B2-04 (flet por pip): de acuerdo con «bajo»; afecta solo a quien instala con pip.

Lo que dejé fuera del top 10, pero debería ir justo después:
- El foco del teclado que no se ve (F2-01, F2-02, F2-09). Es alto para quien usa el teclado, y un archivo borrado sin verlo marcado da miedo de verdad.
- La App Moderna con el lector de pantalla (F2-05). No debe presentarse como la ventana para lectores de pantalla sin probarla con NVDA.
- Corregir el README: que diga «artículo por defecto», que el límite de memoria es «solo en Linux», y quitar «en construcción» (B5-05, B2-03). Es barato y también es cuestión de verdad.
- La frase de propósito en la Bienvenida: «Convierte tus documentos en texto que tu IA entiende mejor» (F4-01).

Lo que rechazo o freno por agregar complejidad:
- No mover las opciones de Elegir sin enmendar ADR-0031 y ADR-0033. Basta cambiar el título a «Dónde Guardar los Resultados».
- Dejar el ajuste de tamaño de texto para más adelante.
- No tocar la comprobación de OneDrive (B2-08) sin probarla antes en un Windows real.
- Para el bloqueo de carpeta (B1-01), basta un aviso de una línea, sin opciones nuevas.

**Notas por lente (de 0 a 10, tras el debate):**

| Lente | Nota | Hallazgos | Intervenciones en el debate |
| --- | --- | --- | --- |
| Backend · Lógica y robustez | 7 | 10 | 10 |
| Backend · Seguridad y privacidad | 7 | 8 | 10 |
| Backend · Fidelidad del contenido para la IA | 6,5 | 10 | 12 |
| Backend · Eficiencia y empaquetado | 7 | 7 | 10 |
| Backend · Claridad es cariño | 6,5 | 9 | 15 |
| Frontend · Lógica y estados | 6,5 | 8 | 12 |
| Frontend · Accesibilidad | 5,5 | 9 | 10 |
| Frontend · Estilo visual UI/UX | 6,8 | 10 | 15 |
| Frontend · Primer uso, instalación e idioma | 7 | 10 | 15 |
| Frontend · Claridad es cariño | 6,8 | 10 | 18 |

## 2b. Qué se resolvió desde la tercera auditoría (y tus cinco decisiones)

| Estado | Mejora o decisión de la tercera auditoría | Nota de la conciliadora de doctrina |
| --- | --- | --- |
| ◐ Parcial | 1. Notas y CSV cortos de Windows sin letras rotas | Lo comprobé: «José;Bogotá;Medellín», «Canción de cuna…» y «Café» salen bien. «Sí», «Año» y «¿Qué?» siguen rotos. La lección XIII.1 se repitió: la prueba no usó el caso más corto. |
| ◐ Parcial | 2. «Todo local» y privacidad: sin imágenes remotas ni rutas en el resumen | La imagen simple se neutraliza y el correo se escribe en memoria. Las formas raras y Unir lo saltan (B2-01, B2-02). El ocultador de rutas tiene huecos (B2-06). |
| ◐ Parcial | 3. Página de descarga e instalador que digan la verdad | Existen «Qué Descargar» y «Abrir ClearMD ahora» ([Run], clearmd.iss:258). Quedan la licencia en inglés, «Completando la Instalación» (línea 94), el atajo de terminal en inglés y el aviso de SmartScreen lejos del botón. |
| ✅ Resuelto | 4. Acompañar el primer uso | La Bienvenida cambia el idioma al momento, y la Ayuda y Resultados explican dónde quedan los archivos y cómo usarlos con la IA. Faltan detalles nuevos: marcar el idioma activo y una frase de propósito. |
| ◐ Parcial | 5. No asustar con «más de 10 minutos» y no borrar la lista al dividir | El aviso desapareció y la lista se devuelve. Pero la casilla «Mantener» se ignora y los valores temporales se guardan en disco al guardar Ajustes (lo comprobé en tools.py). El primer tercio de un PDF largo pasa sin avance. |
| ✅ Resuelto | 6. Dividir conserva las partes buenas | Cumplido (AC-06). La pérdida con dos ejecuciones a la vez es otra causa, que ya estaba decidida y no se aplicó. |
| ◐ Parcial | 7. Números y colores de Revisar y Resultados | Ya no hay cuenta doble, y la carpeta solo se abre sola si todo salió bien. Pero «0 convertidos» vuelve tras guardar Ajustes, aparece «5» frente a «1 de 6», y «Conservado» sale en naranja (review.py:58). |
| ◐ Parcial | 8. Avisar cuando el resultado puede engañar a la IA | ADR-0054 existe, y hay avisos de ecuaciones, de celdas combinadas en Word y de Unir. Pero un logo apaga el filtro, y un resultado vacío se presenta como éxito. |
| ✅ Resuelto | 9. Ajustes siempre cabe en la pantalla | Hay capturas a 1366×768 en Qt. En flet falta una señal de que el contenido sigue más abajo (F3-10, baja). |
| ✅ Resuelto | 10. Una tecla o un clic sin querer no borra trabajo | Hay una regla de teclado común, Deshacer y regreso al paso 1 con aviso. Detalles: Deshacer sobrevive a un cambio de herramienta (F1-08) y el foco no se ve (F2-01). |
| ◐ Parcial | Decisión: artículo por defecto en páginas web | En el código, sí (settings.py:17). El README.es.md:223 dice lo contrario, y el resumen puede decir «Artículo» de una página que se convirtió completa. |
| ✅ Resuelto | Decisión: archivo vacío = falló con su razón | Cumplido para la entrada. Falta extenderlo al resultado vacío (decisión nueva). |
| ◐ Parcial | Decisión: reportar en la comunidad o por correo | report.how y unexpected_error cumplen. details_copied todavía manda a /issues (es.toml:512, en.toml:511). |
| ⏳ Pendiente | Decisión: firmar los instaladores cuando SignPath esté listo | Escrito en la enmienda de ADR-0037. Espera a un tercero; es lo previsto. |
| ◐ Parcial | Decisión: ADR para el texto oculto de los PDF | ADR-0054 existe y se aplica. Su regla («cualquier imagen protege») es demasiado amplia y necesita una enmienda. |

## 3. Lo que hay que proteger

Las fortalezas que ninguna mejora debe romper:

- Todo ocurre en el computador de la persona: sin registros, sin telemetría, sin red propia.
- Los originales nunca se modifican, y las escrituras son atómicas y no siguen enlaces.
- Las bombas zip se detectan desde el índice, y el proceso de conversión aislado tiene límites que siguen el avance real.
- La regla «archivo vacío = falló con su razón»: es el modelo para el resultado vacío.
- Dividir conserva las partes buenas, y Cancelar nunca es un error.
- La carpeta de resultados solo se abre sola cuando todo salió bien.
- Un presentador compartido: un arreglo llega a las tres ventanas a la vez.
- Cada error trae su motivo y su paso siguiente, en dos idiomas.
- Tablas de PDF y ecuaciones como LaTeX; el modo artículo para páginas web.
- El instalador por usuario, sin permisos de administrador, que describe cada app con franqueza.
- La paleta común con prueba de contraste, y los estados dichos también con palabras.
- La costumbre de decidir por escrito (ADR) y de aprender de cada auditoría.

## 4. Las once mejoras recomendadas

Ordenadas por valor para el cliente final frente al esfuerzo. Marca tu decisión en la última columna.

| # | Mejora | Por qué le importa a la persona | Esfuerzo | ¿Me acojo? |
| --- | --- | --- | --- | --- |
| 1 | **Si el resultado sale vacío, decir «falló» y explicar qué hacer** | Hoy la persona entrega a su IA un archivo en blanco que ClearMD llamó «convertido». Es tu regla del archivo vacío, aplicada al resultado, en las tres herramientas. | pequeño | ☐ Sí ☐ No |
| 2 | **Unir en el orden en que una persona cuenta: 1, 2, 3… 10** | Un libro unido no debe quedar desordenado sin que nadie lo vea. | pequeño | ☐ Sí ☐ No |
| 3 | **Que «Copiar Detalles» lleve a la comunidad o al correo** | Lo subo desde el puesto 7: incumple una decisión tuya y es una línea. Sin esto, quien no tiene cuenta no reporta. | pequeño | ☐ Sí ☐ No |
| 4 | **Cumplir «abrir un resultado no descarga nada», también en Unir, con marcas legibles** | La promesa nueva de la 2.12 debe ser cierta, o hay que dejar de hacerla. | medio | ☐ Sí ☐ No |
| 5 | **Mostrar completo el «qué hacer» de cada archivo** | Un consejo cortado en «Quít…» no ayuda. | medio | ☐ Sí ☐ No |
| 6 | **Que Dividir nunca diga «todo bien» si faltan partes** | Primero las medidas baratas que ya decidiste en la tercera auditoría: barrer solo temporales viejos y fallar si falta una parte. | pequeño | ☐ Sí ☐ No |
| 7 | **Que un logo no apague el filtro de texto invisible (enmendar ADR-0054)** | Casi toda carta oficial tiene membrete; ahí una orden escondida llega entera a la IA. | pequeño | ☐ Sí ☐ No |
| 8 | **No cambiar lo que la persona escribió: notas cortas, código al unir, CSV con comillas** | «Sí» y «¿Qué?» llegan como símbolos raros. Y las notas de la versión prometen lo contrario. | pequeño | ☐ Sí ☐ No |
| 9 | **PDF: listas numeradas y membrete fuera de las frases (enmendar ADR-0030)** | Son los documentos más comunes: cartas de dos páginas y requisitos numerados. | medio | ☐ Sí ☐ No |
| 10 | **Que cifras, colores y consejos nunca se contradigan** | «5 listos» y «1 de 6», «Conservado» en naranja, «0 convertidos» tras un error y «divídelo» sin salida. Se puede aceptar por partes. | pequeño | ☐ Sí ☐ No |
| 11 | **Justo después: que el foco del teclado se vea en Qt y flet** | Lo añado porque C2 lo dejó fuera. Quien usa teclado puede borrar un archivo sin verlo marcado, en la ventana que se recomienda para la accesibilidad. | pequeño | ☐ Sí ☐ No |

Los códigos de cada mejora (por ejemplo, B1-01) llevan a los hallazgos de la sección 8:

- **1.** B1-03, B3-05, B5-01, F5-11
- **2.** B1-04
- **3.** B5-04, F4-02, F5-02
- **4.** B2-01, B2-02, B3-06
- **5.** F3-01, F5-01, F2-03
- **6.** B1-01
- **7.** B3-04
- **8.** B5-03, B3-11, C-1, B1-07, B1-05
- **9.** B3-01, B3-02, B3-03
- **10.** F3-04, F5-04, F3-06, B5-08, F1-01, B1-02
- **11.** F2-01, F2-02, F2-09

## 5. Lo que no conviene hacer

Propuestas que surgieron en las juntas y que, según la conciliadora, **añadirían complejidad o romperían algo**:

- No subir el tope de 250 MB de Dividir sin enmendar ADR-0015 y ADR-0010, aplicar la lectura segura y tener un tope de memoria en Windows. Ahora, solo cambiar el consejo.
- No sacar Imágenes ni Resumen del paso 1 para llevarlos a Ajustes (F5-05): contradice la spec 009 AC-10 y ADR-0031 y ADR-0033. Plegarlos dentro del paso 1 sí.
- No «afinar» el filtro de texto invisible sin enmendar antes ADR-0054: el código cumple su texto literal.
- No quitar el membrete en documentos de menos de 4 páginas sin enmendar ADR-0030.
- No poner un candado por carpeta antes de las dos medidas baratas que ya decidió la tercera auditoría.
- No añadir un ajuste de tamaño de texto sin enmendar ADR-0012 (F2-07).
- No dar a la ayuda de la terminal el idioma del sistema (ADR-0017): usar el idioma que el instalador ya escribió en los ajustes.
- No quitar markitdown sin enmendar ADR-0004, ni empezar eso antes de la puerta de salida común.
- No aplicar a todos los formatos el escape ilegible de hoy, ni aflojarlo sin el lector de referencia (ADR-0023).
- No quitar los nombres de archivo del resultado unido (ADR-0046): solo decirlo en Revisión.
- No mantener vivo el proceso de conversión para ganar tiempo de arranque (decisión del dueño): usar importaciones diferidas.
- No confirmar Cancelar (decisión del dueño): durante la conversión, solo dejar Cancelar visible.
- No renombrar OutputMD, OutputSep ni OutputUnif sin una migración.
- No tocar la comprobación de OneDrive sin probarla en un Windows real.
- No subir una gravedad porque varios auditores vieron el mismo hecho.

## 6. Desacuerdos que quedan abiertos

- Gravedad de «Copiar Detalles» (alta para F4 y F5, media para C1): RESUELTO. La gravedad queda en media, porque no se pierde nada. La prioridad sube al puesto 3: incumple una decisión tuya y se arregla con una línea.
- Atajo de la Línea de Comandos (alta para B5, media para F4 y C1): RESUELTO en media. Solo afecta a la edición completa.
- Candado por carpeta (C1 lo quiere primero): RESUELTO a favor de la tercera auditoría. Primero se barren solo los temporales viejos y se falla si falta una parte. El candado viene después, si hace falta.
- Tope de 250 MB en Dividir (B1 pide 2 GB): RESUELTO. Ahora solo se cambia el consejo. Subir el tope exige enmendar ADR-0015 y ADR-0010, la lectura segura y un tope de memoria en Windows (B2-03).
- Opciones del paso 1 (F5-05 las manda a Ajustes): RESUELTO. Se pliegan dentro del paso 1 y cambia el título. No se sacan del paso 1 (spec 009 AC-10, ADR-0031 y ADR-0033).
- Escapar más (B2) frente a escapar legible (B3): RESUELTO. Una sola puerta de salida, mínima y legible, probada con un lector de Markdown real, sin escapar dos veces en Unir.
- Resultado vacío = «falló»: ABIERTO, lo confirmas tú. Recomiendo que sí: es tu misma regla del archivo vacío, aplicada al resultado.
- Texto invisible con logo (B3-04): ABIERTO, lo decides tú. El código cumple ADR-0054 al pie de la letra; para arreglarlo hay que enmendar la ADR. Recomiendo enmendarla.
- Membrete en PDF de 2-3 páginas (B3-02): ABIERTO, lo decides tú. Hay que enmendar ADR-0030. Recomiendo hacerlo con la condición de B1: solo líneas idénticas en el mismo margen.
- Valor de F1-01 (alto para C1, medio para C2): RESUELTO. Gravedad alta y arreglo pequeño; entra en el puesto 10.
- Reemplazar markitdown en Word y PowerPoint (B4-02, B3-09): ABIERTO a largo plazo. Exige enmendar ADR-0004 y no es urgente.

## 7. Cómo trabajaron las juntas

La conciliadora también auditó a las juntas y a su debate:

### Junta Backend (B1-B5) — rigor 8,5/10

- **Lo que hizo bien:** Reprodujo casi todo con archivos sintéticos en el contenedor. Tres auditores llegaron por caminos distintos al resultado vacío y lo fusionaron bien, sin subir la gravedad. B2 probó el filtro de salida con formas raras y no solo con la simple. B1 encontró la pérdida de partes con dos ejecuciones a la vez. Citó los ADR en casi todos los hallazgos.
- **Lo que no vio:** C-1 (lo comprobé yo): el problema de las notas cortas no se limita a 2 o 3 bytes. «¿Qué?» (5 bytes, cp1252) sale «쯈u鼈». La prueba pedida («Sí», «Año») sigue sin ser el caso más difícil. C-3: B1-01 no es un hallazgo nuevo. La tercera auditoría ya había decidido dos medidas baratas (no contar como éxito una parte que falta y barrer solo temporales viejos), y nunca se aplicaron: output_files.py:135-154 sigue borrando todos los temporales sin mirar su edad. Nadie lo dijo.
- **Donde se excedió:** B1-02 propone un límite de 2 GB para Dividir sin decir que la tercera auditoría lo condicionó a enmendar ADR-0015 y ADR-0010 y a aplicar antes la lectura segura. B3-04 dice «afinar, no revertir» ADR-0054, pero la línea 24 de esa ADR dice literalmente que, en una página con imagen, el texto invisible se queda: hace falta enmendarla. B4-02 propone quitar markitdown, lo que exige enmendar ADR-0004.

### Junta Frontend (F1-F5) — rigor 8/10

- **Lo que hizo bien:** F1 reprodujo con guiones los errores de estado (el «0 convertidos» tras guardar Ajustes, la casilla ignorada). F2 dibujó el foco sin pantalla y mostró que no cambia nada. F3, F4 y F5 se apoyaron en capturas concretas. F4 bajó su propia gravedad cuando faltaba evidencia, y F5 cuestionó con razón a F3-02 por no citar los ADR.
- **Lo que no vio:** Casi nada se ejecutó en flet ni en Windows: el velo de foco débil, las paradas de Tab y la altura a 125 % son cálculos o lecturas de código. Nadie hizo una prueba con un lector de pantalla real. Nadie revisó si las medidas resueltas en la tercera auditoría fuera del top 10 se habían aplicado.
- **Donde se excedió:** F5-05 propone dejar Imágenes y Resumen en Ajustes, lo que contradice la spec 009 AC-10 y ADR-0031 y ADR-0033 (la tercera auditoría ya dijo: plegarlas sí, sacarlas no). F2-07 pide un ajuste de tamaño de texto, que exige enmendar ADR-0012.

### Debate (ronda 2) — rigor 8/10

- **Lo que hizo bien:** Se repitió la regla «coincidir confirma el hecho, no la gravedad», y la mayoría la aplicó. Hubo fusiones limpias (resultado vacío, Copiar Detalles, motivo cortado) sin perder evidencia. Apareció una tensión útil entre seguridad y legibilidad del escape, y se resolvió con una sola puerta de salida.
- **Lo que no vio:** Casi nadie miró las decisiones del dueño como lista de control. Por eso nadie vio que el candado barato de la tercera auditoría seguía pendiente.
- **Donde se excedió:** F4 y F5 sostuvieron «alta» para Copiar Detalles en parte porque tres lo vieron. Algunos apoyos se dieron sin volver a comprobar, marcados reverified=false; eso está bien dicho, pero suma volumen.

### Conciliador 1 (verificación) — rigor 8,5/10

- **Lo que hizo bien:** Reprodujo nueve hechos clave en el contenedor. Corrigió gravedades con razones, como B4-01 medido en el peor caso. Encontró el matiz del código de salida (2 para un archivo inexistente, 0 para uno no admitido). Mantuvo las fusiones con evidencia.
- **Lo que no vio:** En B3-02 y B1-02 omitió las citas de ADR-0030 y ADR-0015/0010 que los auditores sí daban, así que sus recomendaciones parecen sin condiciones. Recomendó el candado por carpeta primero, contra lo que resolvió la tercera auditoría. La lista es muy larga (47 grupos) para que el dueño la lea.
- **Donde se excedió:** Ninguna recomendación contradice en silencio una decisión del dueño, salvo el orden del candado (B1-01).

### Conciliador 2 (valor) — rigor 7,5/10

- **Lo que hizo bien:** Prosa clara, con ejemplos que una persona entiende. Criterio explícito: primero lo que hace que la IA reciba algo falso o vacío. Rechazó con razón mover opciones del paso 1 sin enmendar los ADR y dejar el ajuste de texto para después.
- **Lo que no vio:** Dejó fuera del top 10 la accesibilidad del foco, aunque él mismo dice que va justo después. El puesto 10 junta seis problemas distintos, lo que hace difícil aceptarlo o rechazarlo por partes. No marcó que los puestos 6 y 9 necesitan enmendar ADR-0054 y ADR-0030.
- **Donde se excedió:** Puso «Copiar Detalles» en el puesto 7 aunque incumple una decisión explícita del dueño y se arregla con una línea. Por doctrina, lo subo.

## 8. Hallazgos verificados

Son 26 hallazgos, ordenados por gravedad. **Veredicto:** ✅ confirmada · ◐ parcialmente cierta · ✖ refutada.

| Gravedad | Valor para el usuario | Esfuerzo | Veredicto | Hallazgo |
| --- | --- | --- | --- | --- |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [1. Un resultado vacío se cuenta como «convertido»](#h1) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [2. La promesa «nada en un resultado descarga algo» no se cumple en formas raras, y Unir no pasa por el filtro](#h2) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [3. El «qué hacer» de cada archivo queda cortado en Revisar y Resultados; en flet solo se lee con el ratón](#h3) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [4. Unir una carpeta ordena los capítulos 1, 10, 11, 2, 3](#h4) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [5. Dos ClearMD sobre la misma carpeta pierden partes de Dividir y dicen «todo bien»](#h5) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [6. Un logo pequeño apaga el filtro de texto invisible](#h6) |
| 🔴 Alta | medio | pequeño | ✅ Confirmada | [7. Tras un error, guardar Ajustes cambia Resultados a «0 convertidos»](#h7) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [8. PDF: listas numeradas pegadas y membrete dentro de las frases en documentos de 2-3 páginas](#h8) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [9. En Qt y flet el foco del teclado no se ve](#h9) |
| 🟠 Media | alto | pequeño | ✅ Confirmada | [10. «Copiar Detalles» manda a GitHub Issues y borra la opción del correo](#h10) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [11. Las notas muy cortas de Windows salen en caracteres asiáticos](#h11) |
| 🟠 Media | medio | medio | ✅ Confirmada | [12. Tras «Dividir los PDF grandes», la casilla «Mantener» no manda y los valores temporales se guardan](#h12) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [13. Unir cambia el código y una comilla de pulgadas desbalancea un CSV al dividir](#h13) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [14. Cifras, colores y etiquetas que se contradicen](#h14) |
| 🟠 Media | alto | medio | ✅ Confirmada | [15. La App Moderna con lector de pantalla: nombres internos y nada se anuncia](#h15) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [16. Instalador: atajo de terminal que no funciona, licencia en inglés y capturas viejas](#h16) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [17. El README dice cosas que no son verdad](#h17) |
| 🟠 Media | medio | medio | ✅ Confirmada | [18. En Elegir la lista tiene poco espacio y el título «Los Resultados Van» está incompleto](#h18) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [19. Una ventana del explorador por carpeta y rutas cortadas por el final](#h19) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [20. Bienvenida e Inicio no dicen para qué sirve; el idioma activo no se marca](#h20) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [21. El consejo «divídelo» para un PDF de más de 250 MB lleva a Dividir, que lo rechaza](#h21) |
| 🟠 Media | medio | medio | ◐ Parcial | [22. El tiempo de un PDF comprimido se estima corto y el primer tercio pasa sin avance](#h22) |
| 🟠 Media | medio | medio | ◐ Parcial | [23. Accesibilidad secundaria: avisos ocultos en Inicio, contrastes mezclados, altura mínima, Tab por fila](#h23) |
| ⚪ Baja | medio | medio | ◐ Parcial | [24. Fidelidad y robustez menores: títulos solos al dividir, Excel, Word, PowerPoint, duplicados, rutas largas](#h24) |
| ⚪ Baja | bajo | pequeño | ◐ Parcial | [25. Empaquetado y privacidad menores: flet por pip, alertas de vulnerabilidades, huecos del ocultador, pesos](#h25) |
| ⚪ Baja | bajo | pequeño | ✅ Confirmada | [26. Detalles: glosario, «Esperando tu decisión» sin decisión, controles sin acción, Ctrl+0, terminal en inglés, documentos de comunidad](#h26) |

<a id="h1"></a>

### 8.1 Un resultado vacío se cuenta como «convertido»

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B1-03, B3-05, B5-01, F5-11*

- **Lo que siente la persona:** «Me dijo que se convirtió, se lo pasé a la IA y me dijo que el archivo estaba vacío.»
- **Recomendación:** Si el Markdown queda sin texto tras la limpieza, marcarlo como «falló» con su razón y su paso siguiente (escaneado: pasarlo antes por un programa de reconocimiento de texto; sin contenido; solo texto oculto). La nota de «escaneado» se calcula antes de la limpieza. Vale también para cada parte de Dividir y cada documento de Unir. Lo debe confirmar el dueño, porque extiende su regla del archivo vacío.
- **Comprobación de la conciliadora:** C1 lo reprodujo: PDF de 2 páginas en blanco, .md de 1 byte, «1 convertido», código 0. Lo acepto. Aclaro que el resumen sí muestra un aviso, pero el titular dice «El documento se convirtió».

<a id="h2"></a>

### 8.2 La promesa «nada en un resultado descarga algo» no se cumple en formas raras, y Unir no pasa por el filtro

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B2-01, B2-02, B3-06*

- **Lo que siente la persona:** «Me prometía que era seguro abrirlo, y quien me lo mandó supo que lo abrí.»
- **Recomendación:** Una sola puerta de salida para todo el Markdown (Convertir, Dividir, Unir), probada con un lector de Markdown real como referencia y con formas raras. En el mismo trabajo, cambiar las marcas ilegibles por otras legibles, sin escapar dos veces lo ya escapado. Hasta entonces, no prometer «en todos los formatos».
- **Comprobación de la conciliadora:** C1 reprodujo dos formas que pasan intactas y el bypass de Unir. ADR-0023 se respeta: cambia la forma del escape, no la garantía.

<a id="h3"></a>

### 8.3 El «qué hacer» de cada archivo queda cortado en Revisar y Resultados; en flet solo se lee con el ratón

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · F3-01, F5-01, F2-03*

- **Lo que siente la persona:** «Dice que tiene contraseña y “Quít…”, y no sé qué hacer.»
- **Recomendación:** El motivo completo dentro de la fila (dos o tres líneas), desde un componente compartido por las tres ventanas, sin preseleccionar ninguna fila. En flet, flechas para moverse entre filas.
- **Comprobación de la conciliadora:** Código visto por C1 y tres auditores (file_list.py:166-168).

<a id="h4"></a>

### 8.4 Unir una carpeta ordena los capítulos 1, 10, 11, 2, 3

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B1-04*

- **Lo que siente la persona:** «La IA leyó el capítulo 10 justo después del 1.»
- **Recomendación:** Orden natural (los números como números) en todo listado que defina un orden de salida. Respeta ADR-0046.
- **Comprobación de la conciliadora:** C1 lo reprodujo.

<a id="h5"></a>

### 8.5 Dos ClearMD sobre la misma carpeta pierden partes de Dividir y dicen «todo bien»

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B1-01*

- **Lo que siente la persona:** «Dividí un libro, me dijo que todo salió bien, y faltaba la mitad.»
- **Recomendación:** Primero, las medidas baratas que ya decidió la tercera auditoría: barrer solo los temporales viejos y fallar si falta una parte esperada. El candado con aviso, solo si eso no basta.
- **Comprobación de la conciliadora:** Lo comprobé: sweep_temporary_files (output_files.py:135-154) borra los temporales sin mirar su edad. Era una medida decidida y no aplicada (C-3).

<a id="h6"></a>

### 8.6 Un logo pequeño apaga el filtro de texto invisible

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B3-04*

- **Lo que siente la persona:** «La IA leyó una orden escondida en mi carta con membrete.»
- **Recomendación:** Enmendar ADR-0054: solo una imagen que cubre buena parte de la página protege el texto invisible. Probar con un logo pequeño, una imagen grande transparente y una fuera de la página.
- **Comprobación de la conciliadora:** Lo comprobé: hidden.py:24-38 da por protegida la página ante cualquier imagen, y ADR-0054 línea 24 dice exactamente eso. El código cumple la ADR; lo que hay que cambiar es la ADR.

<a id="h7"></a>

### 8.7 Tras un error, guardar Ajustes cambia Resultados a «0 convertidos»

*🔴 Alta · valor medio · esfuerzo pequeño · ✅ Confirmada · F1-01*

- **Lo que siente la persona:** «Decía 2 de 3; cambié el tema y ahora dice 0.»
- **Recomendación:** Guardar en la sesión los datos de la parada y redibujar desde ellos. Probar con un cambio de idioma y de tema.
- **Comprobación de la conciliadora:** C1 revisó el código (reset.py, preferences.py).

<a id="h8"></a>

### 8.8 PDF: listas numeradas pegadas y membrete dentro de las frases en documentos de 2-3 páginas

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B3-01, B3-02, B3-03*

- **Lo que siente la persona:** «Mi carta de dos páginas tiene el membrete en medio de una frase.»
- **Recomendación:** Reconocer listas «1.», «a)». Para documentos cortos, enmendar ADR-0030 («menos de 4 páginas conserva todo»): quitar solo líneas idénticas en el mismo margen y nunca pegar un margen a un párrafo.
- **Comprobación de la conciliadora:** Código visto por C1 (items.py, running.py:14). La parte de 2-3 páginas necesita la enmienda de ADR-0030, que C1 no mencionó.

<a id="h9"></a>

### 8.9 En Qt y flet el foco del teclado no se ve

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · F2-01, F2-02, F2-09*

- **Lo que siente la persona:** «No sé dónde estoy y borré un archivo sin verlo marcado.»
- **Recomendación:** Un foco propio por tipo de control, distinto del de «última herramienta usada», y una prueba que dibuje cada control con y sin foco.
- **Comprobación de la conciliadora:** Qt revisado por C1 (stylesheet.py). Lo de flet viene del código, no medido en pantalla.

<a id="h10"></a>

### 8.10 «Copiar Detalles» manda a GitHub Issues y borra la opción del correo

*🟠 Media · valor alto · esfuerzo pequeño · ✅ Confirmada · B5-04, F4-02, F5-02*

- **Lo que siente la persona:** «Quería avisar del error y me pidió crear una cuenta; el correo ya no aparece.»
- **Recomendación:** Usar {report} en details_copied y añadir una prueba que falle si «/issues» aparece en el catálogo. Revisar también el formulario de errores.
- **Comprobación de la conciliadora:** Lo comprobé: es.toml:512 y en.toml:511 son las únicas líneas con /issues. La gravedad es media, pero la prioridad es alta: incumple una decisión del dueño.

<a id="h11"></a>

### 8.11 Las notas muy cortas de Windows salen en caracteres asiáticos

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B5-03, B3-11, C-1*

- **Lo que siente la persona:** «Escribí “¿Qué?” y la IA recibió símbolos raros.»
- **Recomendación:** Con pocos bytes, preferir cp1252 y exigir más longitud antes de aceptar codificaciones asiáticas o UTF-16 sin BOM. Probar con «Sí», «Año», «¿Qué?» y «Café». Corregir ya las notas de la versión.
- **Comprobación de la conciliadora:** Lo reproduje: «Sí» da «叭», «¿Qué?» da «쯈u鼈», y «Café», «José;Bogotá;Medellín» y «Canción…» salen bien.

<a id="h12"></a>

### 8.12 Tras «Dividir los PDF grandes», la casilla «Mantener» no manda y los valores temporales se guardan

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · F1-02, F1-04, F1-05*

- **Lo que siente la persona:** «Le dije que mantuviera mis archivos y me puso otros.»
- **Recomendación:** Que la casilla mande. Guardar los valores de esta tarea fuera de los ajustes que van al disco. Que el aviso diga lo que pasó.
- **Comprobación de la conciliadora:** Lo comprobé: tools.py reemplaza s.settings en memoria y _give_back repone la lista sin mirar la casilla. Contradice el AC-05 de la 039.

<a id="h13"></a>

### 8.13 Unir cambia el código y una comilla de pulgadas desbalancea un CSV al dividir

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B1-07, B1-05*

- **Lo que siente la persona:** «El código que llegó a la IA estaba cambiado; una parte tenía casi todo el CSV.»
- **Recomendación:** Renumerar solo notas al pie con definición y nunca dentro de código. Encontrar las filas del CSV con el lector estándar.
- **Comprobación de la conciliadora:** C1 reprodujo los dos.

<a id="h14"></a>

### 8.14 Cifras, colores y etiquetas que se contradicen

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F3-04, F5-04, F3-06, B5-08*

- **Lo que siente la persona:** «Dice 5 y cuenta 6; todo salió bien y está en naranja.»
- **Recomendación:** El progreso cuenta solo lo que se escribe. El tono del contador sale de la regla de sus filas. flet pinta la advertencia como Qt. La etiqueta HTML dice lo que se hizo.
- **Comprobación de la conciliadora:** Lo comprobé: stat() usa WARNING por defecto (review.py:58).

<a id="h15"></a>

### 8.15 La App Moderna con lector de pantalla: nombres internos y nada se anuncia

*🟠 Media · valor alto · esfuerzo medio · ✅ Confirmada · F2-05*

- **Lo que siente la persona:** «Oigo “inputs” en inglés y nunca me entero de que terminó.»
- **Recomendación:** Nombres desde el catálogo, el paso actual marcado y una prueba manual con NVDA antes de seguir recomendándola para lectores.
- **Comprobación de la conciliadora:** Literal «inputs» comprobado por C1.

<a id="h16"></a>

### 8.16 Instalador: atajo de terminal que no funciona, licencia en inglés y capturas viejas

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B5-02, F4-11, F4-05, F4-08*

- **Lo que siente la persona:** «Escribí lo que decía y Windows no reconoce el comando.»
- **Recomendación:** Texto del atajo en los dos idiomas y que funcione sin PATH. Sin página de licencia en la edición liviana. «Instalación Terminada». Capturas del instalador en cada publicación.
- **Comprobación de la conciliadora:** Lo comprobé en clearmd.iss: líneas 53, 94, 245 y 254.

<a id="h17"></a>

### 8.17 El README dice cosas que no son verdad

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B5-05, F4-07, B2-03*

- **Lo que siente la persona:** «El README dice una cosa y el programa hace otra.»
- **Recomendación:** Corregir el valor por defecto de --html, decir «solo en Linux» para el tope de memoria, quitar «en construcción» y poner el aviso de Windows junto al botón.
- **Comprobación de la conciliadora:** Lo comprobé: README.es.md:223 dice «la página completa (por defecto)» y settings.py:17 usa «article».

<a id="h18"></a>

### 8.18 En Elegir la lista tiene poco espacio y el título «Los Resultados Van» está incompleto

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · F3-02, F5-05, F3-03*

- **Lo que siente la persona:** «Casi no veo mis archivos.»
- **Recomendación:** Título «Dónde Guardar los Resultados». Plegar Imágenes y Resumen dentro del paso 1, nunca moverlos a Ajustes (spec 009 AC-10, ADR-0031 y ADR-0033).
- **Comprobación de la conciliadora:** Catálogo es.toml:594 confirmado por varios.

<a id="h19"></a>

### 8.19 Una ventana del explorador por carpeta y rutas cortadas por el final

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F5-03, F3-05, F5-06*

- **Lo que siente la persona:** «Se me abrieron diez ventanas, y todas las filas empiezan igual.»
- **Recomendación:** Con varias carpetas, no abrir nada solo y que el botón diga cuántas son. Mostrar el nombre de la carpeta o recortar la ruta por el centro.
- **Comprobación de la conciliadora:** Código revisado por C1 y dos auditores.

<a id="h20"></a>

### 8.20 Bienvenida e Inicio no dicen para qué sirve; el idioma activo no se marca

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F4-01, F5-09, F4-03*

- **Lo que siente la persona:** «No sé qué es Markdown ni qué idioma quedó.»
- **Recomendación:** Una frase de propósito sobre la IA. Marcar el idioma activo, sin la línea «cámbialo en Ajustes».
- **Comprobación de la conciliadora:** Catálogo revisado por C1.

<a id="h21"></a>

### 8.21 El consejo «divídelo» para un PDF de más de 250 MB lleva a Dividir, que lo rechaza

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B1-02*

- **Lo que siente la persona:** «Me dijo que lo dividiera y Dividir me dijo lo mismo.»
- **Recomendación:** Ahora, solo cambiar el consejo. Subir el tope exige enmendar ADR-0015 y ADR-0010 y aplicar antes la lectura segura y un tope de memoria en Windows.
- **Comprobación de la conciliadora:** C1 lo reprodujo. El esfuerzo baja a pequeño porque solo se cambia el texto.

<a id="h22"></a>

### 8.22 El tiempo de un PDF comprimido se estima corto y el primer tercio pasa sin avance

*🟠 Media · valor medio · esfuerzo medio · ◐ Parcial · B4-01, B4-04*

- **Lo que siente la persona:** «Decía un segundo y tardó veinte; pensé que se había colgado.»
- **Recomendación:** Contar páginas dentro del proceso de conversión (ADR-0015) e informar avance en la primera pasada.
- **Comprobación de la conciliadora:** Medición del auditor, en el peor caso.

<a id="h23"></a>

### 8.23 Accesibilidad secundaria: avisos ocultos en Inicio, contrastes mezclados, altura mínima, Tab por fila

*🟠 Media · valor medio · esfuerzo medio · ◐ Parcial · F1-03, F2-04, F2-06, F2-07, F2-08*

- **Lo que siente la persona:** «Con la pantalla al 125 % no veo el botón Siguiente.»
- **Recomendación:** Que Inicio muestre mensajes, ampliar la prueba de contraste, bajar el alto mínimo y una sola parada de Tab para la lista. El ajuste de tamaño de texto, solo si se enmienda ADR-0012.
- **Comprobación de la conciliadora:** Cálculos y lectura de código, sin prueba en Windows.

<a id="h24"></a>

### 8.24 Fidelidad y robustez menores: títulos solos al dividir, Excel, Word, PowerPoint, duplicados, rutas largas

*⚪ Baja · valor medio · esfuerzo medio · ◐ Parcial · B3-07, B3-08, B3-09, B1-06, B1-08, B1-09, B1-10*

- **Lo que siente la persona:** «La IA no vio los comentarios de mi contrato.»
- **Recomendación:** Un aviso en el resumen por cada pérdida conocida, como ya hace ODT. Reemplazar markitdown solo con una enmienda de ADR-0004.
- **Comprobación de la conciliadora:** No reproducido por los conciliadores.

<a id="h25"></a>

### 8.25 Empaquetado y privacidad menores: flet por pip, alertas de vulnerabilidades, huecos del ocultador, pesos

*⚪ Baja · valor bajo · esfuerzo pequeño · ◐ Parcial · B2-04, B2-05, B2-06, B2-07, B2-08, B4-02, B4-03, B4-05, B4-06, B4-07*

- **Lo que siente la persona:** «Me dijeron que no usaba internet y lo primero que hizo fue descargar algo.»
- **Recomendación:** Que flet no se abra sin su cliente empaquetado. Revisar el lock en el CI. Ocultar subcarpetas. Decir en Unir que van los nombres de los archivos. Probar OneDrive en Windows antes de tocar nada.
- **Comprobación de la conciliadora:** El lanzamiento de flet sin FLET_VIEW_PATH lo comprobaron dos auditores. El resto es de los auditores.

<a id="h26"></a>

### 8.26 Detalles: glosario, «Esperando tu decisión» sin decisión, controles sin acción, Ctrl+0, terminal en inglés, documentos de comunidad

*⚪ Baja · valor bajo · esfuerzo pequeño · ✅ Confirmada · F5-07, F5-10, F1-06, F1-07, F1-08, F3-07, F3-08, F3-09, F3-10, F4-04, F4-06, F4-09, B5-06, B5-07, B5-09*

- **Lo que siente la persona:** «Pulso “Deseleccionar Todo” con la lista vacía y no pasa nada.»
- **Recomendación:** Llevar estas reglas al código compartido con una prueba de paridad, y un glosario de una palabra por idea.
- **Comprobación de la conciliadora:** Comprobados en código por varios auditores y por C1.

## 9. Los informes de cada auditor (tras el debate)

### Backend · Lógica y robustez — 7/10

Tras la ronda 2 mantengo la nota de 7/10 y mis diez hallazgos. Los otros auditores confirman de forma independiente el problema más repetido: un resultado vacío se cuenta como «convertido». B3 lo encontró en PDF, B5 en PDF escaneados y yo en PPTX, HTML y PDF en blanco. Es una sola regla que falta en el backend, no tres errores distintos. Volví a comprobar en el código y en el contenedor tres hallazgos ajenos que tocan mi lente. Unir copia un .md sin pasar por el filtro de salida (merging.py:99, B2-02). Las notas de Windows de 2 o 3 bytes siguen saliendo en caracteres chinos: 'Sí' da '叭' y 'Año' da 'A隳' (B5-03). Y el texto invisible queda protegido en cuanto la página tiene cualquier imagen (hidden.py:24-38, B3-04). Lo más grave de mi lente sigue siendo lo que el resumen no dice: partes perdidas cuando hay dos ventanas abiertas a la vez, un PDF grande que no se puede dividir aunque el mensaje dice «divídelo», capítulos desordenados en Unir y resultados vacíos presentados como éxito.

**Fortalezas que vio:**

- Las escrituras atómicas no siguen enlaces ni uniones (junctions) sembrados en ClearMD_Output (output_files.py).
- PartStage: las partes nuevas reemplazan el corte anterior solo cuando todas están listas. Repetir un Split de 3 partes como uno de 4 dejó exactamente 4 partes, sin restos.
- La cancelación se informa como cancelada en todas las etapas (nunca como error) y el resumen siempre se escribe.
- Los nombres que chocan (a.pdf y a.docx) se resuelven igual sin importar el orden, sin distinguir mayúsculas ni forma Unicode, y se recortan por bytes UTF-8.
- Un archivo de entrada vacío, dañado, cifrado o una bomba ZIP terminan en un fallo con una razón clara. Un PDF con solo contraseña de propietario se convierte, se divide y se une bien.
- La decodificación prueba cp1252 antes que el detector genérico, y cuando adivina lo dice en el resumen con un paso a seguir. Funciona bien desde unas 4 letras.
- Un worker por tarea, con límites de tiempo que se basan en el avance y límites de memoria medidos en el proceso hijo.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B1-01 | 🔴 Alta | medio | alta | Dos ClearMD a la vez sobre la misma carpeta pierden partes de Split en silencio |
| B1-02 | 🔴 Alta | medio | alta | Un PDF de más de 250 MB no se puede dividir, aunque el mensaje dice 'divídelo' |
| B1-03 | 🔴 Alta | pequeño | alta | Un resultado vacío se cuenta como 'convertido' (también en PDF escaneados y en Unir) |
| B1-04 | 🔴 Alta | pequeño | alta | Unir una carpeta ordena los capítulos 1, 10, 11, 2, 3 |
| B1-05 | 🟠 Media | pequeño | alta | Una comilla de pulgadas en un CSV rompe Dividir |
| B1-06 | 🟠 Media | medio | alta | Al agregar un archivo con el mismo nombre quedan resultados viejos duplicados |
| B1-07 | 🟠 Media | pequeño | alta | Unir cambia el código de los documentos ([^a-z] pasa a ser [^d1-a-z]) |
| B1-08 | 🟠 Media | medio | media | Split repite el nombre en la ruta y puede pasar el límite de 260 caracteres de Windows |
| B1-09 | 🟠 Media | pequeño | media | Los resultados se escriben sin fsync, y el modo incremental puede conservar para siempre uno roto |
| B1-10 | ⚪ Baja | pequeño | alta | La extensión engaña: 'Acta 12.05.2024' no se admite y un Word renombrado .pdf 'está dañado' |

<details><summary>Detalle técnico y evidencia</summary>

- **B1-01 — Dos ClearMD a la vez sobre la misma carpeta pierden partes de Split en silencio**
  - *Impacto:* Si la app se abre dos veces, o si se convierte en una ventana mientras se divide en otra, la segunda ejecución borra los archivos temporales de la primera. Split termina diciendo '1 dividido · 0 con error' aunque faltan cientos de partes. La IA recibe un documento incompleto y nadie avisa.
  - *Evidencia:* Reproducido: un PDF sintético de 600 páginas con `clearmd --split-pages 1 --keep both --overwrite` en segundo plano, y `clearmd --overwrite nota.txt` en bucle sobre la misma carpeta. Resultado: 357 de 600 partes y la salida '1 split · 0 skipped · 0 failed'. Causas: execution.py:_root_problem llama a sweep_temporary_files, que borra todos los temporales sin mirar quién los creó ni cuándo. PartStage.commit (part_stage.py:37) salta en silencio una parte preparada que ya no existe. No hay ningún bloqueo de instancia.
  - *Recomendación:* 1) Un archivo de bloqueo por ClearMD_Output, creado en exclusiva y con el PID, y un aviso sencillo: 'Otra ventana de ClearMD está trabajando en esta carpeta'. 2) Barrer solo los temporales viejos o de procesos muertos. 3) Que commit registre las partes que se borraron a propósito y falle si falta una parte esperada. Test: borrar una parte preparada antes del commit.
- **B1-02 — Un PDF de más de 250 MB no se puede dividir, aunque el mensaje dice 'divídelo'**
  - *Impacto:* Un libro escaneado o un informe con fotos supera fácilmente los 250 MB. Convertir lo omite y aconseja dividirlo. Pero la herramienta Dividir del mismo ClearMD lo rechaza igual: la persona llega a un callejón sin salida.
  - *Evidencia:* Un PDF de 260 MB (`truncate -s 260M`) con `clearmd --split-pages 50 --dry-run --lang es` da 'Omitido: ... demasiado grande (260 MB; límite 250 MB). Divídelo en archivos más pequeños.' y luego 'Nada que dividir.'. El límite Limits.max_file_size de scan_rules.py:file_rule se aplica a todas las herramientas. El texto está en es.toml:93 too_large.
  - *Recomendación:* Dar a Dividir PDF (por páginas o en partes) un límite propio, por ejemplo 2 GB, medido con un benchmark. Que el mensaje de Convertir lleve a Dividir con el número de partes sugerido. Test con un PDF de 300 MB.
- **B1-03 — Un resultado vacío se cuenta como 'convertido' (también en PDF escaneados y en Unir)**
  - *Impacto:* Una presentación vacía, una página web sin cuerpo, un PDF escaneado o un PDF cuyo texto quitó la limpieza dan un .md de 0 o 1 byte, y el resumen dice 'convertido'. La persona sube un archivo vacío a la IA. Al unir, aparece un 'Documento N de M' sin contenido. Tres auditores llegamos a lo mismo por caminos distintos (B3-05, B5-01).
  - *Evidencia:* vacia.pptx da 0 bytes y '4 convertidos · 0 con error', sin nota. vacia.html da 1 byte. Un PDF de 2 páginas en blanco da 1 byte y '1 convertido' con exit 0. En schemas/notes.py no existe un NoteKind para un resultado vacío, y execution.py:_convert_one escribe sin comprobar result.markdown.strip(). B3 reprodujo la nota falsa de 'escaneado' cuando la limpieza vacía las páginas.
  - *Recomendación:* Si el Markdown queda sin texto después de la limpieza, marcarlo como 'falló' con un código EMPTY_RESULT, no escribir el .md y explicar el motivo según el caso: 'son imágenes escaneadas; pásalo antes por un programa que reconozca texto (OCR)' o 'el documento no tiene contenido'. Hacer lo mismo por parte en Split y por documento en Unir. La nota de 'escaneado' debe calcularse antes de la limpieza. Tests: un PDF de una sola página en blanco, uno mixto (1 de 10 páginas con texto) y un PDF con solo espacios.
- **B1-04 — Unir una carpeta ordena los capítulos 1, 10, 11, 2, 3**
  - *Impacto:* Quien une 'Capítulo 1' a 'Capítulo 12' recibe un libro desordenado y ningún aviso. El Explorador de Windows le muestra 1, 2, 3, así que no puede preverlo.
  - *Evidencia:* Con 'Capitulo 1/2/3/10/11.txt' y `clearmd --merge markdown .` el orden queda 1, 10, 11, 2, 3. Causa: scan_rules.py:sorted_entries ordena con entry.name.casefold().
  - *Recomendación:* Usar orden natural (los números como números) en todos los listados que definen un orden de salida. Test con '2', '10', '02', 'Cap 1a' y nombres con tilde.
- **B1-05 — Una comilla de pulgadas en un CSV rompe Dividir**
  - *Impacto:* Una lista con '24" pulgadas' se divide mal: se piden 4 partes y salen 3, y una se queda con el 99 % de las filas. Puede no caber en la IA. Convertir el mismo CSV sí funciona.
  - *Evidencia:* Un CSV de 400 filas con `Monitor 3 24" pulgadas,103` y `--split-parts 4` da partes de 2, 2 y 398 líneas. Causa: text_cut.py:csv_rows alterna el estado de comillas con cualquier comilla, también en mitad de un campo.
  - *Recomendación:* Encontrar las filas con csv.reader, usando el separador ya detectado. Test con una comilla suelta, con ';' como separador y con un salto de línea dentro de comillas.
- **B1-06 — Al agregar un archivo con el mismo nombre quedan resultados viejos duplicados**
  - *Impacto:* Primero 'Reunión.txt' da 'Reunión.md'. Al agregar después 'Reunión.html', salen '(txt)' y '(html)', y el viejo 'Reunión.md' se queda. La IA recibe el mismo contenido dos veces.
  - *Evidencia:* Con `--changed .` después de agregar el .html, OutputMD contiene 'Reunión (html).md', 'Reunión (txt).md' y 'Reunión.md'. paths.py:resolve_names decide la etiqueta solo dentro del lote.
  - *Recomendación:* Al planear, retirar el resultado anterior del mismo original cuando cambie de nombre, en el mismo paso atómico, y decirlo en el resumen. Como mínimo, avisar. Test también del camino inverso.
- **B1-07 — Unir cambia el código de los documentos ([^a-z] pasa a ser [^d1-a-z])**
  - *Impacto:* Un manual o una tesis con código llega a la IA con el código alterado y sin aviso.
  - *Evidencia:* `[^0-9]` y `r"[^a-z]"` dentro de ```python salen como `[^d1-0-9]` y `[^d1-a-z]`. Causa: merging.py:88 _FOOTNOTE se aplica a todo el texto.
  - *Recomendación:* Renumerar solo las etiquetas que tienen definición `[^x]:` y nunca dentro de código. Test: código con [^...] junto a una nota al pie real.
- **B1-08 — Split repite el nombre en la ruta y puede pasar el límite de 260 caracteres de Windows**
  - *Impacto:* En carpetas profundas y con nombres largos, la división falla en un Windows sin rutas largas, con un mensaje genérico que no dice cuánto acortar.
  - *Evidencia:* split_target_for crea una carpeta con el nombre y part_name lo repite en cada parte; _fit limita solo cada componente a 200 bytes. No hay ningún cálculo de la ruta total. No lo probé en Windows.
  - *Recomendación:* Calcular la ruta más larga al planear y acortar el nombre de las partes, o avisar antes de empezar. Test en el CI de Windows.
- **B1-09 — Los resultados se escriben sin fsync, y el modo incremental puede conservar para siempre uno roto**
  - *Impacto:* Un corte de luz puede dejar un .md vacío con una fecha más nueva que el original. Con 'Reemplazar si el original cambió', ClearMD lo conserva sin avisar.
  - *Evidencia:* output_files.py:atomic_write_bytes no llama a os.fsync antes de os.replace, mientras que settings_store.py:49 sí lo hace. changes.py:13 compara solo fechas. Lo deduje del código, no reproduje el corte.
  - *Recomendación:* Llamar a fsync antes del replace. En modo 'changed', tratar un resultado vacío como cambiado (esto encaja con B1-03).
- **B1-10 — La extensión engaña: 'Acta 12.05.2024' no se admite y un Word renombrado .pdf 'está dañado'**
  - *Impacto:* Archivos con puntos en el nombre se omiten como no soportados. Un Word guardado como .pdf se informa como dañado, con un consejo que no lo arregla. Un CSV UTF-16 con BOM recibe el aviso de 'tuvo que adivinar'.
  - *Evidencia:* content_policy.py:19 `None if path.suffix`. 'contrato.PDF' (en realidad un DOCX) da 'parece estar dañado'. decode_source no mira el BOM UTF-16.
  - *Recomendación:* Mirar el contenido cuando la extensión no es conocida. Si el lector falla, mirar la firma y decir el tipo real. Reconocer el BOM UTF-16 sin adivinar.

</details>

### Backend · Seguridad y privacidad — 7/10

Tras el debate mantengo la nota de 7 y mis ocho hallazgos. La falla principal sigue siendo la misma: la promesa nueva de la 2.12.0, «nada en un resultado descarga ni ejecuta algo al abrirlo», se atraviesa con Markdown válido, y Unir en Markdown ni siquiera pasa por el filtro. Mis colegas encontraron dos fallas más dentro de mi lente, y las comprobé en el código. La primera: la protección contra texto oculto (ADR-0054) se apaga si la página tiene cualquier imagen, aunque sea un logo pequeño. Así, una instrucción escondida para la IA llega completa en el caso más común, el de una página con membrete (B3-04). La segunda: cuando dos ejecuciones trabajan sobre la misma carpeta, el barrido de temporales de una borra las partes de la otra, y la división termina como «correcta» con partes de menos (B1-01). Las dos rompen la promesa «lo que llega a tu IA es lo que tú ves». En privacidad, «Copiar Detalles» todavía manda a pegar el error en un foro público con cuenta (/issues). Eso contradice la decisión del dueño, y tres auditores lo vieron por separado. La base sigue siendo excelente y no debe perderse: bombas zip detectadas desde el índice, nada que siga enlaces, un proceso de conversión con límites reales, ningún registro y ninguna conexión a internet propia.

**Fortalezas que vio:**

- Las bombas zip se detectan desde el índice del archivo, sin descomprimir nada: tamaño total, proporción, número de entradas y tamaños declarados imposibles (use_cases/archive.py).
- Un proceso de conversión aislado con límites reales: un PDF bomba sintético de 3,8 MB se detuvo en 9 s con un mensaje amable, y el resto de la tanda siguió.
- Nada planta un enlace en la carpeta de salida: el barrido y las escrituras usan lstat, los temporales tienen nombre aleatorio y exclusivo, y os.replace sustituye el enlace en vez de seguirlo. Los originales se abren con O_NOFOLLOW (safe_files.py).
- LaTeX solo lee dentro de la carpeta del documento, sin enlaces. El lector XML propio rechaza DOCTYPE y entidades y limita tamaño y profundidad.
- No hay registros, telemetría ni código de red propio. Los ajustes se guardan de forma atómica y validada.
- El escape de texto (escaping.py) duplica primero la barra del propio documento, así que el texto de un tercero no puede anular un escape. Es una base correcta que debe conservarse aunque se haga más legible (B3-06).
- El modo artículo (por defecto) y el correo .eml convierten las imágenes remotas en texto.
- «Copiar detalles» oculta las rutas comunes antes de que la persona pegue el error, y le pide revisarlo.
- Cadena de suministro cuidada: acciones de CI fijadas por SHA, uv sync --locked, Trusted Publishing en PyPI, la regla de dos semanas y el cliente flet del ejecutable verificado con SHA-256.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B2-01 | 🔴 Alta | medio | alta | La garantía «nada en un resultado descarga ni ejecuta algo» se atraviesa con Markdown válido |
| B2-02 | 🟠 Media | pequeño | alta | Unir en Markdown copia el texto tal cual, sin la garantía de salida |
| B2-03 | 🟠 Media | medio | alta | En Windows no existe el «límite duro de memoria del sistema» que anuncia el README, y su prioridad está atada a SignPath |
| B2-04 | 🟠 Media | pequeño | alta | La ventana flet instalada desde PyPI descarga un programa de GitHub, y en Windows escucha en un puerto local sin autenticación |
| B2-05 | 🟠 Media | pequeño | alta | Nada avisa cuando una biblioteca nativa del lock tiene una vulnerabilidad conocida |
| B2-06 | ⚪ Baja | pequeño | alta | El ocultador de rutas deja ver carpetas en casos poco comunes |
| B2-07 | ⚪ Baja | pequeño | alta | Unir pone el nombre de cada archivo dentro del resultado que va a la IA, sin decirlo |
| B2-08 | ⚪ Baja | pequeño | baja | En Windows, la comprobación de enlaces en la salida podría rechazar carpetas de OneDrive |

<details><summary>Detalle técnico y evidencia</summary>

- **B2-01 — La garantía «nada en un resultado descarga ni ejecuta algo» se atraviesa con Markdown válido**
  - *Impacto:* Una persona convierte un .txt, un .csv, un cuaderno o una página web (en modo completo) que le envió un tercero, y abre el resultado en Obsidian, Typora o VS Code. El visor descarga una imagen remota, y el remitente se entera de que lo abrió, cuándo y desde dónde. El README y la AC-02 prometen lo contrario.
  - *Evidencia:* safe_output.py:22-31 reconoce imágenes con `!\[([^\]\n]*)\]` y un destino sin espacios. Estos casos volvieron de safe_output() con 0 cambios: `![a [b] c](http://evil.example/p.png)`, `![x][r]` + `[r]: http://...`, `![x](&#104;ttp://...)`, `![x](<http://.../a b.png>)`, un texto alternativo de dos líneas, `<div style="background:url(http://...)">`, `[t](jav&#x61;script:...)`. De punta a punta, n.txt, d.csv, probe.ipynb y p.html con --html full conservan las imágenes remotas, y markdown-it-py (commonmark) renderiza <img src=http://evil...>. Los tests (tests/acceptance/test_039_truth_and_care.py:59-81) solo usan la forma simple.
  - *Recomendación:* Cambiar el método, no solo los patrones. Hay dos caminos: neutralizar todo `![` y toda definición de referencia que no apunte a la carpeta de imágenes propia, o tokenizar con un parser CommonMark (markdown-it-py es Python puro) y reescribir imágenes, referencias, entidades y HTML con style o background. El test debe usar el parser como oráculo y un fuzz con todas estas formas, en todos los formatos. Hay que tratar `//host` como red.
- **B2-02 — Unir en Markdown copia el texto tal cual, sin la garantía de salida**
  - *Impacto:* Quien une varios .md descargados obtiene un archivo que, al abrirlo, carga imágenes remotas y HTML activo, aunque ClearMD promete que sus resultados no lo hacen.
  - *Evidencia:* merging.py:96-98: a un .md se le aplica cutter.read_text sin pasar por safe_output, que solo se aplica en worker child.py:115. Con a.md que contiene `![p](https://tracker.example/a.gif)` y `<img src=...>`, `clearmd --merge markdown a.md b.md` deja ambas líneas intactas en OutputUnif.
  - *Recomendación:* Una sola puerta de salida para toda escritura de Markdown, en Convertir, Dividir y Unir, con el filtro de B2-01 ya corregido, y un test que recorra las tres herramientas.
- **B2-03 — En Windows no existe el «límite duro de memoria del sistema» que anuncia el README, y su prioridad está atada a SignPath**
  - *Impacto:* En Windows, la plataforma principal del público, un archivo hostil solo se detiene por un muestreo cada 0,1 s. Una reserva grande puede congelar el equipo unos segundos antes de que ClearMD actúe.
  - *Evidencia:* README.md:58-59 promete «a hard cap from the OS». child.py:56-72 apply_memory_cap usa RLIMIT_AS y no hace nada sin el módulo resource (Windows). grep JobObject: nada. spec/roadmap.md:81-85 deja el Job Object dentro de 006b, que espera a SignPath.
  - *Recomendación:* Separar el Job Object (JOB_OBJECT_LIMIT_PROCESS_MEMORY + KILL_ON_JOB_CLOSE) de la firma. Mientras tanto, que el README diga «en Linux».
- **B2-04 — La ventana flet instalada desde PyPI descarga un programa de GitHub, y en Windows escucha en un puerto local sin autenticación**
  - *Impacto:* Quien instala `pip install "clearmd[flet]"`, como indica el README de PyPI, descarga en silencio un ejecutable de GitHub sin comprobación de checksum. Eso contradice «ClearMD never uses the internet». En Windows, otro programa del equipo puede conectarse al puerto local de la ventana.
  - *Evidencia:* packaging/pypi-readme.md:12 y :25. flet_desktop/__init__.py:309-331 descarga el cliente si no existe FLET_VIEW_PATH, y solo packaging/launch_flet.py:17-18 lo define. flet_socket_server.py:100-107 escucha por TCP en localhost en Windows, y handle_connection acepta cualquier conexión. SECURITY.md:3 dice «it opens no network connection».
  - *Recomendación:* Si clearmd-flet no encuentra el cliente empaquetado, que no lance la ventana sin permiso explícito y ofrezca clearmd-ttk. Ajustar el README de PyPI y SECURITY.md, y reportar el puerto a flet.
- **B2-05 — Nada avisa cuando una biblioteca nativa del lock tiene una vulnerabilidad conocida**
  - *Impacto:* PDFium, lxml y Pillow abren documentos de terceros con todos los permisos del usuario. Si publican un parche de seguridad, nadie se entera, y la regla de dos semanas lo retrasa aún más.
  - *Evidencia:* No hay pip-audit ni osv-scanner en .github/workflows. spec/roadmap.md:85 deja «an advisory check of uv.lock» dentro de 006b, que espera a SignPath. La regla de dos semanas (pyproject.toml:101-112) no distingue los arreglos de seguridad.
  - *Recomendación:* Análisis del lock (osv-scanner o pip-audit) en cada PR y cada semana, sin depender de SignPath, más una excepción escrita a la regla de dos semanas para parches de seguridad.
- **B2-06 — El ocultador de rutas deja ver carpetas en casos poco comunes**
  - *Impacto:* Un error raro puede mostrar en «Copiar detalles» nombres de carpetas (un paciente, un cliente) que la persona pega en un foro público. El riesgo es mayor mientras el mensaje mande a /issues (ver debate sobre B5-04, F4-02 y F5-02).
  - *Evidencia:* without_paths devolvió sin cambios `source:/srv/Pacientes/Juan Perez/x.pdf`, `~/Pacientes/...`, rutas relativas y nombres sin comillas. reset.py:42 pasa como nombres solo el archivo y su raíz. summary/content.py:156 no pasa ningún nombre.
  - *Recomendación:* Ocultar cada parte de la ruta de los archivos planeados, también las subcarpetas. Tratar `~` y una ruta precedida de `:` como comienzo de ruta, y añadir estos casos al test.
- **B2-07 — Unir pone el nombre de cada archivo dentro del resultado que va a la IA, sin decirlo**
  - *Impacto:* Los nombres de archivo suelen llevar datos personales, y quien une y sube el resultado a una IA los comparte, también en un comentario oculto.
  - *Evidencia:* merging.py:61-70: `<!-- ClearMD: {name} -->` y `*Document 1 of 2: a.md*`.
  - *Recomendación:* Decirlo en la pantalla de Revisión de Unir. Más adelante, opcionalmente, numerar sin nombres.
- **B2-08 — En Windows, la comprobación de enlaces en la salida podría rechazar carpetas de OneDrive**
  - *Impacto:* Si se confirma, quien tiene Documentos sincronizado con OneDrive vería «no es una carpeta real» al guardar junto a sus originales.
  - *Evidencia:* output_files.py:41-43 y tex/includes.py:55-58 tratan como enlace cualquier entrada con FILE_ATTRIBUTE_REPARSE_POINT. scan_rules.py:29-31 sí usa is_symlink e is_junction. No lo probé en Windows.
  - *Recomendación:* Probarlo en un Windows real con OneDrive. Si falla, decidir por st_reparse_tag (symlink y mount point).

</details>

### Backend · Fidelidad del contenido para la IA — 6,5/10

Después del debate mantengo el diagnóstico. ClearMD reconstruye muy bien lo difícil: tablas PDF, ecuaciones como LaTeX, páginas web sin menú ni cookies y límites claros al unir. Pero entre «lo que dice el documento» y «lo que lee la IA» hay fallas que nadie ve, y los colegas confirmaron varias por su cuenta. Las principales: las listas numeradas de un PDF quedan en un párrafo corrido; en los PDF de 2 o 3 páginas el membrete y el pie se cuelan en mitad de las frases; al dividir vuelven los encabezados que la conversión completa sí quitaba; el filtro de texto invisible se apaga con cualquier logo; y un resultado vacío se cuenta como «convertido». Añado dos fallas que los colegas me hicieron ver y que reproduje en esta ronda. La primera: las notas muy cortas de Windows («Sí», «Año») llegan a la IA en caracteres chinos, aunque la 2.12.0 promete que no pasa. La segunda: Unir altera el código que contiene «[^…]» (eso queda en el debate, porque el hallazgo es de B1). El debate también deja ver una tensión que hay que resolver con un solo diseño. B2 pide escapar más (el filtro de seguridad deja pasar formas raras en .txt, .csv y otros formatos que se copian casi tal cual) y yo pido escapar de forma más legible (en PDF, Word y Excel la IA lee «&#91;12&#93;» y «juan\_perez»). Las dos cosas caben en una sola puerta de salida, igual para todos los formatos, que escape lo mínimo y con marcas legibles. Nota: 6,5.

**Fortalezas que vio:**

- Las tablas PDF se reconstruyen completas, con y sin líneas (7 de 7 y 5 de 5 filas), y los números quedan intactos (decimales con coma, miles con punto).
- Las ecuaciones PDF salen como LaTeX real con su número (`\frac{a + b}{2} \tag{1}`). ODT y TeX también entregan sus fórmulas como LaTeX.
- El modo artículo de las páginas web quita el menú, las cookies, la barra lateral y el pie, y conserva títulos, listas anidadas, citas, tablas y código.
- Una página sin imágenes con texto invisible pierde ese texto, y el resumen lo avisa con el número de página (ADR-0054).
- Al dividir un CSV, cada parte repite la fila de encabezado, así que cada parte se entiende sola.
- Al unir, los límites entre documentos se ven claros (comentario de origen, «Document N of M» y una regla `---`), y las notas al pie de verdad se renumeran sin chocar entre documentos (lo comprobé otra vez en esta ronda).
- DOCX conserva las listas numeradas anidadas, las viñetas, los títulos, las ecuaciones y el texto final de los cambios controlados.
- Los fallos totales (contraseña, archivo dañado, bomba zip, archivo vacío) siempre traen su razón: nada se pierde entero sin explicación.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B3-01 | 🔴 Alta | medio | alta | Las listas numeradas y con letras de un PDF se convierten en un párrafo corrido |
| B3-02 | 🔴 Alta | medio | alta | En los PDF de 2 o 3 páginas, el encabezado y el pie quedan pegados en mitad de las frases |
| B3-04 | 🔴 Alta | pequeño | alta | La protección contra texto invisible se desactiva si la página tiene cualquier imagen, incluso un logo pequeño |
| B3-03 | 🟠 Media | medio | alta | Al dividir un PDF, cada parte vuelve a traer los encabezados y pies que la conversión completa quitaba |
| B3-05 | 🟠 Media | pequeño | alta | Un resultado vacío se cuenta como «convertido», y la nota puede atribuirle una causa falsa («escaneado») |
| B3-06 | 🟠 Media | medio | alta | El escape de seguridad deja marcas raras en el texto (&#91;12&#93;, AT&amp;T, juan\_perez) y no es igual en todos los formatos |
| B3-11 | 🟠 Media | pequeño | alta | Las notas muy cortas de Windows llegan a la IA en caracteres chinos |
| B3-07 | 🟠 Media | medio | alta | Dividir por palabras deja títulos solos en una parte y no corta las tablas grandes |
| B3-08 | 🟠 Media | medio | media | Excel: el título combinado queda como encabezado de la tabla, los porcentajes salen como decimales y las fórmulas sin valor guardado salen en blanco sin aviso |
| B3-09 | 🟠 Media | medio | alta | Lo que markitdown pierde sin aviso: comentarios de Word, pies de foto web, notas al pie con enlaces de ruido, y la jerarquía y los «\|» de PowerPoint |

<details><summary>Detalle técnico y evidencia</summary>

- **B3-01 — Las listas numeradas y con letras de un PDF se convierten en un párrafo corrido**
  - *Impacto:* Requisitos, pasos y cláusulas casi siempre vienen numerados. La IA los recibe pegados en un solo párrafo, con el primero escapado como «1\.», y pierde cuántos puntos hay y dónde termina cada uno. Las viñetas sí se conservan, y eso hace la diferencia más confusa.
  - *Evidencia:* listas.pdf sintético (tests/support/pdf_builder.py) con «1. / 2. / 3.» (el tercero en dos renglones), «a) / b)» y «10. / 11.». Salida: `1\. Copia...` / `2\. Recibo ... reciente. 3. Formulario ...` / `a) Persona natural b) Persona jurídica`. cleaner/items.py:7-23 solo reconoce BULLET, DASH y CIRCLE.
  - *Recomendación:* Tratar como punto de lista un renglón que empieza con «N.», «N)», «a)» o «a.» cuando hay al menos dos seguidos, con números consecutivos y el mismo margen izquierdo, y unir a cada punto sus renglones de continuación. Los números en negrita siguen siendo títulos. La prueba debe cubrir el caso difícil: puntos que terminan en punto final, un punto en dos renglones, la numeración 10 y 11, y letras.
- **B3-02 — En los PDF de 2 o 3 páginas, el encabezado y el pie quedan pegados en mitad de las frases**
  - *Impacto:* Cartas, facturas, resoluciones y certificados de pocas páginas con membrete y «Página X de Y» llegan a la IA con frases cortadas por el membrete, y el pie de la página 1 aparece arriba.
  - *Evidencia:* dos.pdf e informe.pdf sintéticos: `...sin cerrar la frase Informe Anual de Agua 2026 - Municipio Ejemplo` y `...fondo regional El servicio Informe Anual ... Página 2 de 3 población rural...`. Con 40 páginas, 0 apariciones. running.py:14 `MIN_PAGES_FOR_RUNNING = 4` y running.py:75 (lo volví a ver en esta ronda).
  - *Recomendación:* En documentos de 2 o 3 páginas, quitar solo los renglones idénticos, o con un número que sigue a la página, que aparecen en el mismo margen de todas las páginas. Y si un renglón del margen se conserva, que nunca se una a un párrafo vecino: debe quedar en su propio párrafo y en su lugar. La prueba: 2 páginas y un párrafo que pasa de una a la otra.
- **B3-04 — La protección contra texto invisible se desactiva si la página tiene cualquier imagen, incluso un logo pequeño**
  - *Impacto:* Casi todo documento oficial tiene un logo en el membrete. En esas páginas, una instrucción oculta llega completa a la IA y el resumen no avisa nada.
  - *Evidencia:* logo_oculto.pdf sintético (logo de 20×20 pt y texto en modo de render 3): la instrucción oculta aparece en la salida y el resumen no avisa nada. Lo releí en esta ronda: pdfium/hidden.py `_invisible_without_picture` devuelve `invisible and not picture`, donde basta una sola imagen de cualquier tamaño en la página.
  - *Recomendación:* Conservar el texto invisible solo cuando queda dentro del área de una imagen grande, como en un escaneo con texto reconocido (por ejemplo, una imagen que cubre al menos la mitad de la página). El resto se quita y se avisa. La prueba: un logo pequeño y texto invisible lejos de él.
- **B3-03 — Al dividir un PDF, cada parte vuelve a traer los encabezados y pies que la conversión completa quitaba**
  - *Impacto:* Quien divide un documento largo para dárselo a la IA por partes recibe partes más sucias que el documento entero. El membrete y el pie se repiten en cada parte, y la IA los puede tomar por contenido.
  - *Evidencia:* largo.pdf sintético de 40 páginas: convertido completo, 0 apariciones; con `--split-words 500`, el encabezado aparece en las 40 partes. Mismo umbral de running.py:14.
  - *Recomendación:* Detectar los encabezados y pies una sola vez sobre el documento completo y aplicar ese resultado a cada parte. Otra opción: convertir completo y cortar el Markdown en los límites de página. La prueba: 40 páginas divididas de a una, comparadas con la conversión completa.
- **B3-05 — Un resultado vacío se cuenta como «convertido», y la nota puede atribuirle una causa falsa («escaneado»)**
  - *Impacto:* La persona ve «convertido» y le entrega a la IA un archivo vacío. En mi caso, además, la nota dice «páginas escaneadas» cuando el texto existía y ClearMD lo quitó al tomarlo por encabezados. Al unir, el documento aparece como «Document 4 of 4» sin contenido. B1-03 y B5-01 muestran el mismo fallo con casos más comunes (un PDF escaneado, una presentación vacía).
  - *Evidencia:* cuatro.pdf sintético: salida de 1 byte; resumen `pages without text, probably scanned images ...: 1–4` junto a `headers, footers ... were left out`. B1-03 (pptx vacía de 0 bytes) y B5-01 (PDF de páginas en blanco, EXIT=0) dan la misma causa raíz: execution.py escribe sin mirar si el Markdown tiene texto.
  - *Recomendación:* (1) Si el Markdown queda sin texto, el resultado es «falló», con su razón adaptada al caso: escaneado, sin contenido o todo era margen. Vale también para las partes de Dividir y los documentos de Unir. (2) La nota de «escaneado» se calcula antes de la limpieza: si la página tenía texto, no se dice «escaneada». Lo mejor en ese caso es devolverla sin limpiar.
- **B3-06 — El escape de seguridad deja marcas raras en el texto (&#91;12&#93;, AT&amp;T, juan\_perez) y no es igual en todos los formatos**
  - *Impacto:* En los PDF, ODT, TeX, HTML y Excel, la IA lee «&#91;12&#93;», «AT&amp;T» y «juan\_perez@...». Puede copiar esas marcas en sus respuestas, y un correo con «\_» no sirve. En .txt y .csv el mismo texto llega limpio, pero B2-01 mostró que esos son justo los formatos por donde se cuelan imágenes remotas: no hay una sola regla de salida.
  - *Evidencia:* simbolos.pdf frente a simbolos.txt (ronda 1). escaping.py:29-40: `&` seguido de letra se vuelve `&amp;`, y `[ ]` se vuelven `&#91; &#93;`. B2-01 reproduce que los formatos copiados casi tal cual no pasan por ese escape y dejan pasar `![a [b] c](http://...)`.
  - *Recomendación:* Una sola puerta de salida, igual para todos los formatos, que escape lo mínimo y con marcas legibles: «\[» en vez de «&#91;», sin escapar «_» dentro de una palabra y sin tocar el «&» que no forma una entidad. Que neutralice de verdad lo que descarga algo (imágenes, referencias, HTML activo) usando un parser CommonMark como oráculo, como pide B2-01. Medir los caracteres que agrega el escape en un corpus público.
- **B3-11 — Las notas muy cortas de Windows llegan a la IA en caracteres chinos**
  - *Impacto:* Una nota de dos o tres letras («Sí», «Año»), guardada con la codificación antigua de Windows, llega a la IA como «叭» o «A隳». La IA recibe un texto sin sentido, y las notas de la versión 2.12.0 dicen que eso ya no pasa.
  - *Evidencia:* Lo reproduje en esta ronda, en /tmp/audit-b3r2 del contenedor: `printf "S\xed" > si.txt` → si.md = `叭`; `printf "A\xf1o"` → `A隳`. Coincide con B5-03. packaging/RELEASE_NOTES.md:27 promete lo contrario. B1-10 añade que un CSV UTF-16 con BOM recibe el aviso de «tuvo que adivinar».
  - *Recomendación:* Con textos de muy pocos bytes, preferir cp1252 a las codificaciones asiáticas, o exigir una longitud mínima antes de aceptar big5, gbk o shift_jis. Reconocer el BOM UTF-16 sin adivinar. La prueba debe incluir los casos «Sí» y «Año», y hay que corregir las notas de la versión.
- **B3-07 — Dividir por palabras deja títulos solos en una parte y no corta las tablas grandes**
  - *Impacto:* Una parte que solo dice «# Prosa» no le sirve a la IA, y la siguiente llega sin su título. Una tabla Markdown larga no se corta nunca: con un límite de 500 palabras salió una parte de 4.510.
  - *Evidencia:* tabla.md sintético: part 1 = 13 palabras (termina en el título), part 2 = 4.510 palabras. prosa.md: part 1 = `# Prosa`. En el CSV sí se corta y se repite el encabezado.
  - *Recomendación:* Un título nunca termina una parte: pasa a la siguiente con su contenido. Una tabla más grande que el límite se corta por filas y repite su encabezado, como ya se hace con el CSV. Un párrafo enorme se corta por frases.
- **B3-08 — Excel: el título combinado queda como encabezado de la tabla, los porcentajes salen como decimales y las fórmulas sin valor guardado salen en blanco sin aviso**
  - *Impacto:* La IA toma el título «Reporte de Ventas 2026» por el nombre de las columnas, lee 15,5 % como «0.155» y no sabe que faltan los totales.
  - *Evidencia:* ventas.xlsx sintético (openpyxl). xlsx.py:78-83 toma siempre la primera fila como encabezado; xlsx.py:38-50 ignora number_format. Las fórmulas sin valor dependen del programa que generó el archivo (confianza media).
  - *Recomendación:* Separar el título combinado de la tabla, respetar el formato de porcentaje y avisar cuando hay fórmulas sin valor guardado y celdas combinadas.
- **B3-09 — Lo que markitdown pierde sin aviso: comentarios de Word, pies de foto web, notas al pie con enlaces de ruido, y la jerarquía y los «|» de PowerPoint**
  - *Impacto:* Los comentarios de un contrato («REVISAR ESTA CLÁUSULA») desaparecen sin aviso, aunque en ODT sí se avisa. El pie de foto de una noticia se pierde. Las notas al pie de Word llegan con enlaces internos que son ruido. En una presentación, las viñetas pierden sus niveles, y un «\|» dentro de una celda desplaza las columnas de la tabla.
  - *Evidencia:* contrato.docx sintético: el comentario no aparece y el resumen no lo menciona; `[[1]](#footnote-2)`; una tabla con el encabezado vacío. news.html: falta el figcaption. plan.pptx: niveles 0/1/1/2/0 salen planos, y `\| Viajes \| 10 \| \|pipe\| \|` (5 celdas en una tabla de 3). markitdown_adapter.py:146-158 pasa esa salida tal cual.
  - *Recomendación:* Un paso posterior por formato, con su lista de lo que markitdown pierde. DOCX: avisar de los comentarios, limpiar las notas al pie a `[^1]` y usar la siguiente fila como encabezado si la primera está vacía. HTML: conservar el figcaption. PPTX: escribir las viñetas con su nivel, escapar «\|» y dejar una línea en blanco alrededor de cada tabla. Encaja con B4-02, que propone convertir DOCX y PPTX directamente con mammoth y python-pptx.

</details>

### Backend · Eficiencia y empaquetado — 7/10

Después del debate mantengo la nota de 7/10. ClearMD es austero en lo que más pesa para la mayoría: el instalador ligero ocupa 28,6 MB, la memoria de un PDF largo se mantiene baja y el trabajador nunca queda vivo con memoria sucia. Sigo viendo tres problemas que una persona sí nota. Primero, el tiempo estimado de un PDF se calcula por su peso en bytes. Para un PDF de texto comprimido se queda hasta 20 veces corto, y el propio comentario de limits.py reconoce que la cifra elegida es un punto medio. Segundo, al convertir un PDF largo pasa casi un tercio del tiempo sin mostrar avance. Tercero, todo lo que se descarga fuera del instalador ligero de Windows pesa de más: 264 MB por PyPI y un único archivo de 224 MB en Linux. Mis colegas sumaron dos hallazgos que tocan el empaquetado y que comprobé: la ventana flet instalada desde PyPI descarga su programa porque nadie define FLET_VIEW_PATH (B2-04), y el CI no revisa vulnerabilidades del lock (B2-05). Bajo de prioridad mi hallazgo sobre el CI (B4-06), porque la persona no lo ve.

**Fortalezas que vio:**

- El instalador ligero de Windows (28,6 MB frente a 159 MB) tiene un tope de tamaño en CI (ADR-0052). Lo que baja casi todo el mundo pesa lo que instala.
- Los ejecutables dejan fuera magika, onnxruntime, numpy y pandas, y check_executables.sh falla si vuelve a entrar una librería pesada o si una carpeta pasa de su tope.
- La lectura de PDF usa poca memoria: un PDF de 400 páginas y 1,5 millones de caracteres se queda en unos 57 MB, porque el lector guarda una sola página a la vez.
- El límite de tiempo cuenta desde el último avance: un PDF largo que sigue avanzando termina en lugar de cortarse.
- La cola convierte primero los archivos ligeros (ADR-0050) y arranca un trabajador nuevo por tarea, así que no quedan procesos con la memoria sucia.
- El CI guarda el tiempo de cada test (junitxml), y eso hace posible medir y optimizar.
- La rueda de PyPI pesa 0,8 MB y fija sus dependencias a versiones con al menos dos semanas de antigüedad.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B4-01 | 🔴 Alta | medio | alta | El tiempo estimado de un PDF se calcula por su peso en bytes, y en un PDF de texto comprimido se queda corto hasta 20 veces |
| B4-04 | 🟠 Media | pequeño | alta | Al convertir un PDF, el primer 30 % del tiempo pasa sin avance visible, y cada página se abre dos veces |
| B4-02 | 🟠 Media | medio | alta | Instalar desde PyPI ocupa 264 MB, y casi la mitad son librerías que ClearMD nunca usa (magika, onnxruntime, numpy) |
| B4-03 | 🟠 Media | pequeño | alta | En Linux solo hay un archivo de 224 MB con las cuatro aplicaciones, sin versión ligera ni tope de tamaño |
| B4-05 | 🟠 Media | pequeño | media | Cada tarea paga casi un segundo de arranque del trabajador, más de lo que estima el programa, en parte por cargar librerías que esa tarea no usa |
| B4-07 | ⚪ Baja | pequeño | media | La línea de comandos de Windows pesa lo mismo que la ventana clásica porque lleva dentro la interfaz gráfica |
| B4-06 | ⚪ Baja | pequeño | media | El CI tarda unos 16 minutos por cada push, también cuando solo cambian capturas o informes |

<details><summary>Detalle técnico y evidencia</summary>

- **B4-01 — El tiempo estimado de un PDF se calcula por su peso en bytes, y en un PDF de texto comprimido se queda corto hasta 20 veces**
  - *Impacto:* La persona ve un tiempo restante que no se cumple: el programa promete un segundo y tarda veinte. Además, la cola cree que ese PDF es rápido y lo pone delante de archivos que de verdad lo son, que entonces esperan. El aviso de archivo largo nunca sale para un PDF.
  - *Evidencia:* limits.py:24 FormatId.PDF: 4.0 s/MiB. El comentario de limits.py:21-23 reconoce que es «un valor medio» entre 6-14 s/MiB (texto sintético) y 0,03 s/MiB (escaneados). Medido: un PDF sintético de 400 páginas comprimido pesa 255 KB, se estiman 0,99 s y tarda 19,9 s. Sin comprimir pesa 2,14 MiB, se estiman 8,6 s y tarda unos 20 s. TimeLeft corrige solo después del primer archivo. planning.py:197 deja los PDF fuera del aviso. Gemelo público: cualquier libro de texto exportado a PDF con flujos comprimidos.
  - *Recomendación:* Estimar los PDF por número de páginas y, si se puede, por si tienen texto (FPDF_GetPageCount es inmediato). Así se cubren los dos extremos que hoy promedia el comentario. Test del caso difícil: un PDF comprimido de 400 páginas cuya estimación quede dentro de 2 veces el tiempo real, y una cola en la que un DOCX de 2 MiB no espere detrás de él.
- **B4-04 — Al convertir un PDF, el primer 30 % del tiempo pasa sin avance visible, y cada página se abre dos veces**
  - *Impacto:* En un libro grande, la persona ve «Convirtiendo…» sin número de página durante decenas de segundos y puede pensar que el programa se colgó.
  - *Evidencia:* reader.py:33-37 hace una primera pasada por todas las páginas sin llamar a report(). Medido con un PDF de 400 páginas: el primer avance llega a los 5,4 s de 18,1 s. cProfile: each_font se llama 3,1 millones de veces para 1,55 millones de caracteres.
  - *Recomendación:* Informar avance también en la primera pasada (2N pasos: «leyendo página 40 de 400»). Test que mida el tiempo hasta el primer avance en un PDF de cientos de páginas. Más adelante, reducir el trabajo por carácter de la primera pasada.
- **B4-02 — Instalar desde PyPI ocupa 264 MB, y casi la mitad son librerías que ClearMD nunca usa (magika, onnxruntime, numpy)**
  - *Impacto:* Quien instala con pip descarga unos 124 MB inútiles, y el trabajador carga onnxruntime en memoria cada vez que convierte un Word o un PowerPoint.
  - *Evidencia:* Instalación limpia de la rueda 2.12.0: 264 MB (onnxruntime 63 MB, numpy 57 MB, magika 4 MB). markitdown 0.1.9 exige magika. Con import markitdown quedan cargados los tres. El RSS del adaptador pasa de 55 a 100 MB, y a 80 MB con el stub de packaging/no_magika.py.
  - *Recomendación:* A corto plazo, aplicar el stub de magika también en el trabajador de las instalaciones con pip. A medio plazo, convertir DOCX y PPTX directamente con mammoth y python-pptx. Eso encaja con B3-09 y B3-10, que piden de todos modos un paso propio para esos formatos, y permitiría quitar markitdown. Actualizar ADR-0032, porque PyPI ya es un canal público.
- **B4-03 — En Linux solo hay un archivo de 224 MB con las cuatro aplicaciones, sin versión ligera ni tope de tamaño**
  - *Impacto:* Quien usa Linux y solo quiere la App Clásica (unos 36 MB) tiene que bajar 224 MB, seis veces más.
  - *Evidencia:* gh release view v2.11.0: el linux.tar.gz pesa 224,3 MB. packaging/package.sh:41-46 mete las cuatro aplicaciones en un solo tar. check_executables.sh no pone tope al archivo publicado.
  - *Recomendación:* Publicar un tar ligero (App Clásica y línea de comandos) y otros aparte para Qt y flet, como en ADR-0052, con un tope de tamaño en CI y una línea en el README que diga cuál bajar.
- **B4-05 — Cada tarea paga casi un segundo de arranque del trabajador, más de lo que estima el programa, en parte por cargar librerías que esa tarea no usa**
  - *Impacto:* Convertir un .txt de 41 bytes tarda 1,8 s. Como el trabajador arranca de nuevo en cada tarea (decisión del dueño), cada clic paga ese arranque, y en un portátil Windows modesto probablemente más.
  - *Evidencia:* warm_up medido en el contenedor: 0,9-1,26 s, frente a limits.py:86 worker_startup_seconds=0.7. Con -X importtime, el hijo carga openpyxl (167 ms), pypdfium2 (80 ms) e images (50 ms) sin importar qué se convierte.
  - *Recomendación:* Importar de forma diferida openpyxl, pypdfium2 e images en worker/pages.py y split/*. Medir el arranque real en el ejecutable de Windows y usar esa cifra. Añadir un test que vigile la lista de módulos que se cargan al arrancar.
- **B4-07 — La línea de comandos de Windows pesa lo mismo que la ventana clásica porque lleva dentro la interfaz gráfica**
  - *Impacto:* clearmd-cli.exe pesa 36,2 MB, lo mismo que ClearMD.exe, porque lleva Tk, ttkbootstrap y Pillow, que nunca usa.
  - *Evidencia:* gh release view v2.11.0: los dos pesan 36,2 MB. packaging/clearmd.spec usa el mismo analysis(), con collect_submodules('clearmd'), para launch_cli.py.
  - *Recomendación:* Hacer un analysis() propio para la CLI que excluya frontend.ttk, tkinter, ttkbootstrap y tkinterdnd2 (y PIL si --images no lo necesita), con su propio tope en check_executables.sh.
- **B4-06 — El CI tarda unos 16 minutos por cada push, también cuando solo cambian capturas o informes**
  - *Impacto:* La persona no lo ve, pero retrasa los arreglos que solo se pueden comprobar en Windows.
  - *Evidencia:* Run 42714246321: Windows 3.14 tarda 16 min y Linux 10-12 min. 3.802 tests en serie (913 s en Windows). ci.yml no tiene paths-ignore, así que un commit que solo cambia capturas lanza la matriz completa.
  - *Recomendación:* paths-ignore estrecho para docs/screenshots/** y docs/audit/**, pytest-xdist en Linux (--dist loadfile para la GUI) y Windows 3.12 solo en main y en los tags. Windows sigue en el CI.

</details>

### Backend · Claridad es cariño — 6,5/10

Tras leer a los diez auditores mantengo el diagnóstico: los textos de ClearMD fuera de la ventana son muy superiores a lo normal (cada error con su motivo y su paso siguiente, un resumen ordenado para una persona, cuidado de la privacidad al reportar), pero en los casos difíciles prometen más de lo que el producto cumple. El debate confirmó, con pruebas independientes de tres auditores (B1, B3 y yo), el problema más serio de mi lente: un resultado vacío (PDF escaneado, presentación vacía, PDF cuyo texto se tomó por encabezados) se anuncia como "convertido", con código de salida 0, y a veces con una nota que adivina mal la causa. También confirmó, por tres vías (B5, F4, F5), que "Copiar Detalles" manda a GitHub Issues contra la decisión del dueño. Los colegas me hicieron ver otra forma del mismo patrón: el consejo "divídelo" para un PDF de más de 250 MB lleva a una herramienta que lo rechaza igual (B1-02), y una nota "escaneado" que no es verdad (B3-05). Mantengo las demás: el acceso directo de la Línea de Comandos que no funciona sin PATH, las notas de versión que prometen algo que "Sí" o "Año" desmienten, el README desactualizado, la ayuda de la línea de comandos a medias en inglés y los documentos de comunidad solo en inglés. Nota: 6,5/10.

**Fortalezas que vio:**

- El catálogo de errores separa siempre qué pasó de qué hacer (message + action en es.toml), con acciones concretas y amables.
- Un archivo vacío de entrada es un fallo con su razón en palabras sencillas, como decidió el dueño.
- El resumen está ordenado para una persona: titular con la cifra, dónde están los archivos, lo que necesita atención, y el detalle técnico plegado.
- La línea de comandos traduce las instrucciones pensadas para la ventana a su opción equivalente (--merge, --overwrite, --skip).
- Cuidado de la privacidad al reportar: aviso de no pegar el resumen completo y ocultación de rutas en Copiar Detalles.
- Honestidad con la codificación: cuando ClearMD adivina, lo dice y da un paso concreto.
- El instalador describe cada app con franqueza (incluido que la App Clásica no la lee un lector de pantalla).
- El README advierte que OneDrive, Google Drive o Dropbox pueden subir los resultados a la nube aunque ClearMD no use internet.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B5-01 | 🔴 Alta | pequeño | alta | Un resultado vacío (PDF escaneado, presentación vacía, PDF cuyo texto se tomó por encabezados) se anuncia como "convertido" |
| B5-02 | 🔴 Alta | pequeño | alta | El acceso directo de la Línea de Comandos indica, en inglés, un comando que no funciona con la instalación por defecto |
| B5-03 | 🟠 Media | pequeño | alta | Las notas de la versión prometen que las notas cortas de Windows conservan sus letras, y las más cortas salen en caracteres chinos |
| B5-04 | 🟠 Media | pequeño | alta | "Copiar Detalles" manda a reportar en un sitio distinto del acordado y que exige cuenta |
| B5-05 | 🟠 Media | medio | alta | El README se quedó atrás en datos que el usuario usa: valor por defecto, opciones, códigos de salida y carpetas |
| B5-06 | 🟠 Media | medio | alta | La ayuda y los errores de la línea de comandos salen en inglés aunque se pida español, y mandan a una lista de formatos que no existe |
| B5-07 | 🟠 Media | pequeño | alta | SECURITY, el formulario de ideas y los enlaces de contacto solo en inglés; "cómo comprobar la descarga" son comandos de terminal |
| B5-08 | ⚪ Baja | pequeño | alta | El resumen dice "HTML (Artículo)" para una página que se convirtió completa |
| B5-09 | ⚪ Baja | pequeño | media | Consejos que no llevan a ninguna parte y jerga en los textos que se leen fuera de la ventana |

<details><summary>Detalle técnico y evidencia</summary>

- **B5-01 — Un resultado vacío (PDF escaneado, presentación vacía, PDF cuyo texto se tomó por encabezados) se anuncia como "convertido"**
  - *Impacto:* La persona ve 'El documento se convirtió', la línea de comandos termina con éxito (código 0) y le entrega a su IA un archivo vacío. El aviso, cuando existe, va como nota secundaria, no dice qué hacer y a veces dice una causa falsa ('páginas escaneadas' cuando el texto lo quitó la limpieza). Choca con la promesa de la 2.12.0: 'Lo que llega a tu IA es lo que tú ves'.
  - *Evidencia:* Mío: PDF sintético de 3 páginas en blanco (pypdfium2 new_page) → 'ℹ escaneado.pdf — convertido con notas', '1 convertido', EXIT=0; titular es.toml:220 headline.all.one; nota es.toml:298 sin paso siguiente; .md vacío. Confirmado de forma independiente por B1-03 (pptx vacío → .md de 0 bytes sin nota; html sin cuerpo → 1 byte) y B3-05 (PDF de 4 páginas con todo el texto en márgenes → 1 byte con nota 'escaneado' falsa). En el código, el worker solo aplica safe_output (child.py:109) y no hay comprobación de resultado vacío; schemas/notes.py no tiene NoteKind para él.
  - *Recomendación:* Extender la regla del dueño 'archivo vacío = fallido con su razón' al resultado: si el Markdown queda sin texto tras la limpieza, dar 'falló' con un motivo adaptado ('Este PDF son solo imágenes escaneadas: pásalo antes por un programa que reconozca texto (OCR)' / 'El documento no tiene contenido'). La nota de 'escaneado' debe calcularse antes de la limpieza. Aplicarlo también a cada parte de Dividir y a cada documento de Unir. Test del caso difícil: un PDF de una sola página en blanco, uno con solo espacios, el de B3-05 y uno mixto (1 de 10 páginas con texto, que sigue siendo convertido con nota).
- **B5-02 — El acceso directo de la Línea de Comandos indica, en inglés, un comando que no funciona con la instalación por defecto**
  - *Impacto:* Quien instala la Línea de Comandos y abre su acceso directo ve la ayuda en inglés y 'Type: clearmd-cli "<folder or file>"'. Como la opción PATH viene desmarcada, Windows responde que 'clearmd-cli' no se reconoce. La primera experiencia es un error, sin una pista en español; y la ayuda dice 'usage: clearmd', otro nombre.
  - *Evidencia:* packaging/installer/clearmd.iss:245 (Parameters con texto fijo en inglés, WorkingDir {userdocs}); clearmd.iss:204 tarea addpath con 'Flags: unchecked'; clearmd.iss:146 CompareCli promete 'clearmd-cli "C:\Mis documentos"'; src/clearmd/frontend/cli/parser.py:14 prog="clearmd". Deducido del script del instalador; no ejecutado en Windows.
  - *Recomendación:* Texto del acceso directo en CustomMessages (dos idiomas) y que funcione sin PATH (abrir el cmd en la carpeta de la app o usar la ruta completa en el ejemplo). Que la ayuda use el nombre real del ejecutable y el idioma del instalador o de los ajustes. Probarlo en una máquina limpia con PATH sin marcar (el caso por defecto), idealmente con las capturas de instalador que pide F4-08.
- **B5-03 — Las notas de la versión prometen que las notas cortas de Windows conservan sus letras, y las más cortas salen en caracteres chinos**
  - *Impacto:* Una nota de dos o tres letras guardada en el Bloc de notas antiguo ('Sí', 'Año') llega a la IA como '叭' o 'A隳'. El aviso aparece en jerga ('`a.txt (big5)`'), y la versión 2.12.0 dice que eso ya no pasa.
  - *Evidencia:* packaging/RELEASE_NOTES.md:27 'Las notas y los CSV cortos guardados por Windows conservan sus letras'. Archivos sintéticos cp1252: 'Sí' (2 bytes) → '叭', 'Año' (3 bytes) → 'A隳' con nota encoding_guessed (big5). 'Mamá', 'Niño', 'Señor Pérez' bien. B1-10 añade un caso hermano: un CSV UTF-16 con BOM recibe 'ClearMD tuvo que adivinar' aunque el BOM es certero.
  - *Recomendación:* Con muy pocos bytes, preferir cp1252 frente a big5/gbk/shift_jis o exigir una longitud mínima para aceptarlas; reconocer el BOM UTF-16 sin 'adivinar' (B1-10). Agregar 'Sí' y 'Año' al test. Quitar el nombre técnico de la codificación del aviso o moverlo al detalle técnico. Corregir las notas de la versión mientras tanto.
- **B5-04 — "Copiar Detalles" manda a reportar en un sitio distinto del acordado y que exige cuenta**
  - *Impacto:* Tras un error inesperado, la persona pulsa Copiar Detalles y el mensaje que ofrecía comunidad o correo se reemplaza por 'Pégalo en github.com/ClearNote97/ClearMD/issues', que exige cuenta. Quien no tiene cuenta pierde la opción del correo justo cuando quiere ayudar.
  - *Evidencia:* Re-verificado: src/clearmd/i18n/es.toml:512 y en.toml:511 details_copied con '/issues'; es.toml:60 report.how y :167 unexpected_error mandan a /discussions o al correo. Confirmado también por F4-02 y F5-02, que añaden que reset.py:78 reemplaza el mensaje anterior.
  - *Recomendación:* Que details_copied use {report}, como el resto. Un test que falle si algún texto del catálogo contiene '/issues' o una URL de reporte escrita a mano.
- **B5-05 — El README se quedó atrás en datos que el usuario usa: valor por defecto, opciones, códigos de salida y carpetas**
  - *Impacto:* Quien sigue el README lee que las páginas web se convierten completas por defecto (es al revés), no encuentra la mitad de las opciones, cree que una entrada no válida termina con código 2 (termina con 0), no sabe que existen OutputSep y OutputUnif y lee 'en construcción' en la 2.12.
  - *Evidencia:* README.es.md:223 / README.md:221 '--html ... la página completa (por defecto)' frente a settings.py:17 html_strategy='article' y `clearmd --help`. Tabla de opciones sin --changed, --summary-pdf(-only), --images, --split-*, --keep, --merge. `clearmd one/nota.xyz --lang es` → 'Nada que convertir.' EXIT=0 frente a 'código 2' del README. Conteos de ADR desactualizados (55 archivos). F4-07 confirma la insignia y los conteos.
  - *Recomendación:* Generar o verificar con un test la tabla de opciones a partir del parser. Corregir el defecto de --html, los conteos y 'Qué produce'. Decidir si 'nada que hacer' es éxito o error y alinear README y código. Quitar 'en construcción' (F4-07).
- **B5-06 — La ayuda y los errores de la línea de comandos salen en inglés aunque se pida español, y mandan a una lista de formatos que no existe**
  - *Impacto:* Con '--lang es' la persona ve 'usage:', 'options', 'the following arguments are required: PATH', 'must be from 500 to 1000000'. 'clearmd' sin nada da un bloque de uso en inglés. Al omitir un formato, el mensaje dice 'Revisa los formatos compatibles en la ayuda', y la ayuda no los lista.
  - *Evidencia:* Ejecutado en el contenedor: `clearmd --lang es --help`, `clearmd`, `clearmd in --lang es --split-words 100`. parser.py:14 argparse sin traducir; parser.py:84-86 mensajes fijos en inglés. es.toml:5 y :99 remiten a la ayuda; la lista solo está en gui.help.formats.
  - *Recomendación:* Traducir los textos de argparse y los de parser.py:84-86 por el catálogo. 'clearmd' sin argumentos: dos o tres ejemplos amables. Añadir al epílogo la lista de formatos (reusando gui.help.formats), los códigos de salida y dónde está settings.toml.
- **B5-07 — SECURITY, el formulario de ideas y los enlaces de contacto solo en inglés; "cómo comprobar la descarga" son comandos de terminal**
  - *Impacto:* El README en español invita a comprobar cada descarga y lleva a una página en inglés con comandos de Linux y PowerShell y un ejemplo de la 1.2.0. Quien quiere proponer una idea encuentra un formulario solo en inglés, y el de errores pide 'clearmd --version', que en Windows no existe con ese nombre.
  - *Evidencia:* SECURITY.md entero en inglés, sección 'Checking a download' con sha256sum y Get-FileHash .\ClearMD-Setup-1.2.0.exe; enlazado desde README.es.md y RELEASE_NOTES.md. .github/ISSUE_TEMPLATE/feature_request.yml y config.yml solo en inglés; bug_report.yml con 'clearmd --version' y placeholder '1.2.0'.
  - *Recomendación:* Sección de comprobación bilingüe, en dos pasos sin terminal ('normalmente no hace falta; si quieres...'), sin versión fija. Formulario de ideas y contactos bilingües. En el de errores: 'Ayuda → número de versión' y 'clearmd-cli --version (Windows)'.
- **B5-08 — El resumen dice "HTML (Artículo)" para una página que se convirtió completa**
  - *Impacto:* En la misma página del resumen, la tabla dice que se tomó el artículo y la nota dice que se convirtió la página completa. Una contradicción así hace dudar del resto.
  - *Evidencia:* Fixture pública tests/fixtures/documents/sample.html: fila 'HTML (Artículo)' más la nota 'no se encontró un artículo...; se convirtió la página completa'. backend/services/summary/content.py:195-196 usa outcome.item.strategy (lo planeado).
  - *Recomendación:* Etiquetar con la estrategia aplicada ('HTML (Página completa)' cuando se vuelve a la página completa). Lo mismo en Revisar si se sabe antes.
- **B5-09 — Consejos que no llevan a ninguna parte y jerga en los textos que se leen fuera de la ventana**
  - *Impacto:* Pequeñas fricciones que, juntas, alejan el tono de 'Claridad es cariño': detalle técnico en inglés dentro de un resumen en español, cifras sin contexto ('crece 338 veces al abrirse; límite 100'), traducciones literales, notas de versión intercaladas por viñeta y un consejo ('divídelo') que, para un PDF de más de 250 MB, lleva a una herramienta que lo rechaza igual (detalle y severidad en B1-02).
  - *Evidencia:* Resumen en español con 'PDFium could not open it (error 4)' / 'BadZipFile...'; es.toml skip.archive_ratio; clearmd.iss:94 'Completando la Instalación'; RELEASE_NOTES.md:27-55 intercalado (también F4-06). es.toml:93 too_large = 'Divídelo en archivos más pequeños.' aplicado también por la herramienta Dividir (B1-02, comprobado por B1 con un PDF de 260 MB; yo verifiqué solo el texto del catálogo).
  - *Recomendación:* Anteponer 'Para soporte técnico:' al detalle técnico. Omisión de ZIP en palabras ('parece un archivo comprimido dañado o peligroso; por seguridad no se abre'), con la cifra en el detalle. 'Instalación Terminada'. Notas de versión con un bloque por idioma. Que todo consejo que propone una acción tenga un test que la siga dentro del producto (B1-02).

</details>

### Frontend · Lógica y estados — 6,5/10

Después de leer a mis colegas, mantengo mis ocho hallazgos y el diagnóstico de fondo. La máquina de estados del presentador no deja a nadie atrapado. Pero en varios caminos que no son el principal, la ventana dice algo distinto de lo que pasó.
Volví a revisar en el código cuatro hallazgos de otros auditores que son de mi lente, y los apoyo:
- El contador «1 de 6» cuando la tarjeta dice «5» (F3-04).
- El estado «Esperando tu decisión» aparece siempre, aunque no haya nada que decidir (F5-10).
- «Abrir resultados» abre una ventana por cada carpeta (F5-03).
- El encabezado de flet nunca se pinta como advertencia (F3-06).
Los cuatro confirman lo que ya veía: las reglas de la ventana que no dependen de la biblioteca gráfica siguen repartidas entre las tres ventanas, o se calculan con datos distintos de los que se muestran.
Lo más grave sigue siendo lo mío: guardar Ajustes después de un error deja Resultados en «0 convertidos» (F1-01), y la casilla «Mantener los archivos» se ignora después de «Dividir los PDF grandes» (F1-02).
Tres equipos señalaron por separado el mismo problema: el mensaje de Copiar Detalles manda a GitHub Issues. Lo comprobé y debería contarse como un solo hallazgo. Coincidir confirma el hecho, no su gravedad.
Nota: 6,5.

**Fortalezas que vio:**

- Las tandas obsoletas nunca llegan a la pantalla: cada tarea lleva su número (session.generation) y lo que devuelve un análisis cancelado se descarta, incluido el conteo del escaneo.
- Un único punto decide si se puede editar (reset.editable): mientras se analiza o convierte no se edita nada, y cualquier cambio después de un plan lo descarta y vuelve al paso 1 con un aviso.
- Ningún botón principal queda desactivado sin explicar por qué (primary_of con why()), como exige ADR-0029.
- La respuesta sobre los resultados que ya existen se conserva al redibujar el mismo plan (plan_id), en las tres ventanas.
- La política de cierre es compartida (chrome/close_policy): solo pregunta si se cierra durante una conversión, espera a que se escriba el resumen y tiene un tope de 60 s.
- La carpeta de resultados se abre sola solo cuando todo salió bien (conversion.py: state is FINISHED): una ventana del explorador nunca tapa la lista de lo que falló.
- Los duplicados se filtran dos veces (presentador y backend: ALREADY_INCLUDED).
- Un error a mitad de tarea lleva a Resultados con «se detuvo: N de M terminados», las carpetas de lo que se escribió y Copiar Detalles.
- La pausa del botón principal después de cambiar de página impide que un doble clic salte de Revisar a Convertir.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F1-01 | 🔴 Alta | pequeño | alta | Tras un error a mitad de tarea, guardar Ajustes hace que Resultados diga «0 convertidos» |
| F1-02 | 🔴 Alta | medio | alta | «Mantener los archivos que elegiste» no se cumple después de «Dividir los PDF grandes», y la lista de Dividir se pierde |
| F1-03 | 🟠 Media | pequeño | alta | En la ventana clásica (ttk), los avisos que llegan en Inicio nunca se ven |
| F1-04 | 🟠 Media | pequeño | alta | Los valores temporales de «Dividir los PDF grandes» se guardan como si los hubiera elegido la persona |
| F1-05 | ⚪ Baja | pequeño | alta | «Cambiaste la lista» aparece cuando la persona no cambió nada |
| F1-06 | ⚪ Baja | pequeño | media | Durante la conversión, las páginas que se pueden visitar dejan controles activos que no hacen nada |
| F1-07 | ⚪ Baja | pequeño | alta | El teclado no es igual en las tres ventanas: Ctrl+0 (Inicio) falta en la ventana Qt |
| F1-08 | ⚪ Baja | pequeño | alta | «Deshacer» de Vaciar Lista sobrevive a un cambio de herramienta |

<details><summary>Detalle técnico y evidencia</summary>

- **F1-01 — Tras un error a mitad de tarea, guardar Ajustes hace que Resultados diga «0 convertidos»**
  - *Impacto:* La persona ve «Se detuvo por un error: 2 de 3 terminados». Si después guarda cualquier ajuste (el tema o el idioma), la página pasa a decir «0 convertidos · 0 omitidos · 0 con error». Puede creer que perdió lo convertido y repetir todo, o borrar la carpeta.
  - *Evidencia:* reset.unexpected() arma una vista especial sobre un BatchReport vacío (outcomes=()). Preferences.save_settings vuelve a llamar a result_view(s.catalog, s.report, s.state) y descarta esa vista. Lo reproduje con FakeBackend (/tmp/audit-logic-s7.py): antes, 'Stopped by an error: 2 of 3 finished.'; después de save_settings(language='es') o de theme='light', '0 convertidos · 0 omitidos · 0 con error'. Ajustes está activo en FINISHED_WITH_PROBLEMS.
  - *Recomendación:* Guardar en la sesión la razón de la parada (hecho y total) y volver a dibujar Resultados a partir de esos datos, no del informe vacío. La prueba debe cubrir: error a mitad de tarea, luego cambio de idioma y de tema, y verificar que nunca aparece «0 convertidos».
- **F1-02 — «Mantener los archivos que elegiste» no se cumple después de «Dividir los PDF grandes», y la lista de Dividir se pierde**
  - *Impacto:* Después de dividir los PDF grandes y elegir Convertir en ¿Y Ahora Qué?, la persona no recibe la lista que tenía, marque o desmarque la casilla: recibe «el resto» de la tarea anterior. Los PDF que añadió en Dividir desaparecen sin aviso. Si al principio había elegido una carpeta, «el resto» vuelve a incluir el PDF que no se podía convertir.
  - *Evidencia:* _give_back() (intents/tools.py) reemplaza s.inputs por s.back_to_convert sin mirar keep. Reproducido (/tmp/audit-logic-s1..s3.py): continue_with(CONVERT, keep=True) da ['small.docx'] en lugar de ['big.pdf'], y con keep=False da lo mismo. Si se añade c.pdf en Dividir, se pierde. Con una carpeta como entrada, rest=['docs'], porque split_large compara rutas de archivo con entradas que son carpetas. test_ac_05 solo usa archivos sueltos.
  - *Recomendación:* Que la casilla mande. Devolver «el resto» como una oferta explícita y de una sola vez («¿Volver a tu lista anterior de Convertir (N archivos)?»). Si la entrada era una carpeta, dejar fuera el PDF grande o decirlo. Probar con una carpeta y con la casilla desmarcada.
- **F1-03 — En la ventana clásica (ttk), los avisos que llegan en Inicio nunca se ven**
  - *Impacto:* Si al arrancar el archivo de ajustes estaba dañado, o si falla «guardar los ajustes» desde Inicio o desde la Bienvenida, la ventana clásica pone el aviso en una línea oculta y lo borra al cambiar de página. La persona cree que sus preferencias quedaron guardadas. En la ventana Qt el mismo aviso sí se ve.
  - *Evidencia:* ttk/window/home_chrome.show_bar(shown=not home) llama a message.pack_forget() en Inicio, y view.show_state borra el mensaje al cambiar de página. Comprobado con Xvfb (/tmp/audit-logic-s4.py): el mensaje está, pero winfo_ismapped()=0, y después de choose_tool(CONVERT) queda vacío. En PySide (/tmp/audit-logic-s5.py): isVisible()=True.
  - *Recomendación:* En Inicio, mostrar la línea de mensaje aunque se oculte la barra de acciones, o guardar el aviso para la primera página que pueda mostrarlo. Añadir una prueba de paridad en las tres ventanas: aviso al arrancar → visible.
- **F1-04 — Los valores temporales de «Dividir los PDF grandes» se guardan como si los hubiera elegido la persona**
  - *Impacto:* «Dividir los PDF grandes» fija para esa tarea N partes y «conservar el Markdown». Si mientras tanto la persona guarda cualquier ajuste, esos valores quedan escritos en disco, y la próxima vez Dividir aparece con un corte que nadie eligió.
  - *Evidencia:* Tools.split_large reemplaza s.settings en memoria (split_cut='parts', split_parts=N, split_keep='markdown'). save_settings, choose_summary_format y choose_images parten de s.settings. Reproducido (/tmp/audit-logic-s2.py): save_settings(theme='dark') guarda split_parts=7 y split_keep='markdown'.
  - *Recomendación:* Guardar los valores temporales aparte (por ejemplo, session.task_overrides) y aplicarlos al construir el SplitSpec, sin tocar s.settings. Probar: «Dividir los PDF grandes», luego un cambio de tema, y verificar lo que quedó guardado.
- **F1-05 — «Cambiaste la lista» aparece cuando la persona no cambió nada**
  - *Impacto:* Al pulsar «Dividir los PDF grandes», la ventana dice «Cambiaste la lista: los resultados anteriores siguen en su carpeta». La persona solo pulsó un botón que le ofrecimos y puede creer que borró algo.
  - *Evidencia:* split_large → choose_tool(SPLIT) → reset.editable() con page=4 y un informe presente asigna notice = gui.app.result_kept. Reproducido (/tmp/audit-logic-s3.py).
  - *Recomendación:* Que editable() reciba el motivo del cambio y elija el texto según el caso (edición, cambio de herramienta o dividir los PDF grandes).
- **F1-06 — Durante la conversión, las páginas que se pueden visitar dejan controles activos que no hacen nada**
  - *Impacto:* Mientras convierte, la persona puede volver a Revisar y cambiar «Mantener / Reemplazar» creyendo que se aplica, aunque la decisión ya se tomó. En la ventana clásica, además, aparece «Dividir los PDF grandes» y pulsarlo no hace nada.
  - *Evidencia:* Navigation.go_to permite las páginas 1 a 4 en cualquier estado. Ninguna ventana deshabilita los radios de review.py. ttk/window/offer.show_offer no comprueba WORKING, mientras que pyside/offer_of y flet/_show_offer sí lo hacen. Lo vi en el código; no lo comprobé en pantalla.
  - *Recomendación:* Deshabilitar las respuestas de Revisar fuera de WAITING_DECISION. Mover offer_of a presenter/chrome. Junto con F3-08: durante la conversión, que el botón principal no quede como «Convertir» gris.
- **F1-07 — El teclado no es igual en las tres ventanas: Ctrl+0 (Inicio) falta en la ventana Qt**
  - *Impacto:* Ctrl+0 lleva a Inicio en la ventana clásica y en flet, pero no en Qt, y la Ayuda no lo menciona. Para quien usa solo el teclado, Inicio es la única forma de cambiar de herramienta.
  - *Evidencia:* ttk inputs.py: range(5). flet keys.py: STEP_KEYS incluye HOME. pyside inputs.py: range(1, len(STEPS)+1). La ayuda de teclado (gui.help keyboard) dice 'Ctrl+1 … Ctrl+4'.
  - *Recomendación:* Definir la tabla de atajos una sola vez en presenter/chrome, con una prueba de paridad entre las tres ventanas, y nombrar Ctrl+0 en la Ayuda.
- **F1-08 — «Deshacer» de Vaciar Lista sobrevive a un cambio de herramienta**
  - *Impacto:* Hoy casi no se nota, porque el botón se oculta al cambiar de página. Pero el estado sigue vivo: un atajo futuro (Ctrl+Z) pondría los archivos de Convertir dentro de Unir.
  - *Evidencia:* Tools.choose_tool no limpia s.cleared. Reproducido (/tmp/audit-logic-s1.py): después de vaciar, ir a Inicio y elegir Unir, undo_clear() deja ['a.pdf','b.pdf'] en merge.
  - *Recomendación:* Olvidar el deshacer al cambiar de herramienta y de página.

</details>

### Frontend · Accesibilidad — 5,5/10

Después del debate mantengo el diagnóstico de la ronda 1. ClearMD tiene buenas bases de accesibilidad: una paleta probada, objetivos de 44 px, texto de 14 px como mínimo, ninguna animación y estados dichos con palabras. Pero la promesa se rompe en las dos ventanas modernas, justo las que se recomiendan a las personas con discapacidad. En la App Moderna (Qt), el foco no se ve en la lista ni en los botones de texto, y el lector de pantalla oye nombres internos. En la App Estilo Móvil (flet), las tarjetas no muestran el foco, y el motivo completo de cada archivo solo se lee con el ratón. Tres colegas (F3-01, F5-01 y, en parte, F2-05) llegan por otro camino al mismo problema del motivo cortado. Volví a comprobar en el código el corte con puntos suspensivos y el tooltip de flet, y que la fila es un Container sin foco. Eso confirma el hecho, pero no sube la gravedad. Lo dejo como un hallazgo propio, el del teclado y la información solo con el puntero, y apoyo que la solución sea mostrar el texto completo en la fila, lo que arregla los dos aspectos a la vez. También comprobé y apoyo cuatro hallazgos de otros que tocan mi lente: falta Ctrl+0 en Qt (F1-07), el aviso de Inicio no se ve en ttk (F1-03), el tono de 'Terminado con problemas' en flet (F3-06) y los contadores en naranja por defecto (F5-04). Ninguno cambia la nota. Nota: 5,5/10.

**Fortalezas que vio:**

- Una sola paleta para las tres ventanas (frontend/design/palette.py), con una prueba automática de contraste 4,5:1 en los dos temas. Ningún color base de texto falla.
- Los estados nunca se indican solo con color: las filas dicen 'Con error:' u 'Omitido:', las cifras llevan su etiqueta, los listos tienen ✓ y el paso actual se marca con un relleno.
- La App Clásica (ttk) tiene el mejor anillo de foco de las tres: va por fuera del botón, deja un hueco y contrasta 3,4–4,0:1. Sus tarjetas se iluminan igual con foco que con el puntero, y su lista se recorre con las flechas.
- El instalador, el README, las notas de versión y la Ayuda dicen con honestidad que la App Clásica no se puede leer con un lector de pantalla, y llevan a la persona a la App Moderna.
- Atajos coherentes y explicados: Enter pulsa el botón enfocado o la acción principal, Esc cierra, y Supr y Ctrl+A solo actúan con la lista enfocada. Hay una matriz de pruebas por ventana.
- La App Moderna ya da nombre accesible a las tarjetas de herramienta, a los pasos del riel, a Ajustes y Ayuda en modo compacto y a los campos de Ajustes, con su etiqueta enlazada.
- No hay animaciones ni parpadeos. 'Deshacer' tras 'Quitar todo' evita perder trabajo por un error de teclado.
- Objetivos de 44 px y texto nunca menor de 14 px, como tokens comunes (metrics.py, typography.py).

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F2-01 | 🔴 Alta | pequeño | alta | En la App Moderna (la que se recomienda con lector de pantalla), el foco del teclado no se ve en la lista de archivos ni en varios botones |
| F2-02 | 🔴 Alta | pequeño | media | En la App Estilo Móvil (flet), las tarjetas grandes no muestran el foco y el resto de los botones lo muestra casi invisible |
| F2-03 | 🔴 Alta | medio | alta | En la App Estilo Móvil, el motivo completo de cada archivo en Revisar y Resultados solo se alcanza con el ratón |
| F2-04 | 🟠 Media | pequeño | alta | El texto de color sobre una fila seleccionada y otros colores mezclados no llegan a 4,5:1, y la prueba de contraste no los revisa |
| F2-05 | 🟠 Media | medio | alta | En la App Moderna, el lector de pantalla oye nombres internos o ningún nombre, y no se entera de los cambios de paso ni de los avisos |
| F2-06 | 🟠 Media | pequeño | alta | La fila seleccionada, los bordes de los campos y los de las tarjetas casi no se distinguen del fondo |
| F2-07 | 🟠 Media | medio | media | No hay forma de agrandar el texto, y la ventana mínima no cabe en pantallas comunes con la escala aumentada |
| F2-08 | 🟠 Media | medio | media | En la App Estilo Móvil, cada fila de la lista es una parada de Tab y su casilla no dice de qué archivo es |
| F2-09 | ⚪ Baja | pequeño | alta | En '¿Qué sigue?', la tarjeta enfocada y la de la última herramienta usada se ven iguales |

<details><summary>Detalle técnico y evidencia</summary>

- **F2-01 — En la App Moderna (la que se recomienda con lector de pantalla), el foco del teclado no se ve en la lista de archivos ni en varios botones**
  - *Impacto:* Quien usa solo el teclado pulsa Tab, entra en la lista y no ve ningún cambio. No sabe que está en la lista ni sobre qué fila actúan Espacio o Supr. Pasa lo mismo con 'Quitar seleccionados', 'Quitar todo', 'Deseleccionar' y '¿Qué sigue?'. Puede marcar o quitar archivos sin verlo, justo en la edición que el instalador recomienda a las personas con discapacidad.
  - *Evidencia:* Lo dibujé sin pantalla (QT_QPA_PLATFORM=offscreen): FileList con foco y sin foco → ImageChops.difference(...).getbbox() = None. QPushButton#link con foco es idéntico salvo el antialiasing; #strong conserva el mismo borde de 2 px. pyside/visuals/stylesheet.py:173 'outline: 0' en QTreeWidget, sin regla QTreeWidget:focus; QPushButton:focus (92) pierde ante los selectores de ID #link (118) y #strong (98), que son más específicos.
  - *Recomendación:* Dar un foco propio a cada tipo de control: 'QTreeWidget:focus' con un borde de acento de 2 px, un rectángulo o relleno en la fila actual cuando la lista tiene el foco, y '#link:focus' / '#strong:focus' con un anillo distinto del estado normal. Agregar una prueba que dibuje cada tipo de control con foco y sin foco, en los dos temas, y exija que las imágenes sean distintas.
- **F2-02 — En la App Estilo Móvil (flet), las tarjetas grandes no muestran el foco y el resto de los botones lo muestra casi invisible**
  - *Impacto:* En Inicio, en las tarjetas de 'Elegir' y en '¿Qué sigue?', quien navega con Tab no ve en qué tarjeta está. En los demás botones y en el riel, el único indicio es un velo que apenas se distingue. La persona tiene que adivinar qué hará Enter.
  - *Evidencia:* flet/visuals/look.py:126 tile_style: overlay_color=TRANSPARENT y estados solo para DEFAULT/HOVERED/DISABLED. grep 'FOCUSED\|focus' en flet/visuals da 0 resultados. Calculé el velo por defecto de M3 (10 %): 1,21:1 y 1,32:1 sobre la tarjeta, y 1,09:1 y 1,20:1 sobre el riel. No lo dibujé en flet: el velo débil sale del comportamiento por defecto de Flutter.
  - *Recomendación:* Agregar ft.ControlState.FOCUSED en tile_style, rail_style y button_style, con un borde de acento de 2 px y un anillo claro en el riel, como en ttk. Quitar overlay_color TRANSPARENT, o dejarlo solo para HOVERED. Agregar una prueba que compare los estilos FOCUSED y DEFAULT de cada tipo.
- **F2-03 — En la App Estilo Móvil, el motivo completo de cada archivo en Revisar y Resultados solo se alcanza con el ratón**
  - *Impacto:* El motivo ('Con error: … Quítale la contraseña …') se corta con '…'. El texto completo solo aparece al hacer clic en la fila o al pasar el puntero. Con el teclado no hay forma de elegir otra fila, así que quien no usa ratón nunca sabe qué hacer con sus archivos. Coinciden en el hecho F3-01 y F5-01, que lo ven como un problema de diseño para todos; aquí se trata la parte de teclado.
  - *Evidencia:* Lo volví a comprobar en esta ronda. flet/components/file_list.py:166-167: max_lines=1, ELLIPSIS y tooltip=text.value. :182-189: cada fila es un ft.Container con on_click y sin ink (en flet 1.0.5 no recibe foco). Con checks=False no queda nada enfocable. flet/window/keys.py no maneja las flechas. ttk (file_list_keys.py:24) y Qt (QTreeWidget) sí lo hacen. Captura docs/screenshots/018/2-review-light-en.png.
  - *Recomendación:* La solución de F3-01/F5-01 (el motivo completo, en varias líneas dentro de la fila) arregla también el teclado, y es la que prefiero. Aun así, hacer la lista navegable: flechas arriba y abajo cuando tiene el foco, como en ttk. Agregar a UX §6 la regla 'toda información visible se alcanza con el teclado' y probarla eligiendo la tercera fila solo con el teclado.
- **F2-04 — El texto de color sobre una fila seleccionada y otros colores mezclados no llegan a 4,5:1, y la prueba de contraste no los revisa**
  - *Impacto:* En la App Moderna, el texto ámbar o rojo de una fila seleccionada se lee peor justo cuando la persona lo mira. Lo mismo pasa con el texto de las tarjetas atenuadas en el tema claro y con el aviso 'TERMINADO CON PROBLEMAS' cuando toca la forma decorativa.
  - *Evidencia:* Lo calculé con palette.py y colors.blend. warning sobre la selección: 3,89:1 (tema claro); danger sobre la selección: 3,56:1 (oscuro); dim_text: 3,64:1 (claro); aviso sobre la forma: 4,14:1. tone_delegate.py:1-3 justifica la corrección F3-03 con el caso fácil (5,01:1). La prueba test_brand.py PAIRS solo revisa colores base y usa 'shape' como fondo de selección, pero Qt y flet usan 'selected'.
  - *Recomendación:* Ampliar la prueba a los pares que de verdad se pintan: cada tono sobre 'selected', 'dim_card', 'shape' y 'rail_hover', en los dos temas. En Qt, mostrar el texto de la fila seleccionada en el color normal y conservar la marca lateral del tono. Subir DIM_TEXT a 4,5:1. Evitar que el aviso quede sobre la forma.
- **F2-05 — En la App Moderna, el lector de pantalla oye nombres internos o ningún nombre, y no se entera de los cambios de paso ni de los avisos**
  - *Impacto:* Con NVDA o Narrador, la lista de 'Elegir' se anuncia como 'inputs' (en inglés también en español), y las listas de Revisar y Resultados no tienen nombre. El riel no dice el paso actual. Al terminar, no se anuncia 'Terminado con problemas'. Los avisos y 'Deshacer' aparecen en silencio.
  - *Evidencia:* pyside/components/inputs_card.py:51 setAccessibleName("inputs") es un literal. views/review.py:49 y views/results.py:47 no tienen nombre. rail.py:147-160 marca el paso actual solo con una propiedad de estilo. window/view.py:90 enfoca un QFrame sin nombre. grep 'QAccessible\|updateAccessibility' da 0 resultados. No lo probé con un lector real.
  - *Recomendación:* Sacar del catálogo los nombres accesibles de todas las listas. Marcar el paso actual como 'checked' o con la descripción 'paso actual'. Al cambiar de página, enfocar el título o el aviso de estado y emitir un QAccessibleEvent. Nombrar las flechas de Unir con su documento. Hacer una prueba manual con NVDA siguiendo un guion de cinco pasos antes de seguir afirmando 'funciona mejor con un lector de pantalla'.
- **F2-06 — La fila seleccionada, los bordes de los campos y los de las tarjetas casi no se distinguen del fondo**
  - *Impacto:* Quien ve poco no distingue qué filas están seleccionadas, ni dónde empieza un campo numérico o un desplegable, ni el contorno de las tarjetas de '¿Qué sigue?'.
  - *Evidencia:* Ratios calculados, frente a 3:1 de WCAG 1.4.11. 'selected' frente a la tarjeta: 1,29 y 1,46. 'shape' (ttk): 1,21 y 1,18. 'border' frente a la tarjeta: 1,31 y 1,26; frente al fondo: 1,20 y 1,42. Se usan en QSpinBox/QComboBox (stylesheet.py), TSpinbox (ttk styles.py:140) y en las tarjetas (016/4-what-next-light-en.png).
  - *Recomendación:* Agregar a la paleta un token 'border_strong' (3:1 frente a la tarjeta y el fondo) para los campos editables y las tarjetas pulsables. Marcar la fila seleccionada también con una barra lateral o un borde de acento de 2 px. Incluir estos pares en la prueba ampliada (F2-04).
- **F2-07 — No hay forma de agrandar el texto, y la ventana mínima no cabe en pantallas comunes con la escala aumentada**
  - *Impacto:* Con la escala de Windows al 125 % en una laptop de 1366×768, la ventana es más alta que la pantalla y los botones Siguiente y Convertir quedan detrás de la barra de tareas. El 'Tamaño del texto' de Windows no se respeta y la app no tiene un ajuste propio de tamaño.
  - *Evidencia:* metrics.py: MIN_HEIGHT=624; flet suma 39, es decir, 663 px. 1366×768 al 125 % = 614 px lógicos, menos unos 40 de la barra ≈ 574. Las fuentes están en px fijos (stylesheet.py, typography.py) y no existe un ajuste de tamaño en schemas/settings.py. Es un cálculo; no lo probé en Windows.
  - *Recomendación:* Bajar MIN_HEIGHT para que el total quepa en unos 560 px lógicos (la página ya se desplaza). Agregar Ctrl+'+'/'-' o un ajuste 'Tamaño del texto' (100/125/150 %) que multiplique los tokens de tipografía. Hacer capturas a 1366×768 al 125 %.
- **F2-08 — En la App Estilo Móvil, cada fila de la lista es una parada de Tab y su casilla no dice de qué archivo es**
  - *Impacto:* Con una carpeta de 200 archivos, quien usa el teclado necesita unas 200 pulsaciones de Tab (más en Unir) para llegar a 'Quitar seleccionados'. Con lector de pantalla oye 'casilla, no marcada' una y otra vez, sin el nombre del archivo.
  - *Evidencia:* Lo volví a comprobar: flet/components/file_list.py:178 ft.Checkbox(value=False, on_change=…) sin label ni semantics_label, y el nombre está en otro ft.Text. Cada IconButton de order_buttons.py es una parada más. En Qt, la lista es una sola parada. No lo medí en ejecución.
  - *Recomendación:* Dar a cada casilla el nombre de su archivo (semantics_label o ft.Semantics). Hacer que la lista sea una sola parada: flechas dentro de la lista y Tab para salir. Probar con 50 filas que basten tres Tab para llegar a 'Quitar seleccionados'.
- **F2-09 — En '¿Qué sigue?', la tarjeta enfocada y la de la última herramienta usada se ven iguales**
  - *Impacto:* En la App Moderna, al pulsar Tab hasta 'Dividir', esa tarjeta toma el mismo borde que 'Convertir de nuevo', que lo lleva por ser la última herramienta usada. La persona ve dos tarjetas marcadas y no sabe cuál abrirá Enter.
  - *Evidencia:* pyside/visuals/stylesheet.py:110 '#smallTile[current="true"] { border: 2px solid accent }' y :112 '#smallTile:focus' son idénticos. views/dialogs/what_next.py:60. Captura 016/4-what-next-light-en.png.
  - *Recomendación:* Usar dos señales distintas: una etiqueta 'La última que usaste' para la herramienta reciente y un anillo exterior para el foco.

</details>

### Frontend · Estilo visual UI/UX — 6,8/10

Tras leer a los diez auditores, mantengo el veredicto de la ronda 1: la identidad visual (ADR-0027) es sólida y se repite bien en las tres ventanas. Los problemas están en cómo se muestra lo que importa. Hay tres fallas que confirmaron, cada uno por su lado, varios colegas de las dos juntas (F2-03, F5-01, F5-04, F5-05, F5-06, F4-09). (1) El motivo y el «qué hacer» de cada archivo quedan cortados en Revisar y Resultados en las tres ventanas, y en flet solo se leen con el ratón. Volví a mirar el código: file_list.py corta cada celda a una línea y deja el texto entero solo en el tooltip. (2) En Elegir, la lista de archivos de la persona es lo que menos espacio recibe. (3) Los colores de estado no dicen lo mismo en todas partes. flet pinta en teal «Terminado con problemas», porque surface.show_header no tiene parámetro de advertencia. Y los contadores salen en ámbar por defecto: stat() usa Tone.WARNING, así que «Conservado» parece un problema. Junté con mis hallazgos los de colegas que tratan el mismo defecto visual, para no contar dos veces una misma falla. No subí ninguna severidad. Nota: 6,8, igual que en la ronda 1.

**Fortalezas que vio:**

- El riel con los cuatro pasos y el paso actual resaltado orienta siempre a la persona, en las tres ventanas y en los dos temas (docs/screenshots/007, 016, 018).
- El encabezado de cada página (contador de paso con su estado, título y una línea de explicación) es igual en todas las páginas y amable.
- Hay una sola acción principal, abajo a la derecha, con «Volver» como secundaria: el flujo se entiende sin leer la Ayuda.
- Las tarjetas de cifras dan el resumen de un vistazo antes del detalle.
- Los íconos de archivo propios (PDF, W, X, carpeta) son los mismos en las tres ventanas.
- El modo oscuro está bien resuelto y el teal claro funciona como acento.
- La rejilla de 8 px y los tokens compartidos (metrics.py, typography.py, palette.py) hacen que las tres ventanas se parezcan de verdad, y se respeta el mínimo de 14 px.
- Inicio, con tres herramientas grandes y la frase «Tus originales nunca se modifican», da una primera impresión clara y tranquilizadora.
- Los estados nunca se indican solo con color: siempre van con una palabra o un símbolo (lo confirma F2).

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F3-01 | 🔴 Alta | medio | alta | El motivo y lo que hay que hacer quedan cortados en Revisar y Resultados (en flet, solo se leen con el ratón) |
| F3-02 | 🔴 Alta | medio | alta | En Elegir, la lista de archivos tiene menos espacio que las opciones |
| F3-03 | 🟠 Media | pequeño | alta | Opciones mal agrupadas y un título incompleto («Los Resultados Van») |
| F3-04 | 🟠 Media | pequeño | alta | Los números no cuadran: «Listos para convertir: 5» y después «1 de 6» |
| F3-05 | 🟠 Media | medio | alta | Las rutas se muestran como texto técnico y se cortan por la parte que importa |
| F3-06 | 🟠 Media | pequeño | alta | Los colores de estado no coinciden: «Terminado con problemas» sale en verde en flet, y «Conservado» y los omitidos informativos salen en ámbar |
| F3-07 | 🟠 Media | pequeño | media | Jerarquía tipográfica plana: los títulos de sección y de diálogo se ven como texto normal |
| F3-08 | ⚪ Baja | pequeño | alta | Botones secundarios con tres estilos distintos, y controles visibles que no hacen nada («Convertir» gris al convertir, «Deseleccionar Todo» con la lista vacía) |
| F3-09 | ⚪ Baja | pequeño | alta | Riel lateral con detalles sin terminar: íconos que faltan, pie partido y bloqueo distinto en cada ventana |
| F3-10 | ⚪ Baja | pequeño | alta | Ajustes: contenido cortado sin señal de desplazamiento, casillas alineadas distinto y capturas del instalador desactualizadas |

<details><summary>Detalle técnico y evidencia</summary>

- **F3-01 — El motivo y lo que hay que hacer quedan cortados en Revisar y Resultados (en flet, solo se leen con el ratón)**
  - *Impacto:* La persona ve «Con error: Este archivo está protegido con contraseña. Quít…» y no lee la instrucción que la saca del problema. Para leerla tiene que hacer clic en la fila, y nada le indica que puede hacerlo. En la App Estilo Móvil el texto completo solo aparece al pasar el ratón por encima, y con el teclado no se puede elegir otra fila. En la App Clásica el texto se corta en seco, sin puntos suspensivos, y parece un error de la aplicación.
  - *Evidencia:* docs/screenshots/018/4-results-light-es.png, 016/4-results-dark-es.png, 007/4-results-light-es.png y 2-review-*-es.png. Lo revisé de nuevo en flet/components/file_list.py:166-168: `text.max_lines, text.overflow = 1, ft.TextOverflow.ELLIPSIS` y `text.tooltip = text.value`, de modo que el texto completo solo existe en el tooltip. La fila es un ft.Container con on_click y sin foco (líneas 183-190). pyside/views/results.py y flet/views/results.py no preseleccionan ninguna fila (decisión 039). F5-01 midió el caso difícil: error.worker_crashed con {report} suma unas 65 palabras. F2-03 añade que el teclado no puede llegar a las filas de flet.
  - *Recomendación:* En las listas de problemas, mostrar el motivo completo en dos o tres líneas por fila, o una segunda línea con el «qué hacer» debajo del nombre. La línea de detalle de abajo puede quedarse, pero no como única forma de leerlo. Mientras tanto, como mínimo, poner «Elige una fila para ver qué hacer» bajo la tabla. Hacer que las filas de flet reciban foco con el teclado (F2-03). Probarlo con worker_crashed en español, una ventana de 800 px y fuentes de Windows.
- **F3-02 — En Elegir, la lista de archivos tiene menos espacio que las opciones**
  - *Impacto:* Justo después de agregar archivos, la persona apenas ve lo que agregó: 2 filas en la App Clásica, unas 3 y media en la Moderna y 4 y media en flet. En su lugar ve decisiones técnicas que la primera vez no entiende («Resumen del Proceso», «Imágenes»), y que ya existen en Ajustes. La pantalla parece un formulario, no la lista de sus documentos.
  - *Evidencia:* docs/screenshots/007/1-choose-dark-es.png y 1-choose-compact-light-es.png, 016/1-choose-light-es.png y 018/1-choose-light-es.png (la última fila sale cortada). 016/1-choose-split-800-light-es.png (la ayuda de Dividir queda cortada). metrics.py: START_HEIGHT=720. F5-05 llega a la misma conclusión desde el texto y cita ADR-0031 y ADR-0033, que pusieron esas opciones en el paso 1.
  - *Recomendación:* Dar a la lista un mínimo de 5 filas completas a 720 px de alto. En Elegir, dejar solo «Dónde guardar» y pasar Imágenes y Resumen a una línea de resumen («Resumen en Markdown · sin imágenes — Cambiar») o a un bloque plegado «Más opciones». Esto pide revisar ADR-0031 y ADR-0033. El motivo: las opciones siguen a un clic, pero ya no tapan lo principal.
- **F3-03 — Opciones mal agrupadas y un título incompleto («Los Resultados Van»)**
  - *Impacto:* «Imágenes» está en la misma fila que el título «Los Resultados Van», así que parece parte de esa pregunta. En Dividir pasa lo mismo con «Guardar:» junto a «Cómo Dividir». «Los Resultados Van» es una frase a la que le falta el final. «Elegir Carpeta…» se ve activo aunque esté marcado «Junto a los originales».
  - *Evidencia:* Volví a comprobarlo: es.toml:594 output_title = "Los Resultados Van", mientras que es.toml:603 ya usa «¿Dónde Van los Resultados?». Capturas 018/1-choose-light-es.png, 1-choose-split-light-es.png y 016/1-choose-light-es.png. flet/components/output_card.py:63-65. F5-08 señala la misma frase incompleta.
  - *Recomendación:* Una pregunta por fila, sin compartirla con otra. Usar el título «Dónde Guardar los Resultados» (en Title Case). Atenuar «Elegir Carpeta…», o mostrar la carpeta elegida, según la opción marcada.
- **F3-04 — Los números no cuadran: «Listos para convertir: 5» y después «1 de 6»**
  - *Impacto:* La tarjeta promete 5 conversiones y el contador cuenta hasta 6. La persona piensa que se convertirá un archivo de más, justo en el momento en que necesita confiar en la app.
  - *Evidencia:* 018/3-convert-ready-light-es.png frente a 018/3-convert-dark-es.png y 016/3-convert-light-es.png. presenter/chrome/secondary.py:56-61 (written = new) frente a backend/use_cases/execution.py:106 (total = len(plan.conversions), que incluye el archivo conservado).
  - *Recomendación:* Que el progreso cuente lo mismo que la tarjeta, o que la tarjeta diga «6 archivos: 5 se convierten, 1 se conserva». Probarlo también con el caso de 0 por convertir.
- **F3-05 — Las rutas se muestran como texto técnico y se cortan por la parte que importa**
  - *Impacto:* En flet, todas las filas de Elegir muestran el mismo comienzo «C:\Users\…\AppData\Local\Te…» y la persona no distingue de qué carpeta viene cada archivo. En Resultados aparece un bloque de rutas completas que parece información del sistema, y con 4 carpetas «Abrir Carpeta de Resultados» abre una ventana del explorador por cada una (F5-03).
  - *Evidencia:* 018/1-choose-light-es.png (las 5 filas iguales), 018/4-results-light-es.png (4 rutas). presenter/screens/choose.py:56-60 devuelve str(path.parent) completo; flet/components/file_list.py:167 corta por el final. Revisar sí muestra solo el nombre de la carpeta (016/2-review-light-es.png), una incoherencia que señala F5-06. Las capturas de Qt usan rutas cortas de /tmp y no muestran el caso difícil.
  - *Recomendación:* Recortar por el centro o mostrar el nombre de la carpeta, como en Revisar, con la ruta completa en el detalle. En Resultados, una lista corta de carpetas, cada una con su propio «Abrir». Tomar las capturas de referencia con rutas largas de Windows.
- **F3-06 — Los colores de estado no coinciden: «Terminado con problemas» sale en verde en flet, y «Conservado» y los omitidos informativos salen en ámbar**
  - *Impacto:* En flet, el encabezado de un resultado con problemas sale en el teal del éxito, mientras que las otras dos ventanas lo muestran en ámbar. A la vez, «1 Conservado» (algo que la persona eligió) y «2 Omitidos» (por ejemplo, un archivo que ya era Markdown) salen en ámbar de advertencia en las tres ventanas, mientras sus filas tienen un tono tranquilo. El color dice lo contrario de lo que pasó.
  - *Evidencia:* Lo comprobé de nuevo. flet/components/surface.py:51 `def show_header(self, *, eyebrow, title, subtitle)` no tiene parámetro de advertencia, y flet/window/view.py:172-174 no lo pasa, a diferencia de pyside/window/view.py. presenter/screens/review.py:58 `def stat(..., tone: Tone = Tone.WARNING)`, que results.py:65 y :69 usan para stat_skipped y stat_kept: todo valor distinto de cero sale en ámbar. Capturas 018/4-results-light-es.png frente a 016/4-results-dark-es.png, y 016/4-results-light-es.png («Conservado» en ámbar). Esto incorpora F5-04.
  - *Recomendación:* Que el encabezado de flet use el tono de advertencia igual que Qt y ttk. «Conservado» siempre en neutro. «Omitidos» en ámbar solo si alguno pide una acción (no está en INFORMING). Una prueba de paridad que compare el tono del estado FINISHED_WITH_PROBLEMS en las tres ventanas, y otra con un lote cuyo único omitido sea un .md.
- **F3-07 — Jerarquía tipográfica plana: los títulos de sección y de diálogo se ven como texto normal**
  - *Impacto:* Fuera del título de la página, casi todo mide 14 px y solo cambia la negrita. Al ojo le cuesta encontrar dónde empieza cada bloque. El mismo diálogo de Ajustes tiene título grande en la App Clásica y pequeño en flet.
  - *Evidencia:* design/typography.py: BODY=SMALL=STRONG=EYEBROW=14; solo TITLE=24 y SUBTITLE=16. 018/6-settings-light-es.png frente a 007/6-settings-dark-es.png; 018/4-what-next-light-es.png; 018/5-help-light-es.png.
  - *Recomendación:* Añadir un nivel intermedio de tamaño (unos 18 px para los títulos de diálogo y 16 px para los de sección) y usarlo igual en las tres ventanas. Ningún texto baja de 14 px. Si se adopta el factor de tamaño de texto que propone F2-07, conviene diseñar los dos cambios juntos.
- **F3-08 — Botones secundarios con tres estilos distintos, y controles visibles que no hacen nada («Convertir» gris al convertir, «Deseleccionar Todo» con la lista vacía)**
  - *Impacto:* «Volver» es blanco y «¿Qué Sigue?» tiene contorno en una ventana y relleno en otra. Durante la conversión, «Cancelar» parece secundario al lado de un «Convertir» gris que no sirve. En Elegir, «Deseleccionar Todo» sale en verde y activo sobre una lista vacía, en la pantalla más visitada: invita a pulsar algo que no hace nada.
  - *Evidencia:* 018/2-review-light-es.png, 018/4-results-light-es.png, 007/4-results-light-es.png, 018/3-convert-dark-es.png y 016/3-convert-light-es.png. Lo de «Deseleccionar» viene de F4-09 y lo comprobé en las tres ventanas: grep de `.deselect` en frontend solo encuentra su creación, su etiqueta y su colocación (pyside, ttk y flet inputs_card.py); en ningún lugar se activa o desactiva, a diferencia de remove (flet/window/keys.py:62 lee remove.disabled). Captura 016/1-choose-empty-light-es.png.
  - *Recomendación:* Un solo estilo de botón secundario, definido como token. Durante la conversión, ocultar el botón principal y dejar «Cancelar» solo, sin confirmación. Desactivar «Deseleccionar Todo» mientras no haya nada marcado, con la misma regla que los otros dos botones, en las tres ventanas. Quitar el texto duplicado de la barra (es.toml:528).
- **F3-09 — Riel lateral con detalles sin terminar: íconos que faltan, pie partido y bloqueo distinto en cada ventana**
  - *Impacto:* En el riel ancho, «Ajustes» y «Ayuda» no tienen ícono; en el compacto aparecen como los caracteres ⚙ y ?. El pie «100 % local · nada sale de tu equipo» se parte en varias líneas y usa «equipo» donde el resto de la app dice «computador». Inicio y Ajustes se atenúan durante la conversión en Qt y no en flet.
  - *Evidencia:* 018/0-home-light-es.png, 016/0-home-light-es.png, 007/0-home-dark-es.png, 016/1-choose-split-800-light-es.png; flet/components/rail.py:151-152; es.toml:509 frente a :491, :565 y :624; 016/3-convert-light-es.png frente a 018/3-convert-dark-es.png.
  - *Recomendación:* Dibujar el engranaje y la ayuda con tool_art, como el ícono de Inicio. Dejar el pie en una sola línea y usar siempre «computador». Que las tres ventanas bloqueen lo mismo durante una tarea, decidido en presenter/chrome (lo mismo que piden F1-06 y F1-07).
- **F3-10 — Ajustes: contenido cortado sin señal de desplazamiento, casillas alineadas distinto y capturas del instalador desactualizadas**
  - *Impacto:* En flet, el diálogo de Ajustes no muestra barra de desplazamiento y corta el contenido a media frase: la persona no sabe que hay más debajo. Las casillas se alinean distinto en cada ventana. Las capturas del instalador muestran textos que ya no existen, así que el dueño revisa con imágenes viejas.
  - *Evidencia:* 018/6-settings-light-es.png, 016/6-settings-1366x768-light-es.png, 007/6-settings-dark-es.png. docs/screenshots/019/06-parts-spanish.png («ClearMD (ttk)») frente a packaging/installer/clearmd.iss:125-126. F4-08 confirma lo de las capturas y propone generarlas en CI.
  - *Recomendación:* En flet, una barra de desplazamiento siempre visible o un degradado al pie. Alinear las casillas con los desplegables en las tres ventanas. Describir el resumen con palabras, no con el nombre de archivo. Regenerar las capturas del instalador en el flujo de publicación (F4-08).

</details>

### Frontend · Primer uso, instalación e idioma — 7/10

Después del debate mantengo el juicio de la primera ronda: el primer uso de ClearMD está muy por encima de lo habitual. Hay una tabla clara de qué descargar, el instalador es por usuario y no pide administrador, la edición liviana no rompe lo que ya está instalado, y una instalación en español deja la app en español. Las grietas siguen en los primeros minutos. Tres auditores encontraron por separado que «Copiar Detalles» manda a GitHub Issues, y lo volví a comprobar en el catálogo: contradice la decisión del dueño y la promesa de la 2.12.0. El acceso directo de la Línea de Comandos, que encontró B5, falla con la instalación por defecto: la opción PATH viene desmarcada y la instrucción «Type: clearmd-cli» está en inglés. Lo comprobé en el script del instalador y lo sumo a mi informe. También confirmé en el código que el botón «Deseleccionar Todo» nunca se apaga en ninguna de las tres ventanas, y que en la App Clásica el aviso de ajustes dañados al arrancar queda oculto en Inicio (F1-03). Bajo a media la gravedad de «para qué sirve ClearMD» (F4-01): F5 la vio igual, pero estar de acuerdo no confirma la gravedad, y quien instala llega desde un README y una página de descarga que sí lo dicen. Nada de esto pierde datos. Todo afecta la confianza justo cuando la persona decide si se queda con la app, y casi todo se arregla en poco tiempo. Nota: 7/10.

**Fortalezas que vio:**

- La tabla «Qué Descargar» de las notas de versión dice primero qué archivo necesita la mayoría, a quién le sirve el completo (lectores de pantalla) y cómo desinstalar cada uno.
- El instalador es por usuario y no pide administrador (PrivilegesRequired=lowest): no sale la pregunta de Control de Cuentas que asusta a cualquiera.
- El instalador liviano nunca toca las otras partes ya instaladas. Si la persona las tiene, le dice qué archivo usar y no cambia nada.
- Una instalación en español deja la app en español sin romper ADR-0017: solo escribe el idioma si no hay configuración previa.
- Al terminar, el instalador ofrece «Abrir ClearMD ahora» (marcado), y el desinstalador conserva la configuración por defecto y dice que los documentos y las carpetas ClearMD_Output nunca se tocan.
- El instalador describe cada app con franqueza (peso, a quién le sirve, que la App Clásica no la lee un lector de pantalla). B5 y F2 coinciden en esto.
- La pantalla de Inicio tiene tres tarjetas claras y repite que nada sale del computador y que los originales nunca cambian.
- La Ayuda explica «Qué es Markdown» y «Usarlo con tu IA» en palabras sencillas, y la configuración se recuerda entre sesiones.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F4-02 | 🔴 Alta | pequeño | alta | «Copiar Detalles» sigue mandando a GitHub Issues, que exige cuenta |
| F4-11 | 🟠 Media | pequeño | alta | El acceso directo de la Línea de Comandos indica un comando que no funciona con la instalación por defecto |
| F4-01 | 🟠 Media | pequeño | alta | Las primeras pantallas no dicen para qué sirve ClearMD ni qué es Markdown |
| F4-05 | 🟠 Media | pequeño | media | El instalador liviano tiene demasiadas pantallas, con una licencia en inglés que hay que aceptar y textos mal cerrados |
| F4-03 | 🟠 Media | pequeño | alta | Los botones de idioma de la Bienvenida no muestran el activo, y el texto de abajo manda a Ajustes |
| F4-04 | 🟠 Media | pequeño | alta | Nadie le dice a la persona cómo actualizar ClearMD |
| F4-06 | 🟠 Media | pequeño | alta | Las novedades de la página de descarga mezclan inglés y español en cada párrafo |
| F4-07 | 🟠 Media | pequeño | alta | El README transmite «obra en construcción» y no avisa de la advertencia de Windows junto al botón de descarga |
| F4-08 | ⚪ Baja | medio | alta | Las capturas del instalador muestran uno que ya no se distribuye, y nadie revisa el actual |
| F4-09 | ⚪ Baja | pequeño | alta | «Deseleccionar Todo» parece activo en las tres ventanas aunque no haya nada marcado |

<details><summary>Detalle técnico y evidencia</summary>

- **F4-02 — «Copiar Detalles» sigue mandando a GitHub Issues, que exige cuenta**
  - *Impacto:* Justo cuando algo falló y la persona quiere pedir ayuda, el mensaje que aparece al pulsar Copiar Detalles reemplaza al anterior, que ofrecía el correo. El nuevo le pide pegar el texto en una página de GitHub que exige cuenta. Eso contradice la versión 2.12.0 («reportar ya no exige cuenta») y la decisión del dueño.
  - *Evidencia:* Volví a comprobar en el catálogo: en.toml:511 y es.toml:512, gui.app.details_copied «…Pégalo en github.com/ClearNote97/ClearMD/issues.». En cambio, [report].how y unexpected_error usan Discussions o el correo. presenter/intents/reset.py:78 lo muestra con show_message, que reemplaza el mensaje anterior. B5-04 y F5-02 lo encontraron por separado.
  - *Recomendación:* Que details_copied use el mismo {report} que los demás mensajes (comunidad o correo). Agregar una prueba que recorra en.toml y es.toml y falle si algún texto visible contiene «/issues». Probar el texto exacto que se ve después de pulsar Copiar Detalles en las tres ventanas.
- **F4-11 — El acceso directo de la Línea de Comandos indica un comando que no funciona con la instalación por defecto**
  - *Impacto:* Quien instala la Línea de Comandos (edición completa) y abre su acceso directo ve la ayuda y debajo «Type: clearmd-cli "<folder or file>"», en inglés aunque haya instalado en español. Como la opción PATH viene desmarcada y la consola abre en Documentos, al escribir eso Windows responde que «clearmd-cli» no se reconoce. La propia ayuda dice «usage: clearmd», otro nombre. La primera experiencia es un error.
  - *Evidencia:* Lo comprobé en el script: packaging/installer/clearmd.iss:245 y :254, Parameters '/k ""{app}\clearmd-cli.exe"" --help & echo. & echo Type: clearmd-cli ...', WorkingDir {userdocs}, texto fijo fuera de CustomMessages. clearmd.iss:204, tarea addpath con Flags: unchecked. cli/parser.py:14 prog="clearmd". No lo ejecuté en Windows. Tomado de B5-02 y vuelto a comprobar.
  - *Recomendación:* Sacar la línea de ejemplo a CustomMessages en los dos idiomas. Hacer que funcione sin PATH: abrir la consola en {app} o mostrar el ejemplo con la ruta completa. Que la ayuda use el nombre real del ejecutable (clearmd-cli en Windows). Probar en una máquina limpia con PATH desmarcado.
- **F4-01 — Las primeras pantallas no dicen para qué sirve ClearMD ni qué es Markdown**
  - *Impacto:* Una persona que nunca ha oído «Markdown» lee «Convertir a Markdown» y «Documentos a Markdown» sin saber para qué le sirve. La promesa que la trajo («prepara tus documentos para la IA») desaparece al instalar y solo vuelve en la Ayuda o en Resultados.
  - *Evidencia:* es.toml:621-631 gui.home: título «¿Qué Quieres Hacer?», subtítulo sobre privacidad, convert_body con la lista de formatos. gui.welcome.intro «Convierte, divide o une tus documentos así:». La palabra IA solo aparece en la Ayuda, Resultados, Dividir y el resumen. F5-09 lo confirma de forma independiente.
  - *Recomendación:* Una frase de propósito en la Bienvenida y en el subtítulo de Inicio, por ejemplo «Convierte tus documentos en texto que tu IA entiende mejor (Markdown). Nada sale de tu computador.», y «listo para tu IA» en la tarjeta Convertir. Una prueba de catálogo que exija la mención en gui.home y gui.welcome en los dos idiomas.
- **F4-05 — El instalador liviano tiene demasiadas pantallas, con una licencia en inglés que hay que aceptar y textos mal cerrados**
  - *Impacto:* Para instalar una sola app, la persona pasa por siete pantallas, entre ellas una licencia legal en inglés con «Acepto» obligatorio, también en español, y una ruta técnica de AppData. La pantalla final en español dice «Completando la Instalación», un calco del inglés. Al desinstalar, la pregunta en español abre «¿» y no la cierra, y la inglesa no lleva «?».
  - *Evidencia:* Comprobado en clearmd.iss: línea 53 LicenseFile={#Root}\LICENSE, sin DisableDirPage ni DisableReadyPage. Línea 94 spanish.FinishedHeadingLabel=«Completando la Instalación de [name]» (lo señaló B5-09). Líneas 165-166 RemoveSettings sin signo de cierre. No lo ejecuté en Windows.
  - *Recomendación:* En la edición liviana: quitar la página de licencia (dejar LICENSE instalado y enlazado en la Ayuda), DisableDirPage=yes y DisableReadyPage=yes. Cambiar a «Instalación Terminada» y cerrar las dos preguntas del desinstalador.
- **F4-03 — Los botones de idioma de la Bienvenida no muestran el activo, y el texto de abajo manda a Ajustes**
  - *Impacto:* La persona ve «English» y «Español» iguales y no sabe cuál está puesto ni si su clic funcionó. Debajo, un texto le dice que cambie el idioma en Ajustes: dos instrucciones opuestas en la primera pantalla. Cada ventana pone los botones en un sitio distinto, y en la App Estilo Móvil van junto a «Empezar».
  - *Evidencia:* pyside/views/dialogs/welcome.py:33-36, ttk/views/dialogs/welcome.py:50-63 y flet/views/dialogs/welcome.py:31-34. Las tres reutilizan gui.help.language y ninguna marca el idioma actual. Capturas 016/0-welcome-light-en.png, 018/0-welcome-light-es.png y 007/0-welcome-light-es.png.
  - *Recomendación:* Marcar el idioma activo (estilo primario o presionado, con estado «seleccionado» en Qt), cambiar la línea de Ajustes por una etiqueta «Idioma · Language» y poner los botones en el mismo lugar en las tres ventanas, nunca junto a «Empezar».
- **F4-04 — Nadie le dice a la persona cómo actualizar ClearMD**
  - *Impacto:* ClearMD no usa internet y por eso nunca avisa de una versión nueva, lo cual está bien. Pero ni la Ayuda, ni el README, ni las notas de versión explican dónde está la versión nueva, que basta con instalar encima ni que la configuración se conserva. Quien vuelve meses después se queda con la versión vieja sin saberlo.
  - *Evidencia:* Un grep de «updat\|new version\|latest\|releases» en en.toml no da nada. README.md solo trata la desinstalación. La tabla what-to-download de RELEASE_NOTES.md no tiene fila para «ya tengo ClearMD».
  - *Recomendación:* Una sección «Versiones Nuevas» en la Ayuda (dónde descargar, ejecutar el mismo instalador encima, la configuración se conserva) y una fila en «Qué Descargar» para quien ya tiene ClearMD o la edición completa. Opcional: un botón que abra esa página solo cuando la persona lo pulse.
- **F4-06 — Las novedades de la página de descarga mezclan inglés y español en cada párrafo**
  - *Impacto:* Lo primero que lee la persona después de la tabla es un muro de viñetas largas, cada una con su inglés y su español intercalados. A los dos lectores les sobra la mitad y les cuesta encontrar su idioma.
  - *Evidencia:* packaging/RELEASE_NOTES.md, «New in 2.12.0 / Novedades de la 2.12.0» (viñetas de 6 a 9 líneas), lo mismo en 2.9.0-2.11.0. packaging/release_notes.py arma con eso la página. B5-09 llegó a lo mismo.
  - *Recomendación:* Dejar la tabla y debajo dos bloques separados (English, Español) de 3 a 5 líneas cortas, con el detalle en un <details>. Quitar las novedades de versiones anteriores.
- **F4-07 — El README transmite «obra en construcción» y no avisa de la advertencia de Windows junto al botón de descarga**
  - *Impacto:* Junto al botón de descarga, la persona ve insignias técnicas y una etiqueta naranja «estado: en construcción» en la versión 2.12. Eso resta confianza justo antes de que Windows le diga «programa no reconocido», y el aviso para seguir («Más información → Ejecutar de todas formas») está unas 170 líneas más abajo.
  - *Evidencia:* Comprobado: README.es.md:20 tiene la insignia «estado-en construcción-orange» (lo mismo en README.md:20). La advertencia de SmartScreen solo está en README.md:189 y README.es.md:192. B5-05 confirma otros datos viejos del README (los conteos de ADR y el valor por defecto de --html).
  - *Recomendación:* Cambiar la insignia por la versión publicada o quitarla. Poner una línea bajo el botón que avise de SmartScreen mientras no haya firma. Bajar las insignias técnicas a la sección para desarrolladores.
- **F4-08 — Las capturas del instalador muestran uno que ya no se distribuye, y nadie revisa el actual**
  - *Impacto:* El dueño no puede ejecutar el instalador en su máquina. Las capturas guardadas muestran «ClearMD (ttk)», «se desempaca al iniciar», solo dos apps y ninguna casilla «Abrir ClearMD ahora». Fallos como los de F4-05 y F4-11 pasan sin que nadie los vea.
  - *Evidencia:* docs/screenshots/019/, con último commit del 2026-11-05. 02-parts-light.png y 06-parts-spanish.png frente a clearmd.iss:125-126. installer-look.yml ya sabe tomar capturas (shoot.ps1), pero release.yml no las genera. F3-10 lo confirma.
  - *Recomendación:* Que el flujo de publicación tome capturas de cada página de los dos instaladores, en inglés y en español, en cada etiqueta, y las adjunte. Que la revisión visual forme parte del criterio para publicar.
- **F4-09 — «Deseleccionar Todo» parece activo en las tres ventanas aunque no haya nada marcado**
  - *Impacto:* La primera vez que la persona entra a Elegir, ve dos botones apagados y uno activo, «Deseleccionar Todo», encima de una lista vacía. Pulsarlo no hace nada. Es un control sin acción en la pantalla más visitada.
  - *Evidencia:* Re-comprobado en las tres ventanas: pyside/components/inputs_card.py:66, ttk/components/inputs_card.py:64 y flet/components/inputs_card.py:41 crean self.deselect, y un grep en src/clearmd/frontend no encuentra ningún sitio que lo desactive. Captura 016/1-choose-empty-light-es.png. En la ronda 1 lo había revisado solo en Qt.
  - *Recomendación:* Apagarlo mientras no haya nada marcado, con la misma regla que «Quitar lo Seleccionado», en las tres ventanas. Probar con la lista vacía y con archivos sin ninguno marcado.

</details>

### Frontend · Claridad es cariño — 6,8/10

El debate confirma mi lectura de la primera ronda. El catálogo de textos es bueno, pero lo que la persona ve en pantalla a menudo no dice la verdad completa, o la dice cortada. Tres auditores llegamos por separado a lo mismo: en Revisar y Resultados, el «qué hacer» queda cortado con puntos suspensivos y en flet solo se ve con el ratón (F3-01, F2-03). Otros tres comprobamos que Copiar Detalles manda a /issues, que exige cuenta (B5-04, F4-02); lo volví a verificar en es.toml:512 y en.toml:511. La mesa de backend me hizo ver un hueco que agrego: un resultado vacío se anuncia con el titular «El documento se convirtió», y la nota de PDF escaneado no dice qué hacer. Volví a verificar en el código que en flet el encabezado «Terminado con problemas» sale sin tono de advertencia (view.py:172, a diferencia de Qt), y lo sumo a mi hallazgo de tonos. No subo ninguna severidad. Uno los calcos y el glosario en un solo hallazgo. Nota: 6,8/10. Los textos son cariñosos, pero el cariño se pierde entre el catálogo y la pantalla.

**Fortalezas que vio:**

- Cada error y cada omisión tiene mensaje y acción en lenguaje llano, con el límite y el valor medido cuando aplica (skip.too_large, skip_action.old_office, error.empty_file). Cumple UX §3.
- Tranquiliza en el momento justo: «Nada se escribe hasta que confirmes», «lo ya terminado se conserva», «Tus originales nunca se modifican».
- Resultados dice dónde están los archivos y cómo usarlos con la IA (gui.result.where, gui.result.with_ai).
- El diálogo de cerrar durante una tarea explica qué se conserva y qué no, sin asustar; Cancelar nunca pide confirmación.
- Quitar Todo se puede deshacer y lo avisa.
- Title Case consistente en títulos y botones, con conectores en minúscula y opciones en tipo oración.
- Las filas solo informativas (ya es Markdown, ya incluido) se muestran en tono neutro y van después de las que piden algo (presenter/screens/results.py:40-46, INFORMING).
- La protección de privacidad al reportar («copia solo el detalle técnico») y el ocultador de rutas en Copiar Detalles.
- Español neutro y cálido, con singular y plural bien resueltos.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F5-01 | 🔴 Alta | medio | alta | En Revisar y Resultados, el «qué hacer» de un error queda cortado y escondido |
| F5-02 | 🔴 Alta | pequeño | alta | «Copiar Detalles» manda a una página que exige cuenta y borra la opción del correo |
| F5-11 | 🟠 Media | pequeño | alta | Un resultado vacío se anuncia con «El documento se convirtió», y la nota de PDF escaneado no dice qué hacer |
| F5-03 | 🟠 Media | pequeño | alta | Abrir los resultados abre una ventana del explorador por cada carpeta |
| F5-04 | 🟠 Media | pequeño | alta | El color de los estados dice cosas distintas: contadores en naranja sin problema y «Terminado con problemas» en verde en flet |
| F5-05 | 🟠 Media | medio | media | El paso 1 pide decisiones técnicas antes de que la persona vea su lista |
| F5-06 | 🟠 Media | pequeño | alta | La columna «Carpeta» del paso 1 se corta por el final y todas las filas se ven iguales |
| F5-07 | ⚪ Baja | pequeño | alta | Una misma idea recibe varios nombres, y quedan calcos y frases cojas |
| F5-09 | ⚪ Baja | pequeño | alta | La Bienvenida y el Inicio no dicen para qué sirve el resultado |
| F5-10 | ⚪ Baja | pequeño | media | «Esperando tu decisión» aparece aunque no haya nada que decidir |

<details><summary>Detalle técnico y evidencia</summary>

- **F5-01 — En Revisar y Resultados, el «qué hacer» de un error queda cortado y escondido**
  - *Impacto:* La persona ve «Con error: Este archivo está protegido con contraseña. Quítale la …» y no lee la instrucción que la saca del problema. Para leerla tiene que hacer clic en la fila, y nada le indica que puede hacerlo. En la App Estilo Móvil el texto completo solo aparece al pasar el ratón, y con el teclado no se puede elegir otra fila. Justo la pantalla que responde «¿qué hago?» no lo responde.
  - *Evidencia:* flet/components/file_list.py:166-168 (max_lines=1, ELLIPSIS, tooltip=value; lo volví a verificar en esta ronda). pyside/views/results.py:58 deja el detalle vacío hasta el clic. Capturas 016/4-results-light-es.png, 018/4-results-light-es.png y 007/4-results-light-es.png. El caso difícil es error.worker_crashed con {report}: unas 65 palabras, medido con load_catalog. F3-01 y F2-03 lo confirman de forma independiente.
  - *Recomendación:* Mantener la decisión de no preseleccionar ninguna fila, pero dejar que «Qué Pasó» ocupe dos o tres líneas, o poner la acción en una segunda línea dentro de cada fila. Como mínimo, poner bajo la tabla «Elige una fila para ver qué hacer». En flet, hacer que las filas se puedan recorrer con las flechas (F2-03). La prueba debe usar el mensaje más largo del catálogo en español, a 800 px de ancho.
- **F5-02 — «Copiar Detalles» manda a una página que exige cuenta y borra la opción del correo**
  - *Impacto:* Ante un error inesperado, el mensaje ofrece la comunidad o un correo sin cuenta. Al pulsar Copiar Detalles, ese mensaje se reemplaza por «Pégalo en github.com/ClearNote97/ClearMD/issues», que exige cuenta de GitHub. La persona sin cuenta pierde la opción del correo justo cuando quiere ayudar. La versión 2.12.0 promete lo contrario.
  - *Evidencia:* es.toml:512 y en.toml:511 details_copied con «/issues» (grep repetido en esta ronda: solo esas dos líneas). [report] how manda a /discussions o al correo. presenter/intents/reset.py:78 sustituye el mensaje anterior. unexpected_error con {report} suma 64 palabras. Confirmado también por B5-04 y F4-02.
  - *Recomendación:* Que details_copied reutilice {report}. Por ejemplo: «Copiado. Revisa que no quede ningún nombre de tus archivos y pégalo en {report}». Acortar unexpected_error a tres frases y agregar un test que impida «/issues» en el catálogo.
- **F5-11 — Un resultado vacío se anuncia con «El documento se convirtió», y la nota de PDF escaneado no dice qué hacer**
  - *Impacto:* Con un PDF escaneado, una presentación vacía o una página web sin cuerpo, el titular del resumen y la ventana dicen que todo se convirtió. La persona le entrega a su IA un archivo vacío. La única pista es una nota secundaria con jerga («páginas sin texto: 1–3») y sin paso siguiente, cuando para las imágenes sí se aconseja pasarlas antes por un programa que reconozca el texto.
  - *Evidencia:* es.toml:220 headline.all.one = «El documento se convirtió.»; es.toml:298 pdf_pages_without_text no trae acción. B5-01, B1-03 y B3-05 lo reprodujeron de punta a punta (salida de 0 a 1 byte, EXIT=0). Yo verifiqué el catálogo; no repetí la ejecución.
  - *Recomendación:* Apoyo la regla de backend: un resultado sin texto es «falló» con su razón, como la regla del dueño para los archivos vacíos. En mi lente, el texto: «Este PDF son solo imágenes escaneadas: no tiene texto que ClearMD pueda leer. Pásalo antes por un programa que reconozca el texto (OCR).» Si en algún caso se mantiene como convertido, el titular no debe decir «se convirtió» sin más. Probar con un PDF de 1 página en blanco y con uno mixto (1 de 10 páginas con texto).
- **F5-03 — Abrir los resultados abre una ventana del explorador por cada carpeta**
  - *Impacto:* Con la opción por defecto, quien convierte archivos de varias carpetas recibe de golpe una ventana del explorador por cada una, y esas ventanas tapan ClearMD. El botón dice «Abrir Carpeta de Resultados», en singular, pero las abre todas.
  - *Evidencia:* presenter/intents/results.py:31-35 recorre result_folders y llama a open_folder sin límite (lo volví a leer en esta ronda). conversion.py:153-156 lo hace solo cuando todo salió bien (open_output_when_done=True por defecto). Captura 018/4-results-light-es.png: 4 carpetas y un único botón. No lo ejecuté en Windows.
  - *Recomendación:* Con más de una carpeta, no abrir nada automáticamente, y que el botón diga «Abrir Carpetas de Resultados (4)». Mejor: que cada ruta de «Tus archivos están en…» abra la suya. Con una sola carpeta, dejarlo como está.
- **F5-04 — El color de los estados dice cosas distintas: contadores en naranja sin problema y «Terminado con problemas» en verde en flet**
  - *Impacto:* En Resultados y Revisar, «1 Conservado» (algo que la persona eligió) y «2 Omitidos» (por ejemplo, un archivo que ya era Markdown) salen en naranja de advertencia, mientras sus filas están en tono tranquilo. Lo contrario pasa en la App Estilo Móvil: el encabezado «Terminado con problemas» sale en el verde del éxito. El color alarma cuando no hay problema y tranquiliza cuando sí lo hay.
  - *Evidencia:* presenter/screens/review.py:58: el tono por defecto de stat() es Tone.WARNING. results.py:65 y :69 usan ese valor para stat_skipped y stat_kept, aunque las filas usan INFORMING (results.py:46). flet/window/view.py:172 llama a show_header sin warning, mientras que pyside/window/view.py:174-178 pasa warning=problems. Lo verifiqué en esta ronda, a partir de F3-06. Capturas 016/4-results-light-es.png y 018/4-results-light-es.png.
  - *Recomendación:* Calcular el tono del contador con la regla de las filas: «Conservado» siempre neutro, y «Omitidos» en naranja solo si alguno pide una acción. En flet, pasar el tono de advertencia al encabezado como en Qt y ttk. Agregar una prueba de paridad en las tres ventanas con FINISHED_WITH_PROBLEMS y un lote cuyo único omitido sea un .md.
- **F5-05 — El paso 1 pide decisiones técnicas antes de que la persona vea su lista**
  - *Impacto:* En «Elige Qué Convertir», la lista deja ver unas 4 filas. El resto son decisiones que una persona no técnica no entiende la primera vez: «Resumen del Proceso: Markdown / Markdown + PDF / Solo PDF», «Imágenes» y el título incompleto «Los Resultados Van». La app funciona sin tocar nada de esto, pero lo pone en primer plano.
  - *Evidencia:* Capturas 018/1-choose-light-es.png y 016/1-choose-light-es.png. es.toml:594 output_title = «Los Resultados Van» y :606 summary_title = «Resumen del Proceso:» (lo volví a verificar). ux.md §7: la app funciona sin abrir Ajustes; las dos opciones ya existen allí. F3-02 y F3-03 llegan a lo mismo desde lo visual.
  - *Recomendación:* Esto contradice ADR-0031 y ADR-0033, que pusieron esas opciones en el paso 1. Propongo revisarlos, porque son decisiones de una sola vez en la primera pantalla de trabajo. Dejarlas en Ajustes y mostrar en el paso 1 una línea discreta («Resumen en Markdown · sin imágenes — Cambiar») o un apartado plegado «Más opciones». Si se quedan, renombrar a «Dónde Guardar los Resultados» y «Informe de lo que pasó:».
- **F5-06 — La columna «Carpeta» del paso 1 se corta por el final y todas las filas se ven iguales**
  - *Impacto:* En Windows todas las rutas empiezan igual. Al cortarse por el final, cada fila muestra el mismo comienzo y la persona no distingue de qué carpeta viene cada archivo. En Revisar, en cambio, se muestra solo el nombre de la carpeta: es incoherente.
  - *Evidencia:* Captura 018/1-choose-light-es.png: las 5 filas dicen «C:\Users\RUNNER~1\AppData\Local\Te…». presenter/screens/choose.py:56-60 devuelve str(path.parent) completo y flet/components/file_list.py:167 recorta por el final. F3-05 lo confirma.
  - *Recomendación:* Recortar por el centro o por el inicio (…\Documentos\Tesis), o usar el mismo criterio que Revisar, con la ruta completa en el detalle. Tomar las capturas de referencia con rutas largas de Windows.
- **F5-07 — Una misma idea recibe varios nombres, y quedan calcos y frases cojas**
  - *Impacto:* La persona aprende una palabra en una pantalla y encuentra otra en la siguiente: «Skipped» y «Left out:», «No Incluidos» y «omitidos», «esos archivos se omiten» que luego cuentan como «Conservado». A eso se suman calcos en pantallas que se leen con atención: «still moving», «About:» y «Los Resultados Van». Juntas, estas diferencias hacen dudar de qué pasó.
  - *Evidencia:* en.toml: gui.result.stat_skipped=«Skipped» frente a word_skipped=«Left out:»; summary.left_out frente a summary.skipped. es.toml: gui.plan.keep=«Conservarlos (esos archivos se omiten)» frente a stat_kept. Calcos: gui.progress.pages «still moving», error.timed_out.message «stopped moving, so it was stopped», gui.split.hint «About:»/«Aproximado:», error.timed_out.action «Prueba dividiéndolo con Dividir…», gui.welcome.step3 «Confirma, y ves…». Mayúscula después de los dos puntos incoherente («Con error: Este…» frente a «Omitido: ya es…»).
  - *Recomendación:* Un glosario con una palabra por idea (convertido, conservado, omitido, con error, detenido), aplicado en la ventana, el resumen y la terminal, con un test que compare contadores, filas y resumen. Corregir los calcos: «still working», «This file stopped making progress, so ClearMD stopped it», «Approximate:», «Prueba a dividirlo con «Dividir»», «3. Confirma y mira dónde quedaron tus archivos». Minúscula después de «Con error:».
- **F5-09 — La Bienvenida y el Inicio no dicen para qué sirve el resultado**
  - *Impacto:* ClearMD existe para preparar documentos para una IA, pero la Bienvenida y el Inicio no lo dicen ni explican qué es Markdown. Quien llega ve «Convertir a Markdown» sin saber si le sirve.
  - *Evidencia:* es.toml gui.welcome.intro, gui.home.subtitle y gui.home.convert_body: ninguno menciona la IA. El «para qué» está solo en gui.help.markdown, gui.help.ai y gui.result.with_ai. Capturas 018/0-welcome-light-es.png y 018/0-home-light-es.png. F4-01 lo confirma con el mismo grep.
  - *Recomendación:* Una frase en la Bienvenida («ClearMD prepara tus documentos para que una IA los lea mejor: los pasa a Markdown, un texto simple y ordenado») y en la tarjeta Convertir («Para usarlos con tu IA · PDF, Word, Excel…»). Una prueba de catálogo que exija mencionar la IA en ambos idiomas.
- **F5-10 — «Esperando tu decisión» aparece aunque no haya nada que decidir**
  - *Impacto:* En Revisar y en Convertir, la cabecera dice «Paso 3 de 4 · Esperando tu decisión» aunque no haya ninguna pregunta en pantalla. La persona busca qué tiene que decidir y no lo encuentra.
  - *Evidencia:* presenter/intents/analysis.py:110 pone siempre AppState.WAITING_DECISION después de analizar (lo volví a verificar). Captura 018/3-convert-ready-light-es.png: solo hay un botón Convertir. es.toml:341.
  - *Recomendación:* Usar «Listo para convertir» (o dividir o unir) cuando no haya resultados existentes que decidir, y reservar «Esperando tu decisión» para cuando hay una pregunta visible. Actualizar ux.md §1 si cambia la lista de estados.

</details>

## 10. Lecciones para las plantillas

Las lecciones de esta cuarta auditoría se incorporaron a
[`docs/lessons-learned.md`](../lessons-learned.md), Parte XV (en inglés, como el resto de ese archivo).
Lo que propuso la conciliadora:

- Producto: un titular de éxito exige un resultado útil. Una salida sin texto tras la limpieza es «falló» con su razón, en todas las herramientas.
- Producto: cada frase de las notas de la versión lleva una prueba con el caso más difícil posible. Para textos, eso es la entrada más corta (2 a 5 bytes, con «¿» o «¡»), no una frase.
- Producto: una garantía de salida vive en una sola puerta por la que pasa todo, con una prueba que recorre cada herramienta.
- Producto: un solo canal de reporte en el catálogo, con una prueba que prohíba otras direcciones.
- Aplicar una auditoría: los desacuerdos resueltos fuera del top 10 van a una lista de pendientes con su prueba. Si no, se pierden, como pasó con las medidas baratas del candado.
- Aplicar una auditoría: cuando el código cumple una ADR al pie de la letra y aun así falla, el arreglo empieza enmendando la ADR, no «afinando» el código.
- Aplicar una auditoría: el AC de la feature se comprueba contra cada camino que llega a él, no solo el principal (la casilla «Mantener» tras Dividir).
- Método: cinco expertos por junta dan profundidad. Los conciliadores deben conservar las citas de ADR de los auditores al reagrupar; C1 perdió dos.
- Método: la lista verificada debe caber en una lectura (unos 25 grupos). Un top que junta seis problemas debe poder aceptarse por partes.
- Método: la conciliadora de doctrina revisa las decisiones del dueño como lista de control, una por una, en el código.
