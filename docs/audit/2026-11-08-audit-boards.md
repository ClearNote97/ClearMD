# Juntas de Auditoría de ClearMD 2.8.1

> **Fecha:** 2026-11-08 · **Versión auditada:** 2.8.1 · **Para:** el dueño del producto.
> Documento en español por excepción a ADR-0011: está escrito para que el dueño decida.
> Presentación ejecutiva: <https://claude.ai/artifact/Ut6BPZxyfHWN3wAStZBQwt> (privada: solo la ve el dueño).
> Datos completos de las tres rondas: [`2026-11-08-audit-boards.json`](./2026-11-08-audit-boards.json).

## Cómo leer este documento

- **Si tienes 5 minutos:** lee el resumen ejecutivo (sección 1) y las diez mejoras recomendadas (sección 4).
- **Para decidir:** las secciones 5 (lo que no conviene hacer) y 6 (desacuerdos abiertos).
- **Para el detalle:** la sección 8 trae cada hallazgo verificado: qué siente la persona, qué se recomienda y
  qué comprobó la junta conciliadora. La sección 9 trae el informe de cada auditor.
- Las referencias técnicas (archivo:línea) quedan para quien implemente; no hace falta entenderlas para decidir.

## 1. Resumen ejecutivo

**Veredicto de la junta conciliadora: 6,5 de 10.** ClearMD es un producto serio y bien protegido cuando todo sale
bien:

- nunca deja un archivo escrito a medias;
- un documento dañado o enorme no tumba la ventana;
- las tres ventanas obedecen las mismas reglas;
- cada error dice qué pasó y qué hacer, en los dos idiomas.

**El problema de fondo es la confianza en los casos límite.** Hay situaciones en que la app dice que todo salió
bien cuando no fue así, y otras en que avisa de un problema que no existe. Justo ahí, una persona no técnica no
tiene cómo comprobarlo:

- **Dice "bien" cuando algo salió mal.** Volver a dividir puede borrar la división anterior. Dos uniones hechas
  en el mismo minuto se pisan. Al dividir o unir, las imágenes quedan rotas. Un CSV de Excel en español sale en
  una sola columna. Un archivo elegido dos veces se procesa dos veces.
- **Avisa cuando todo salió bien.** Casi todo PDF sale marcado con ⚠️ por una limpieza que en realidad es buena
  noticia. Lo que la persona decidió conservar aparece como "necesita tu atención". Una unión fallida pregunta
  "¿el disco está lleno?" sin motivo.
- **No acompaña cuando hay dudas.** La Ayuda describe un recorrido que ya no existe y no menciona Dividir ni Unir.
  En Revisar, el motivo de un archivo omitido sale cortado justo en la parte de "qué hacer". La pantalla de
  Resultados no escribe dónde quedaron los archivos.

**La buena noticia:** de las 10 mejoras recomendadas, 6 son de esfuerzo pequeño y ninguna exige rediseñar la app.
El presentador compartido hace que casi todos los arreglos se escriban una sola vez para las tres ventanas.

**De los 38 hallazgos que revisó la conciliadora:**

- 29 quedaron confirmados.
- 9 son parcialmente ciertos.
- Ninguno es falso.

La conciliadora corrigió dos afirmaciones exageradas y encontró dos huecos que las juntas dejaron caer:

- la ventana abre en inglés aunque la persona instaló en español;
- los `.doc`, `.xls` y `.ppt` antiguos se rechazan sin decir cómo seguir.

### Lo que tienes que decidir

1. **Si te acoges a las 10 mejoras** (sección 4). Recomendación: sí, en tres entregas:
   - 2.9 con 1–3: no perder ni falsear el trabajo;
   - 2.10 con 4–7: señales honestas, Ayuda y pantallas;
   - 2.11 con 8–10: mensajes, primera experiencia y estimaciones.
2. **Qué hacer con los desacuerdos abiertos** (sección 6): ¿tres ventanas o una principal?, ¿fusionar Revisar con
   Convertir?, ¿qué hacer cuando un archivo agota los 10 minutos? Ninguno es urgente para el usuario.
3. **Si confirmas la lista de lo que no conviene hacer** (sección 5). Por ejemplo, no renombrar las carpetas de
   resultados sin un plan de migración.

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
   contenedor de desarrollo. Resultado: 76 hallazgos.
2. **Debate.** Cada auditor leyó los ocho informes, de las dos juntas, y apoyó, cuestionó, matizó o amplió los
   hallazgos de los demás. Fueron 127 intervenciones. Después corrigió su propio
   informe: 78 hallazgos tras el debate.
3. **Conciliación.** La junta conciliadora volvió al código y a las capturas, unió los duplicados y quedó con
   **38 hallazgos verificados**.

Una corrida anterior se interrumpió por un corte de red. Sus tres informes terminados se conservaron **solo como
referencia** para la conciliadora; no cuentan como hallazgos.

**Notas por lente (de 0 a 10, tras el debate):**

| Lente | Nota | Hallazgos | Intervenciones en el debate |
| --- | --- | --- | --- |
| Backend · Lógica | 6,5 | 11 | 12 |
| Backend · Eficiencia | 6,5 | 8 | 12 |
| Backend · Experiencia de lo que entrega | 6,5 | 10 | 15 |
| Backend · Claridad es cariño | 6,5 | 10 | 19 |
| Frontend · Lógica | 7 | 10 | 14 |
| Frontend · Eficiencia | 6 | 9 | 14 |
| Frontend · Estilo visual UI/UX | 7 | 10 | 16 |
| Frontend · Claridad es cariño | 6,5 | 10 | 25 |

## 3. Lo que hay que proteger

Las fortalezas que ninguna mejora debe romper:

- Escrituras atómicas (temporal + os.replace) y «Conservar» por defecto en Convertir: ningún corte deja un .md a medias y nada se pisa sin preguntar.
- Proceso trabajador aislado con límites de tiempo, memoria y arranque: un archivo malicioso o gigante nunca tumba la ventana, y cancelar es inmediato.
- Un único presentador para las tres ventanas: las mismas reglas de cancelar, cerrar, «¿Qué Sigue?» y la protección contra el doble clic en todas.
- Un catálogo bilingüe con mensaje y acción por cada error, valores medidos frente a límites, y una prueba de claves y marcadores iguales en los dos idiomas.
- El orden del resumen: titular humano, dónde están los archivos, qué revisar y el detalle técnico plegado. Lo conservado ya va aparte en el resumen escrito.
- Honestidad con lo que no se pudo leer: páginas escaneadas con su rango exacto, y la división por palabras se niega a producir una parte silenciosa con un PDF escaneado.
- La línea de detalle bajo la lista de Resultados: es el patrón que hay que llevar a Revisar.
- La identidad visual centralizada en design/ (rejilla de 8 px, botones de 44 px, texto de al menos 14 px) y los colores base con contraste AA holgado.
- La promesa de privacidad «100 % local», idéntica en la app, el README y SECURITY.
- La cultura de medir: los ADR con mediciones y el control en CI del peso del ejecutable y de las librerías prohibidas.
- Dividir un Excel conserva formatos y gráficos.

## 4. Las diez mejoras recomendadas

Ordenadas por valor para el cliente final frente al esfuerzo. Marca tu decisión en la última columna.

| # | Mejora | Por qué le importa a la persona | Esfuerzo | ¿Me acojo? |
| --- | --- | --- | --- | --- |
| 1 | **Nunca perder ni pisar trabajo anterior: escribir las partes en un temporal y sufijo (2) en las uniones** | Hoy la persona puede perder una división completa o una unión sin ningún aviso, y el resumen le dice que todo salió bien. Es la falla más grave contra la confianza. | medio | ☐ Sí ☐ No |
| 2 | **Que Unir siempre deje resumen y motivo, y que exija dos documentos desde el paso 1** | Elimina el «¿el disco está lleno?» falso que puede llevar a alguien a borrar archivos, y avisa a tiempo y no al final. | pequeño | ☐ Sí ☐ No |
| 3 | **Cerrar los defectos de contenido silencioso: carpeta más archivo duplicados, CSV con punto y coma, imágenes rotas al dividir o unir** | Son resultados equivocados marcados como correctos que la persona entrega a una IA sin poder notarlo. | medio | ☐ Sí ☐ No |
| 4 | **Una señal honesta: notas informativas sin ⚠️ y lo conservado fuera de «atención», con su carpeta abrible** | Si casi todo sale con ⚠️, la persona deja de creer en los avisos y no ve los reales (páginas escaneadas, errores). | medio | ☐ Sí ☐ No |
| 5 | **Reescribir la Ayuda por herramienta y explicar en una frase qué es Markdown** | La Ayuda es el recurso de quien está perdido, y hoy le indica botones que no existen y no menciona Dividir ni Unir. | pequeño | ☐ Sí ☐ No |
| 6 | **Ver el motivo completo en Revisar y la ruta exacta en Resultados** | La promesa del producto es decir qué pasó y qué hacer. Hoy se corta justo la acción, y la pregunta «¿dónde están mis archivos?» no tiene respuesta escrita. | pequeño | ☐ Sí ☐ No |
| 7 | **Arreglar la lista de la ventana clásica: barra de desplazamiento visible e imágenes en caché** | Es la ventana que se instala por defecto: esconde archivos sin avisar y se congela con carpetas grandes. | pequeño | ☐ Sí ☐ No |
| 8 | **Mensajes de error que no engañan ni usan jerga: separar ventana y terminal, Office cifrado, archivo vacío, error inesperado sin nombres técnicos** | Un consejo equivocado es peor que uno vago, porque la persona lo sigue al pie de la letra. | medio | ☐ Sí ☐ No |
| 9 | **Una primera experiencia amable: instalador liviano, app en el idioma del instalador y accesos directos sin nombres técnicos** | La descarga de 176 MB, la app en inglés y los nombres «flet» y «Qt» son lo primero que vive la persona, antes de convertir nada. | pequeño | ☐ Sí ☐ No |
| 10 | **Estimaciones creíbles y control de memoria también al dividir Excel** | Evita avisos que asustan sin motivo y esperas de minutos anunciadas como segundos. | medio | ☐ Sí ☐ No |

Los códigos de cada mejora (por ejemplo, B1-01) llevan a los hallazgos de la sección 8:

- **1.** B1-01, B1-02, B3-08
- **2.** B4-01, F4-11, F1-02, B1-07
- **3.** B1-11, F1-01, B1-03, B1-12, B3-01
- **4.** B3-02, F1-03, F4-06, F3-03, B4-10
- **5.** F4-02, B4-03, F3-06, F1-04, F4-01
- **6.** F3-01, F4-04, F3-09, F3-11, F4-03
- **7.** F2-01, F3-02, F2-07
- **8.** B1-07, B4-02, F4-05, F1-07, F4-07, B4-05, B4-06, C-2
- **9.** F2-03, B2-07, C-1, B4-09
- **10.** B2-01, B2-02, B1-08, B2-04

## 5. Lo que no conviene hacer

Propuestas que surgieron en las juntas y que, según la conciliadora, **añadirían complejidad o romperían algo**:

- No retirar ni congelar ventanas como parte de estas correcciones: el presentador compartido ya hace que casi todos los arreglos se escriban una sola vez. Es una decisión de producto aparte.
- No renombrar ni traducir OutputMD, OutputSep, OutputUnif ni Resumen_ClearMD sin un ADR y una migración probada: rompe --changed, «Reemplazar» y los resultados existentes.
- No cortar el Excel manipulando su ZIP sin fixtures de gráficos, nombres definidos y fórmulas entre hojas: hoy se conservan y eso es una fortaleza.
- No entregar un resultado parcial al llegar al límite de tiempo como si fuera el normal: la persona lo subiría incompleto a una IA.
- No añadir los alias `clearmd split` y `clearmd merge`: basta con corregir el roadmap.
- No pedirle a la persona que elija el nombre del archivo unido: el nombre automático, con un sufijo, resuelve lo mismo sin otro paso.
- No añadir un «deshacer» general ni guardar lo soltado durante el trabajo: un aviso de una línea basta.
- No reabrir el Title Case en cada hallazgo: es doctrina del dueño; solo aplicarla de forma uniforme.
- No implementar la detección del idioma del sistema en contra de ADR-0017: usar el idioma que ya eligió el instalador.
- No fusionar Revisar y Convertir antes de probar a llenar el paso 3 con información útil.
- No subir severidades solo porque varios auditores repiten lo mismo: la coincidencia confirma el hecho, no su gravedad.

## 6. Desacuerdos que quedan abiertos

- Title Case en español: F4-09 sigue proponiendo la regla de la RAE. F3, B3, B4 y F1 la tratan como doctrina del dueño. Resolución: es decisión del dueño, y la auditoría solo pide aplicarla de forma uniforme con un linter.
- Corte de Excel: B2 propone manipular el ZIP y B1 advierte del riesgo para gráficos y fórmulas. Resolución: cargar una sola vez primero; el ZIP solo con fixtures exigentes.
- Resultado parcial al llegar al límite de tiempo: B2 y B3 lo quieren, y B1 teme que se suba a una IA sin leer la nota. Sigue abierto. Recomiendo solo el progreso por página por ahora.
- Tres ventanas: F2 propone elegir una principal y congelar las otras. Los demás piden primero renombrar los accesos directos. Sigue abierto como decisión de producto, sin urgencia para el usuario.
- Fusionar Revisar y Convertir (F3-10 ideal, F4-08 vía ADR) frente a llenar el paso 3 (F3, F4, B4). Resolución: llenar primero y decidir la fusión después.
- Renombrar o traducir OutputMD, OutputSep y OutputUnif: F4 lo quiere, y B3, B4 y F3 advierten que rompe --changed y los resultados existentes. Resolución: ruta visible ya; el renombre, solo con ADR y migración.
- Idioma del sistema: B4-07 y B3 piden respetarlo, y ADR-0017 lo rechaza a propósito. Ninguna mesa lo notó. Mi propuesta C-1 lo evita usando el idioma del instalador.
- Trabajador persistente durante la sesión (B2-05) frente a arrancarlo en segundo plano solo durante Revisar: diferencia de complejidad no resuelta por las mesas.

## 7. Cómo trabajaron las juntas

La conciliadora también auditó a las juntas y a su debate:

### Backend board (B1 Lógica, B2 Eficiencia, B3 Experiencia de lo que entrega, B4 Claridad es cariño) — rigor 8,5/10

- **Lo que hizo bien:** Reprodujo casi todo con comandos reales: dos uniones seguidas, nueva división con un obstáculo, Unir con un PDF dañado y `find` de la carpeta inexistente, cProfile del lector PDF, mediciones de memoria del corte de Excel. Además citó líneas exactas que pude confirmar: splitting.py:120/144 llaman a remove_earlier_parts antes de escribir, naming.py:9 tiene precisión de minutos, merging.py:131-138 solo llama a prepare_root en la rama else, planning.py:78 deduplica con dict.fromkeys, markitdown_adapter.py:91 usa CsvConverter y content.py:76 manda a atención cualquier nota. En el debate encontró la clase de problema y no solo el caso: una operación sin modelo de coste propio, un código de error con un solo significado y, en general, no destruir trabajo anterior sin tener el reemplazo.
- **Lo que no vio:** No vio que la app abre en inglés para el público hispano (ADR-0017), y B4-07 llega a recomendar «respetar el idioma del sistema» sin advertir que eso contradice un ADR vigente que acepta esa brecha a propósito, incluida la de argparse. Tampoco vio que los .doc, .xls y .ppt antiguos se rechazan con un genérico «formato no soportado» (la primera ronda sí lo tenía). En B1-07(a) no notó que xlsx.py:28 ya reconoce la firma OLE: el fallo es solo de .docx y .pptx. En B1-07(d), el texto de write_failed (es.toml:29) no habla solo de disco lleno. Dice «espacio libre, nombres largos u otra carpeta»; lo que le falta es «ciérralo en el otro programa».
- **Donde se excedió:** Cortar el Excel manipulando su ZIP (B2-01): el propio B1 mostró que pone en riesgo gráficos y nombres definidos. Entregar resultados parciales al llegar al límite de tiempo como si fueran un resultado normal (B2-04). Repartir un PDF entre dos núcleos (B2-03). Alias de subcomandos `clearmd split/merge` (B3-07). Un historial de «pendientes de antes» en el resumen (B3-06). Mantener un trabajador vivo durante toda la sesión es razonable, pero añade estado en tres ventanas: arrancarlo en segundo plano, en paralelo con Revisar, da casi todo el beneficio.

### Frontend board (F1 Lógica, F2 Eficiencia, F3 Estilo visual, F4 Claridad es cariño) — rigor 8/10

- **Lo que hizo bien:** Usó el presentador real sin ventana para reproducir casos límite: la carpeta más un archivo suyo y la segunda ejecución con Conservar. Midió las listas con Xvfb en ttk, flet y Qt y anclaba cada hallazgo visual a capturas concretas, que confirmé (018/4: lo conservado bajo «Lo que Necesita Tu Atención», el fallo en el mismo naranja que lo omitido, «Quítale la contr…» cortado; 007/2: cuatro filas sin barra de desplazamiento). Hizo autocorrecciones honestas: F2 reconoció que marks.icon sí tenía caché y que el trabajador no persiste entre lotes, y F3 retiró la objeción al Title Case por ser doctrina del dueño.
- **Lo que no vio:** F1-03 y F4-06 afirman que lo conservado deja el lote «Terminado con problemas», y eso es falso: el estado solo mira FAILED, STOPPED y los resúmenes no escritos (conversion.py:130-139). El error se propagó por el debate sin que nadie lo comprobara. B4-09 y F2-06 exageran la jerga del instalador: los tipos ya dicen «Solo la app clásica (recomendada: la más liviana)». Tampoco vio el arranque en inglés de la ventana para quien instaló en español, que es la primera pantalla real de la persona.
- **Donde se excedió:** Retirar ventanas (F2-06, esfuerzo grande, con beneficio para la persona que solo es indirecto). Renombrar o traducir OutputMD, OutputSep y OutputUnif (F4-03), que rompe --changed y los resultados existentes. Fusionar Revisar y Convertir (F3-10, F4-08) antes de probar a llenar el paso 3. Desplegar en Unir los archivos de una carpeta como entradas propias (F1-10). Guardar lo soltado durante el trabajo para la siguiente tanda (F1-09). Volver a proponer la mayúscula de la RAE (F4-09) en contra de una doctrina ya registrada.

### Debate (ronda 2, las dos mesas) — rigor 7,5/10

- **Lo que hizo bien:** Fusionó bien los duplicados entre mesas (Ayuda, mensajes de terminal en la ventana, error inesperado, instalador) y llevó varios hallazgos a su raíz común. También produjo matices útiles: preferir reescribir enlaces a copiar imágenes, cargar el libro de Excel una sola vez antes de manipular el ZIP, que una ruta visible no espere al renombre de carpetas y que renombrar los accesos directos no dependa de retirar ventanas.
- **Lo que no vio:** Amplificó por eco: «cuatro auditores lo encontraron» se usó para subir severidades sin volver a comprobar, y así se propagó la afirmación falsa de «Terminado con problemas». Nadie consultó los ADR antes de recomendar algo que los contradice (ADR-0017). Además, la ronda 2 dejó caer hallazgos reales de la primera ronda (formatos Office antiguos, idioma de arranque, foco de teclado en los mosaicos de flet).
- **Donde se excedió:** Algunos auditores sumaron hallazgos de otros a su propia lista (B1-11 y B1-12, F2-09, F3-11) y con eso inflaron el número de hallazgos «altos» sin aportar evidencia nueva.

## 8. Hallazgos verificados

Son 38 hallazgos, ordenados por gravedad. **Veredicto:** ✅ confirmada · ◐ parcialmente cierta · ✖ refutada.

| Gravedad | Valor para el usuario | Esfuerzo | Veredicto | Hallazgo |
| --- | --- | --- | --- | --- |
| 🔴 Alta | alto | medio | ✅ Confirmada | [1. Volver a dividir borra las partes anteriores antes de tener las nuevas](#h1) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [2. Dos uniones en el mismo minuto se pisan, y el archivo unido no muestra dónde empieza cada documento](#h2) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [3. Una carpeta más un archivo de esa carpeta se procesan dos veces](#h3) |
| 🔴 Alta | alto | medio | ✅ Confirmada | [4. Dividir o unir un Markdown con imágenes deja todos los enlaces rotos y el resumen da ✅](#h4) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [5. Un CSV separado por punto y coma (el de Excel en español) sale como una sola columna](#h5) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [6. Unir con un documento dañado (o con menos de dos útiles) termina sin resumen, sin motivo y con «¿el disco está lleno?»](#h6) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [7. Casi todo PDF sale con «⚠️ necesita tu atención» por una limpieza que es buena noticia](#h7) |
| 🔴 Alta | alto | medio | ◐ Parcial | [8. Al repetir una tanda, lo conservado se cuenta como problema, «Abrir carpeta» se apaga y el paso 3 anuncia trabajo que no hará](#h8) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [9. La Ayuda describe un recorrido que ya no existe y no menciona Dividir ni Unir](#h9) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [10. En Revisar, el motivo y la acción de cada archivo omitido salen cortados y no se pueden leer completos](#h10) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [11. Resultados no muestra como texto dónde quedaron los archivos](#h11) |
| 🔴 Alta | alto | pequeño | ✅ Confirmada | [12. La lista de la ventana clásica (la que se instala por defecto) esconde filas sin barra de desplazamiento y se congela con listas grandes](#h12) |
| 🟠 Media | alto | medio | ◐ Parcial | [13. Diagnósticos de error que no corresponden al caso real](#h13) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [14. El error inesperado muestra el nombre técnico de la excepción, borra la vista de lo hecho y «repórtalo» no dice dónde](#h14) |
| 🟠 Media | medio | medio | ✅ Confirmada | [15. Opciones de terminal y jerga en la ventana, nombres de botones en la terminal](#h15) |
| 🟠 Media | alto | pequeño | ✅ Confirmada | [16. Nunca se explica qué es Markdown ni para qué sirve](#h16) |
| 🟠 Media | medio | medio | ✅ Confirmada | [17. Dividir un Excel es mucho más lento que convertirlo y se salta el control de memoria](#h17) |
| 🟠 Media | medio | medio | ◐ Parcial | [18. Las estimaciones de tiempo y memoria se calculan por megabytes, y Unir en PDF usa la estimación de convertir](#h18) |
| 🟠 Media | medio | medio | ✅ Confirmada | [19. Sin progreso dentro de un archivo largo, y al llegar a 10 minutos se pierde todo](#h19) |
| 🟠 Media | medio | medio | ✅ Confirmada | [20. Cada lote vuelve a arrancar el trabajador, y la ventana carga librerías que no usa](#h20) |
| 🟠 Media | alto | pequeño | ✅ Confirmada | [21. El instalador pesa unos 176 MB para instalar por defecto unos 37 MB](#h21) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [22. Colores derivados por debajo de 4,5:1, aunque el ADR-0027 asegura que todo cumple AA](#h22) |
| 🟠 Media | medio | medio | ✅ Confirmada | [23. Ajustes no cabe en un portátil en Qt y no indica en flet que hay más opciones abajo](#h23) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [24. El atajo «Dividir los PDF grandes» cambia sin avisar las preferencias guardadas de Dividir](#h24) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [25. Al unir una carpeta, el orden es 1, 10, 11, 2 y no se puede corregir](#h25) |
| 🟠 Media | medio | pequeño | ◐ Parcial | [26. El resumen se reemplaza en cada acción y puede borrar el PDF del resumen que la persona pidió](#h26) |
| 🟠 Media | medio | medio | ◐ Parcial | [27. En las tablas de PDF sin líneas, cada celda larga se parte en muchas filas](#h27) |
| 🟠 Media | medio | pequeño | ✅ Confirmada | [28. El README muestra un ClearMD más viejo y no menciona clearmd-cli](#h28) |
| 🟠 Media | alto | pequeño | ✅ Confirmada | [29. La ventana abre en inglés aunque la persona instaló ClearMD en español](#h29) |
| 🟠 Media | alto | pequeño | ✅ Confirmada | [30. Los Word, Excel y PowerPoint antiguos (.doc, .xls, .ppt) se rechazan con un genérico «formato no soportado»](#h30) |
| ⚪ Baja | medio | pequeño | ✅ Confirmada | [31. Textos que describen el producto de antes y errores visibles de concordancia](#h31) |
| ⚪ Baja | medio | pequeño | ◐ Parcial | [32. El instalador y los accesos directos muestran nombres de tecnología](#h32) |
| ⚪ Baja | medio | pequeño | ✅ Confirmada | [33. El paso 3 está casi vacío y la bienvenida promete «tres pasos» cuando hay cuatro](#h33) |
| ⚪ Baja | medio | pequeño | ✅ Confirmada | [34. Editar la lista o cambiar de herramienta borra los resultados de la pantalla sin aviso](#h34) |
| ⚪ Baja | medio | pequeño | ✅ Confirmada | [35. Dividir un documento que ya cabe anuncia «se dividió» y entrega una «parte 1 de 1»](#h35) |
| ⚪ Baja | bajo | medio | ◐ Parcial | [36. Detalles de fidelidad y estabilidad: codificación de las partes, renombre ante un choque de nombres, cambios de opciones ignorados](#h36) |
| ⚪ Baja | bajo | pequeño | ◐ Parcial | [37. La CLI mezcla idiomas y el roadmap promete subcomandos que no existen](#h37) |
| ⚪ Baja | bajo | medio | ◐ Parcial | [38. Mejoras de rendimiento, métricas y pulido de menor prioridad](#h38) |

<a id="h1"></a>

### 8.1 Volver a dividir borra las partes anteriores antes de tener las nuevas

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B1-01*

- **Lo que siente la persona:** Pidió dividir de nuevo, algo falló o canceló, y su división anterior desapareció. Le queda una carpeta incompleta que puede subir a una IA sin saberlo.
- **Recomendación:** Escribir las partes nuevas con nombres temporales dentro de OutputSep, moverlas solo cuando estén todas y, entonces, borrar las anteriores. Si falla, borrar lo nuevo. Agregar una prueba de regresión con cancelación a mitad.
- **Comprobación de la conciliadora:** splitting.py:120 (_pdf) y :144 (_markdown) llaman a remove_earlier_parts() antes del bucle de escritura. Lo confirmé en el código.

<a id="h2"></a>

### 8.2 Dos uniones en el mismo minuto se pisan, y el archivo unido no muestra dónde empieza cada documento

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B1-02, B3-08*

- **Lo que siente la persona:** Su primera unión desaparece sin aviso y el resumen dice «2 unidos» las dos veces. Dentro del archivo unido no ve dónde termina un documento y empieza el siguiente.
- **Recomendación:** Sufijo (2), (3) si el nombre existe, como en Convertir. Un separador visible y discreto por documento («Documento 2 de 3: nombre») que conserve el comentario para las máquinas. El nombre basado en el primer documento es opcional y no debe preguntarse a la persona.
- **Comprobación de la conciliadora:** naming.py:9 STAMP='%Y-%m-%d %H-%M'; merging.py:39 fuerza exists=False sobre un destino que solo depende de esa marca de minuto.

<a id="h3"></a>

### 8.3 Una carpeta más un archivo de esa carpeta se procesan dos veces

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B1-11, F1-01*

- **Lo que siente la persona:** Recibe dos copias del mismo documento en dos ClearMD_Output distintos. En Unir, el documento sale repetido dentro de lo que entrega a la IA.
- **Recomendación:** Deduplicar en el backend (planning), por archivo real resuelto y después del escaneo, para que también quede cubierta la CLI. Conservar la primera aparición y avisarlo en una línea en Revisar.
- **Comprobación de la conciliadora:** planning.py:78 solo hace dict.fromkeys(inputs) antes de scan(). F1 lo reprodujo con el presentador real.

<a id="h4"></a>

### 8.4 Dividir o unir un Markdown con imágenes deja todos los enlaces rotos y el resumen da ✅

*🔴 Alta · valor alto · esfuerzo medio · ✅ Confirmada · B1-12, B3-01*

- **Lo que siente la persona:** El flujo que el producto promueve (convertir con imágenes y después dividir o unir) entrega documentos sin ninguna imagen visible, y nada se lo advierte.
- **Recomendación:** Reescribir los enlaces relativos para que apunten bien desde la nueva carpeta. Si alguno no se resuelve, emitir una nota de atención. Agregar una prueba de aceptación: todo enlace local del resultado lleva a un archivo que existe.
- **Comprobación de la conciliadora:** Ni splitting.py ni merging.py tienen un paso que reescriba enlaces o copie recursos. No repetí la reproducción de B3, pero el código es coherente con ella.

<a id="h5"></a>

### 8.5 Un CSV separado por punto y coma (el de Excel en español) sale como una sola columna

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B1-03*

- **Lo que siente la persona:** Recibe una tabla inútil, «nombre;ciudad» en una sola celda, marcada como «convertido» y sin ningún aviso.
- **Recomendación:** Detectar el separador con csv.Sniffer sobre una muestra, o usar un conversor propio como el de XLSX. Agregar fixtures con ';', BOM y cp1252. Como red de seguridad, si sale una tabla de una sola columna con ';' dentro de las celdas, emitir una nota de atención.
- **Comprobación de la conciliadora:** markitdown_adapter.py:91 usa CsvConverter() de markitdown, y no hay ninguna detección de separador en el backend.

<a id="h6"></a>

### 8.6 Unir con un documento dañado (o con menos de dos útiles) termina sin resumen, sin motivo y con «¿el disco está lleno?»

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B4-01, F4-11, F1-02, B1-07(e)*

- **Lo que siente la persona:** Cree que su disco está lleno, puede ponerse a borrar archivos y no sabe por qué el documento sano aparece «con error».
- **Recomendación:** Crear la carpeta de resultados antes de escribir el resumen en todas las ramas. Mostrar nothing_to_merge en cada documento. Reescribir summary_not_written y gui.result.no_summary para que no adivinen la causa. En el paso 1 de Unir, desactivar «Siguiente» con menos de dos archivos y explicar por qué.
- **Comprobación de la conciliadora:** merging.py:131-138: prepare_root solo en la rama else. es.toml:143 «(¿el disco está lleno?)» y :359 «Comprueba que el disco tiene espacio». Lo confirmé.

<a id="h7"></a>

### 8.7 Casi todo PDF sale con «⚠️ necesita tu atención» por una limpieza que es buena noticia

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · B3-02, F4-06 (parte notas), F3-03 (parte tono)*

- **Lo que siente la persona:** Aprende que las advertencias no significan nada y después pasa por alto las reales (páginas escaneadas, texto ilegible).
- **Recomendación:** Dar a cada tipo de nota un nivel (información o atención). Las informativas van en un apartado tranquilo, «Lo que ClearMD limpió», sin ⚠️ y fuera del conteo de atención, tanto en el resumen como en la ventana.
- **Comprobación de la conciliadora:** content.py:76 manda a atención todo convertido con notas, sin distinguir el tipo. NoteKind (notes.py:14) no tiene nivel. pdf/__init__.py:65 emite PDF_RUNNING_REMOVED.

<a id="h8"></a>

### 8.8 Al repetir una tanda, lo conservado se cuenta como problema, «Abrir carpeta» se apaga y el paso 3 anuncia trabajo que no hará

*🔴 Alta · valor alto · esfuerzo medio · ◐ Parcial · F1-03, F4-06, F3-03 (parte conservados), B4-10 (parte conservados), F1-08, F3-10 (parte cifra)*

- **Lo que siente la persona:** Hizo lo correcto (Conservar) y la ventana le muestra sus archivos como «Omitidos» bajo «Lo que Necesita Tu Atención», y además no le deja abrir la carpeta.
- **Recomendación:** Una categoría propia, «Conservados», fuera de la sección de atención. result_folders debe incluir las carpetas de lo conservado. La cifra de «Listo para convertir» se calcula con la decisión ya tomada y la recuerda («2 ya existen: se conservan» o «se reemplazarán»).
- **Comprobación de la conciliadora:** Confirmado: results.py:26-27 pone KEPT como fila, :45 y :53 lo suman a omitidos, :63-72 result_folders solo cuenta CONVERTED, y secondary.py:41 usa plan.stats[0]. La captura 018/4 lo muestra. REFUTADO el «Terminado con problemas»: conversion.py:130-139 solo marca problemas con FAILED, STOPPED o resúmenes no escritos.

<a id="h9"></a>

### 8.9 La Ayuda describe un recorrido que ya no existe y no menciona Dividir ni Unir

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · F4-02, B4-03, F3-06, F1-04*

- **Lo que siente la persona:** Quien abre la Ayuda porque está perdido busca un botón «Confirmar» que no existe y no encuentra cómo dividir o unir.
- **Recomendación:** Reescribir la Ayuda según la herramienta activa: qué recibe, los botones reales y dónde quedan los resultados. Elegir la variante con o sin arrastrar según la capacidad real de la ventana. Agregar pruebas: cada botón citado existe y cada herramienta del Inicio aparece en la Ayuda.
- **Comprobación de la conciliadora:** es.toml:422-423 «Pulsa Convertir… Confirma». No hay claves "gui.help.*" en [tool.split] ni en [tool.merge]. La severidad es correcta, pero el «cuatro auditores» no le añade gravedad: es el mismo hecho.

<a id="h10"></a>

### 8.10 En Revisar, el motivo y la acción de cada archivo omitido salen cortados y no se pueden leer completos

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · F3-01, F4-04, F3-09*

- **Lo que siente la persona:** Lee «archivo ZIP. Descomprímelo y co…» justo antes de confirmar. En la ventana clásica no tiene ninguna forma de ver el resto.
- **Recomendación:** Llevar a Revisar la línea de detalle que ya existe en Resultados, con la primera fila con problema seleccionada por defecto. En la columna Carpeta, mostrar solo la última carpeta. Ampliar ux.md: el texto truncado sin otra forma de leerlo cuenta como «solo por hover».
- **Comprobación de la conciliadora:** La captura 007/2 corta sin «…», y 018/4 muestra «Quítale la contr…». ux.md:53 prohíbe la información solo por hover.

<a id="h11"></a>

### 8.11 Resultados no muestra como texto dónde quedaron los archivos

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · F3-11, F4-03*

- **Lo que siente la persona:** «¿Dónde están mis archivos?» no tiene respuesta visible, y menos aún cuando el botón está apagado.
- **Recomendación:** Mostrar siempre una línea seleccionable con la ruta exacta, incluida la subcarpeta OutputMD, OutputSep u OutputUnif. Igualar all_good de Convertir con el de Dividir y Unir. Renombrar las carpetas va aparte, con ADR y migración, y no es urgente.
- **Comprobación de la conciliadora:** results.py:43-60 no produce ninguna línea con la ruta. es.toml:367 no nombra OutputMD, mientras que :588 y :631 sí nombran OutputSep y OutputUnif.

<a id="h12"></a>

### 8.12 La lista de la ventana clásica (la que se instala por defecto) esconde filas sin barra de desplazamiento y se congela con listas grandes

*🔴 Alta · valor alto · esfuerzo pequeño · ✅ Confirmada · F2-01, F3-02, F2-07*

- **Lo que siente la persona:** Cree que solo se procesarán los cuatro archivos que ve. Con una carpeta grande, la ventana se congela varios segundos y parece colgada.
- **Recomendación:** Empaquetar la barra primero, con side='right'. Guardar en caché las casillas y los números por estado y paleta, y actualizar solo las filas que cambian. Agregar pruebas: barra visible con 9 filas a 800×624, y 1.000 filas en menos de 300 ms.
- **Comprobación de la conciliadora:** ttk/components/file_list.py:58-64: Treeview con #0 fijo de 300 px y stretch=False, empaquetado antes que la Scrollbar. La captura 007/2 muestra 4 filas sin barra (hay al menos 6 entradas). No repetí la medición de F2.

<a id="h13"></a>

### 8.13 Diagnósticos de error que no corresponden al caso real

*🟠 Media · valor alto · esfuerzo medio · ◐ Parcial · B1-07 (a-d)*

- **Lo que siente la persona:** Sigue el consejo al pie de la letra y no le sirve: un Word con contraseña sale como «dañado», un .txt vacío como «PDF escaneado» y una unión cancelada como «fallida».
- **Recomendación:** (a) Reconocer la firma OLE también en .docx y .pptx como «protegido con contraseña». (b) Crear un código propio de «archivo vacío». (c) Que una unión cancelada salga como cancelada. (d) Separar PermissionError con «ciérralo en el programa que lo tenga abierto».
- **Comprobación de la conciliadora:** (a) es parcial: xlsx.py:28 ya detecta OLE, y solo fallan .docx y .pptx. (b) Confirmado: es.toml:43-45 habla de PDF escaneado. (c) Confirmado: merging.py:132. (d) Es parcial: write_failed (es.toml:29) ya menciona espacio, nombres largos y otra carpeta, pero no un archivo abierto en otro programa.

<a id="h14"></a>

### 8.14 El error inesperado muestra el nombre técnico de la excepción, borra la vista de lo hecho y «repórtalo» no dice dónde

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B4-02, F4-05, F1-07*

- **Lo que siente la persona:** Lee «KeyError: …», le piden reportar sin decirle dónde y no ve qué alcanzó a convertirse.
- **Recomendación:** Mostrar solo el mensaje tranquilizador. Poner el detalle técnico detrás de «Copiar detalles» con el enlace exacto de issues. Rotular el detalle técnico como «Para quien te dé soporte». Si es posible, llevar a Resultados con lo que ya se escribió.
- **Comprobación de la conciliadora:** reset.py:24-29 arma detail con type(error).__name__ y pone plan y report en None. es.toml:441 y :144.

<a id="h15"></a>

### 8.15 Opciones de terminal y jerga en la ventana, nombres de botones en la terminal

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · F4-07, B4-05, B4-06, B3-05*

- **Lo que siente la persona:** Lee «Conviértelo con --html full…», «(CLI: --overwrite)» o «posible bomba ZIP»: instrucciones que no puede seguir y palabras que asustan.
- **Recomendación:** Separar las acciones por canal (gui y cli), reescribir la jerga en lenguaje común, tipar los conteos para que no salgan como «`2`» y agregar una prueba que prohíba «--» y nombres de librerías en los textos que llegan a la ventana.
- **Comprobación de la conciliadora:** es.toml:86 «(CLI: --overwrite)», :90 «--html full … markitdown», :60 «posible bomba ZIP», :53 «enlace simbólico».

<a id="h16"></a>

### 8.16 Nunca se explica qué es Markdown ni para qué sirve

*🟠 Media · valor alto · esfuerzo pequeño · ✅ Confirmada · F4-01*

- **Lo que siente la persona:** No sabe qué va a recibir, con qué programa abrirlo ni por qué le sirve para una IA.
- **Recomendación:** Una frase fija en el Inicio y una sección corta en la Ayuda («texto simple, ordenado, que las IA leen mejor; se abre con el Bloc de notas»).
- **Comprobación de la conciliadora:** [gui.help] (es.toml:419-432) no define Markdown ni menciona la IA.

<a id="h17"></a>

### 8.17 Dividir un Excel es mucho más lento que convertirlo y se salta el control de memoria

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · B2-01*

- **Lo que siente la persona:** Con un Excel grande espera minutos con una estimación de segundos, y puede quedarse sin nada si se alcanza el límite.
- **Recomendación:** Primero lo barato: cargar el libro una sola vez y aplicar en Dividir la estimación de memoria y de tiempo del propio formato. Cortar el ZIP a mano solo con fixtures de gráficos, nombres definidos y fórmulas entre hojas.
- **Comprobación de la conciliadora:** xlsx_cut.py:35 load_workbook completo una vez por parte. planning.py:120-125 hace continue antes de estimated_memory. splitting.py:56-61 split_cost usa siempre la velocidad de PDF. No repetí las mediciones.

<a id="h18"></a>

### 8.18 Las estimaciones de tiempo y memoria se calculan por megabytes, y Unir en PDF usa la estimación de convertir

*🟠 Media · valor medio · esfuerzo medio · ◐ Parcial · B2-02, B1-08*

- **Lo que siente la persona:** Un PDF con muchas imágenes recibe un aviso de «más de 10 minutos» y se convierte en segundos. Una unión grande falla al final culpando a todos los documentos.
- **Recomendación:** Estimar los PDF por número de páginas, que PDFium cuenta al instante. Dar a cada tipo de trabajo su propio modelo de coste. Sumar el tamaño total de una unión al planear. Mientras tanto, suavizar el texto del aviso.
- **Comprobación de la conciliadora:** limits.py:21 y :47 (15 s/MiB y 16 MiB/MiB) y planning.py:149 confirmados. Las cifras medidas son de B2 y no las repetí. El caso de más de 512 MiB en B1-08 es deducido, sin ejecutar.

<a id="h19"></a>

### 8.19 Sin progreso dentro de un archivo largo, y al llegar a 10 minutos se pierde todo

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · B2-04*

- **Lo que siente la persona:** Varios minutos sin ninguna señal de avance; parece que el programa se colgó.
- **Recomendación:** Mensajes de «página N de M» limitados a uno por segundo. NO entregar un resultado parcial como si fuera el normal. Si algún día se hace, que sea con un nombre explícito («páginas 1 a N de M»).
- **Comprobación de la conciliadora:** Coherente con schemas/events.py y processes.py según la evidencia. Lo verifiqué de forma indirecta.

<a id="h20"></a>

### 8.20 Cada lote vuelve a arrancar el trabajador, y la ventana carga librerías que no usa

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · B2-05, F2-09, F2-05*

- **Lo que siente la persona:** Una espera fija de 1 a 2 segundos cada vez que pulsa Convertir, y una ventana que tarda más en abrir.
- **Recomendación:** Primero las importaciones diferidas, con una prueba de presupuesto de importación (barato). Después, arrancar el trabajador en segundo plano mientras la persona revisa y reutilizarlo en Convertir, sin mantenerlo vivo durante toda la sesión de entrada.
- **Comprobación de la conciliadora:** Dos mediciones independientes (B2 y F2) coinciden en la cadena supervisor→child→pages→xlsx_cut→openpyxl.

<a id="h21"></a>

### 8.21 El instalador pesa unos 176 MB para instalar por defecto unos 37 MB

*🟠 Media · valor alto · esfuerzo pequeño · ✅ Confirmada · F2-03, B2-07, F2-04*

- **Lo que siente la persona:** Una descarga larga y pesada, que gasta datos y da desconfianza, antes de ver el producto.
- **Recomendación:** Publicar un instalador liviano (ventana clásica + CLI) como descarga recomendada y el completo como opción. Separar el tar de Linux. Poner un límite de tamaño en CI para cada archivo publicado. Lo de onedir, solo después de medirlo en Windows.
- **Comprobación de la conciliadora:** Las cifras de gh release coinciden entre dos auditores. clearmd.iss:134-153 confirma ttkonly por defecto con los tres GUI empaquetados. No volví a consultar gh.

<a id="h22"></a>

### 8.22 Colores derivados por debajo de 4,5:1, aunque el ADR-0027 asegura que todo cumple AA

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F3-08*

- **Lo que siente la persona:** A las personas mayores o con baja visión les cuesta leer el texto atenuado y los botones deshabilitados.
- **Recomendación:** Subir DIM_TEXT a 4,5:1 y los bordes de los campos a 3:1. Agregar una prueba de contraste que recorra los colores mezclados. Corregir la frase del ADR.
- **Comprobación de la conciliadora:** El cálculo de F3 es reproducible. ttk/visuals/styles.py:35 comenta '3:1' para el texto atenuado, lo que contradice el ADR-0027.

<a id="h23"></a>

### 8.23 Ajustes no cabe en un portátil en Qt y no indica en flet que hay más opciones abajo

*🟠 Media · valor medio · esfuerzo medio · ✅ Confirmada · F3-04*

- **Lo que siente la persona:** No encuentra «Guardar», o no sabe que abajo están las opciones de Dividir y Unir.
- **Recomendación:** Contenido desplazable con los botones siempre fijos y visibles, y renombrar el «Guardar» de las partes a «Qué conservar».
- **Comprobación de la conciliadora:** Basado en el tamaño de la captura 016/6 (884 px) y en que no hay QScrollArea. Lo acepté sin medirlo de nuevo.

<a id="h24"></a>

### 8.24 El atajo «Dividir los PDF grandes» cambia sin avisar las preferencias guardadas de Dividir

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · F1-05*

- **Lo que siente la persona:** La próxima vez encuentra Dividir configurado distinto y no sabe por qué.
- **Recomendación:** Aplicar esas opciones solo a esa tanda, sin llamar a save().
- **Comprobación de la conciliadora:** tools.py:53-54 hace replace(settings, split_cut, split_parts, split_keep='markdown') y luego save(...).

<a id="h25"></a>

### 8.25 Al unir una carpeta, el orden es 1, 10, 11, 2 y no se puede corregir

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B1-04, F1-10*

- **Lo que siente la persona:** El capítulo 10 aparece justo después del 1 dentro del archivo unido.
- **Recomendación:** Usar orden natural en el escaneo y en las listas visibles. Mostrar el orden final en Revisar. NO desplegar la carpeta en entradas sueltas.
- **Comprobación de la conciliadora:** scan_rules.py:52 ordena por entry.name.casefold().

<a id="h26"></a>

### 8.26 El resumen se reemplaza en cada acción y puede borrar el PDF del resumen que la persona pidió

*🟠 Media · valor medio · esfuerzo pequeño · ◐ Parcial · B3-06*

- **Lo que siente la persona:** El PDF de resumen que pidió desaparece y, con él, los avisos de la conversión anterior.
- **Recomendación:** No borrar un archivo pedido de forma explícita: regenerarlo. El historial de pendientes es opcional y no es prioritario.
- **Comprobación de la conciliadora:** api/summaries.py tiene _remove_old y _remove_old_pdf. La reproducción es de B3 y no la repetí.

<a id="h27"></a>

### 8.27 En las tablas de PDF sin líneas, cada celda larga se parte en muchas filas

*🟠 Media · valor medio · esfuerzo medio · ◐ Parcial · B3-03*

- **Lo que siente la persona:** Una IA lee como filas distintas los trozos de un mismo registro.
- **Recomendación:** Unir las filas de continuación y agregar un fixture público al estilo de un artículo académico, con una métrica del porcentaje de filas de continuación.
- **Comprobación de la conciliadora:** La evidencia sale de un documento privado y no la verifiqué. Es plausible y su confianza es media.

<a id="h28"></a>

### 8.28 El README muestra un ClearMD más viejo y no menciona clearmd-cli

*🟠 Media · valor medio · esfuerzo pequeño · ✅ Confirmada · B4-08*

- **Lo que siente la persona:** Copia el ejemplo de la terminal y no funciona, y las capturas no se parecen a lo que instaló.
- **Recomendación:** Capturas actuales, una línea por herramienta y por carpeta, y la nota sobre clearmd-cli.
- **Comprobación de la conciliadora:** grep clearmd-cli: 0 resultados en README.md y README.es.md.

<a id="h29"></a>

### 8.29 La ventana abre en inglés aunque la persona instaló ClearMD en español

*🟠 Media · valor alto · esfuerzo pequeño · ✅ Confirmada · C-1*

- **Lo que siente la persona:** El instalador le habló en español, pero la primera pantalla de la app está en inglés y tiene que encontrar sola el ajuste del idioma.
- **Recomendación:** Sin reabrir ADR-0017 (que rechaza detectar el idioma del sistema): en la primera instalación, que el instalador escriba language=es en settings.toml cuando el asistente corrió en español. Así no hay que adivinar nada, porque el idioma ya lo eligió el asistente.
- **Comprobación de la conciliadora:** settings.py:12 language='en'. ADR-0017 decide «English by default». El instalador elige el idioma según el sistema (packaging/installer/README.md:39). La primera ronda lo tenía (F4-09, B4-05) y la ronda 2 lo dejó caer.

<a id="h30"></a>

### 8.30 Los Word, Excel y PowerPoint antiguos (.doc, .xls, .ppt) se rechazan con un genérico «formato no soportado»

*🟠 Media · valor alto · esfuerzo pequeño · ✅ Confirmada · C-2*

- **Lo que siente la persona:** Su documento de siempre «no está soportado» y la única pista es «revisa los formatos en la ayuda»; no sabe que basta con guardarlo como .docx.
- **Recomendación:** Reconocer las extensiones .doc, .xls y .ppt (y la firma OLE) con un motivo propio y una acción concreta: «Ábrelo en Word, Excel o PowerPoint y guárdalo como .docx, .xlsx o .pptx».
- **Comprobación de la conciliadora:** No existe ningún motivo específico en [skip] (es.toml:51-72), y unsupported_format solo dice «Revisa los formatos compatibles en la ayuda» (es.toml:85). La primera ronda lo tenía (B4-02 ref) y la ronda 2 lo dejó caer.

<a id="h31"></a>

### 8.31 Textos que describen el producto de antes y errores visibles de concordancia

*⚪ Baja · valor medio · esfuerzo pequeño · ✅ Confirmada · B4-04, F4-09, F3-05*

- **Lo que siente la persona:** «1 Fallidos», «Convierte más» (un botón que ya no existe) o «elige PDF o Markdown» le enseñan que los mensajes no son de fiar.
- **Recomendación:** Revisar el catálogo contra las herramientas actuales, generar las listas de formatos desde el código, usar las formas .one/.other en las tarjetas y usar «¿Dónde Van los Resultados?». El Title Case NO se discute: es doctrina del dueño; solo se aplica de forma uniforme con un linter.
- **Comprobación de la conciliadora:** es.toml:576 «PDF o Markdown» (pero :68 sí lista bien los formatos), :151 keep_needs_split sin --split-words, :453 «Convierte más», :319 «en tres pasos», :336 y :363 etiquetas fijas en plural.

<a id="h32"></a>

### 8.32 El instalador y los accesos directos muestran nombres de tecnología

*⚪ Baja · valor medio · esfuerzo pequeño · ◐ Parcial · B4-09, F2-06 (parte accesos)*

- **Lo que siente la persona:** Ve «ClearMD (flet) - La App Flutter», «(Qt)» y tres accesos directos, y duda cuál abrir.
- **Recomendación:** Renombrar los componentes y los accesos directos por lo que la persona nota, y dejar ttk, Qt y flet en una línea secundaria. No hace falta retirar ninguna ventana.
- **Comprobación de la conciliadora:** Los TIPOS ya son claros: clearmd.iss:91-96, «Solo la app clásica (recomendada: la más liviana)». La jerga está en los componentes (:100-104) y en los accesos directos.

<a id="h33"></a>

### 8.33 El paso 3 está casi vacío y la bienvenida promete «tres pasos» cuando hay cuatro

*⚪ Baja · valor medio · esfuerzo pequeño · ✅ Confirmada · F4-08, F3-10*

- **Lo que siente la persona:** Un clic y una confirmación de más, sin información nueva.
- **Recomendación:** Llenar el paso 3 con el destino, las cifras reales y la decisión tomada, y corregir la bienvenida. La fusión de pasos queda para un ADR posterior.
- **Comprobación de la conciliadora:** es.toml:319 «en tres pasos». secondary.py:37-41 solo muestra la cifra.

<a id="h34"></a>

### 8.34 Editar la lista o cambiar de herramienta borra los resultados de la pantalla sin aviso

*⚪ Baja · valor medio · esfuerzo pequeño · ✅ Confirmada · F1-06*

- **Lo que siente la persona:** Pierde el camino hacia sus archivos, aunque sigan en el disco.
- **Recomendación:** Un aviso de una línea y la ruta visible (F3-11). Sin un «deshacer» general.
- **Comprobación de la conciliadora:** reset.py editable() pone plan y report en None sin ningún mensaje.

<a id="h35"></a>

### 8.35 Dividir un documento que ya cabe anuncia «se dividió» y entrega una «parte 1 de 1»

*⚪ Baja · valor medio · esfuerzo pequeño · ✅ Confirmada · B3-04*

- **Lo que siente la persona:** No entiende si el archivo le servía tal como estaba.
- **Recomendación:** Un texto y un conteo propios («ya cabía en una sola parte»).
- **Comprobación de la conciliadora:** Lo reprodujo B3 y es coherente con parts.one. No lo repetí.

<a id="h36"></a>

### 8.36 Detalles de fidelidad y estabilidad: codificación de las partes, renombre ante un choque de nombres, cambios de opciones ignorados

*⚪ Baja · valor bajo · esfuerzo medio · ◐ Parcial · B1-05, B1-06, B1-09*

- **Lo que siente la persona:** Casos menos frecuentes: tildes dañadas en partes de un CSV, un resultado viejo duplicado, opciones que no se aplican.
- **Recomendación:** B1-09: un aviso barato. B1-06: un ADR. B1-05: solo con un fixture que lo demuestre.
- **Comprobación de la conciliadora:** No los reproduje. El código citado es coherente con lo que describen.

<a id="h37"></a>

### 8.37 La CLI mezcla idiomas y el roadmap promete subcomandos que no existen

*⚪ Baja · valor bajo · esfuerzo pequeño · ◐ Parcial · B4-07, B3-07*

- **Lo que siente la persona:** Poco visible para el público no técnico, que no usa la terminal.
- **Recomendación:** Corregir la frase del roadmap (sin alias), usar «Nada que unir» o «Nada que dividir» según la herramienta y documentar los códigos de salida.
- **Comprobación de la conciliadora:** roadmap.md:101-102 confirmado. El argparse en inglés y la ausencia de detección del idioma del sistema son brechas ACEPTADAS en ADR-0017. Los auditores no lo citaron.

<a id="h38"></a>

### 8.38 Mejoras de rendimiento, métricas y pulido de menor prioridad

*⚪ Baja · valor bajo · esfuerzo medio · ◐ Parcial · F2-02, F2-08, B2-03, B2-08, B2-09, F3-07, F1-09, B3-09, B3-10*

- **Lo que siente la persona:** Esperas o ruidos pequeños en casos de borde o de volumen alto.
- **Recomendación:** Agrupar en una etapa de «presupuestos medibles»: benchmark de PDFium, 1.000 filas por toolkit, tamaño de cada archivo publicado. Lo demás, cuando se toque el código.
- **Comprobación de la conciliadora:** Hay evidencia, pero en general con poco impacto para el usuario típico (lotes pequeños).

## 9. Los informes de cada auditor (tras el debate)

### Backend · Lógica — 6,5/10

Después de leer a los ocho auditores y de volver a revisar el código, mantengo mi diagnóstico: el caso feliz es sólido y las fallas están en las operaciones que tocan resultados anteriores o que juntan varios archivos. El debate me hizo subir dos problemas que otros colegas encontraron y que caen de lleno en la lógica del backend. El primero: al elegir una carpeta y además un archivo de esa carpeta, el archivo se convierte dos veces, y en Unir sale duplicado (F1-01). La planificación solo quita rutas idénticas (planning.py:78). El segundo: al dividir o unir un Markdown con imágenes, los enlaces quedan rotos y el resumen da todo por bueno (B3-01). También confirmé en el código la causa de B4-01. Cuando Unir se queda con menos de dos documentos, merging.py nunca crea la carpeta de resultados (prepare_root solo corre en la rama else), así que el resumen no se puede escribir y la persona ve "¿el disco está lleno?". Ese caso lo junto con mi hallazgo de diagnósticos falsos. Con esto, los riesgos más graves para la persona son tres: perder la división anterior, perder o duplicar contenido sin aviso (uniones del mismo minuto, archivos duplicados, imágenes rotas) y recibir datos mal estructurados (CSV con punto y coma). Todo se corrige con cambios puntuales y su prueba de regresión, sin rediseñar nada.

**Fortalezas que vio:**

- Escrituras atómicas de verdad (output_files.py): archivo temporal con nombre aleatorio, os.replace, nunca a través de enlaces, y limpieza de temporales huérfanos. Un corte de luz nunca deja un .md a medias.
- Proceso de conversión aislado con límites de tiempo, memoria y arranque (supervisor.py, processes.py). Un archivo malicioso o gigante no tumba la aplicación y queda como "se detuvo", no como "falló".
- Ningún fallo detiene el lote: una carpeta que no se puede escribir hace fallar solo sus archivos (execution.py).
- El "ya existe" se revisa de nuevo justo antes de escribir (execution.py:111). Un resultado que apareció entre el plan y la ejecución no se pisa sin preguntar.
- Los nombres repetidos se resuelven de forma determinista, sin distinguir mayúsculas ni formas Unicode, con recorte seguro a 200 bytes (paths.py).
- Cancelar nunca deja un resultado roto en Convertir: el resultado anterior queda intacto.
- El PDF con contraseña se reconoce con precisión (códigos 4 y 5 de PDFium), con un mensaje claro.
- La división por palabras se niega a producir una parte silenciosa con un PDF escaneado (ADR-0045), y la división por títulos nunca corta dentro de un bloque de código.
- Dividir un Excel conserva formatos y gráficos. Hay que mantenerlo aunque se cambie el método de corte (ver el debate con B2-01).

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B1-01 | 🔴 Alta | medio | alta | Volver a dividir borra las partes anteriores antes de tener las nuevas |
| B1-02 | 🔴 Alta | pequeño | alta | Dos uniones en el mismo minuto se sobrescriben sin avisar |
| B1-11 | 🔴 Alta | pequeño | alta | Una carpeta más un archivo de esa carpeta se procesan dos veces (incorporado de F1-01) |
| B1-12 | 🔴 Alta | medio | alta | Dividir o unir un Markdown con imágenes deja todos los enlaces rotos (incorporado de B3-01) |
| B1-03 | 🔴 Alta | pequeño | alta | Un CSV separado por punto y coma (el de Excel en español) sale como una sola columna |
| B1-07 | 🔴 Alta | medio | alta | Varios mensajes de error dan un diagnóstico falso, incluido Unir sin resumen y con "¿disco lleno?" |
| B1-04 | 🟠 Media | pequeño | alta | Al unir una carpeta, el orden es 1, 10, 11, 2, 3 y no se puede corregir |
| B1-05 | 🟠 Media | medio | alta | Las partes de un texto o CSV dividido cambian la codificación y los saltos de línea |
| B1-06 | 🟠 Media | medio | alta | El nombre de un resultado cambia si aparece otro archivo con el mismo nombre, y el viejo queda duplicado |
| B1-08 | 🟠 Media | medio | media | Unir en PDF valida los límites por archivo y no por el total, y falla al final culpando a todos |
| B1-09 | ⚪ Baja | pequeño | alta | "Reemplazar si el original cambió" ignora que la persona cambió las opciones |

<details><summary>Detalle técnico y evidencia</summary>

- **B1-01 — Volver a dividir borra las partes anteriores antes de tener las nuevas**
  - *Impacto:* Si la persona divide de nuevo un archivo y algo falla a mitad (cancela, una parte tarda demasiado, o en Windows tiene una parte abierta), pierde la división anterior completa y le queda una carpeta con solo algunas partes nuevas. Si la sube a una IA, le falta contenido sin saberlo.
  - *Evidencia:* splitting.py:120 (PDF), splitting.py:144 (Markdown) y split_formats.py:44 llaman a remove_earlier_parts() ANTES del bucle de escritura. Reproducido: `--split-parts 2` y luego, con un obstáculo en `t - part 2 of 3.txt`, `--overwrite --split-parts 3`: queda solo `t - part 1 of 3.txt`, y las dos partes buenas se borraron. Lo mismo ocurre con Cancelled o TIMED_OUT en la parte k.
  - *Recomendación:* Escribir las partes nuevas aparte (con nombres temporales dentro de OutputSep) y, solo cuando estén todas, moverlas a su sitio y borrar las anteriores. Si algo falla, borrar lo nuevo y conservar lo anterior. Agregar una prueba de regresión.
- **B1-02 — Dos uniones en el mismo minuto se sobrescriben sin avisar**
  - *Impacto:* Si la persona une A y B y en el mismo minuto une C y D, el primer resultado desaparece sin ninguna pregunta, y las dos veces el resumen dice "2 unidos".
  - *Evidencia:* api/naming.py:9 `STAMP = "%Y-%m-%d %H-%M"`; merging.py:39 fuerza exists=False. El ADR-0048 dice "Merge always writes a new file". Reproducido: dos `--merge markdown` seguidos dejan un solo `Merged ... 00-08.md`, con c y d.
  - *Recomendación:* Si el nombre ya existe, agregar un sufijo (2), (3). Nunca reemplazar un archivo unido sin preguntar. Agregar una prueba con dos uniones seguidas.
- **B1-11 — Una carpeta más un archivo de esa carpeta se procesan dos veces (incorporado de F1-01)**
  - *Impacto:* Arrastrar una carpeta y además un documento importante de ella es muy común. Convertir genera dos copias en dos ClearMD_Output distintos. Unir mete el documento dos veces en el archivo que se entrega a la IA.
  - *Evidencia:* use_cases/planning.py:78 `unique_inputs = list(dict.fromkeys(inputs))` solo quita rutas idénticas, y scan() recibe la carpeta y el archivo por separado. F1-01 lo reprodujo con el presentador real: el plan incluía ['sample.docx','sample.pdf','sample.pdf'].
  - *Recomendación:* Deduplicar en el backend (planning) por archivo real resuelto, después del escaneo, no en cada GUI. Conservar una sola aparición, la primera en el orden de la persona. Avisar en Revisar con una línea. Agregar una prueba para las tres herramientas.
- **B1-12 — Dividir o unir un Markdown con imágenes deja todos los enlaces rotos (incorporado de B3-01)**
  - *Impacto:* El flujo que el producto promueve (convertir con imágenes y luego dividir o unir para la IA) entrega archivos sin ninguna imagen visible, y el resumen dice que todo salió bien.
  - *Evidencia:* Reproducido por B3: las partes en OutputSep/<doc>/ y el archivo unido en OutputUnif/ conservan '![](<doc>_imagenes/...)' relativo a la ubicación original, sin copiar la carpeta. En splitting.py/merging.py no hay ningún paso que reescriba enlaces ni copie recursos.
  - *Recomendación:* Reescribir los enlaces relativos para que apunten bien desde la nueva carpeta (es lo más simple y no duplica archivos en disco). Si un enlace no se puede resolver, emitir una nota de atención. Agregar una prueba de que todo enlace local del resultado lleva a un archivo que existe.
- **B1-03 — Un CSV separado por punto y coma (el de Excel en español) sale como una sola columna**
  - *Impacto:* En Colombia, España y casi toda Latinoamérica, Excel guarda el CSV con punto y coma. La persona recibe una tabla de una sola columna ("nombre;ciudad"), y ClearMD reporta "convertido" sin ningún aviso.
  - *Evidencia:* markitdown_adapter.py:91 usa CsvConverter() de markitdown con la coma por defecto. No hay detección de separador (grep de delimiter/Sniffer: 0). Reproducido con 400 filas: `\| nombre;ciudad \|`.
  - *Recomendación:* Detectar el separador (coma, punto y coma, tabulador) con csv.Sniffer sobre una muestra, o usar un conversor CSV propio como ya se hizo con XLSX. Agregar un fixture con punto y coma, acentos y BOM.
- **B1-07 — Varios mensajes de error dan un diagnóstico falso, incluido Unir sin resumen y con "¿disco lleno?"**
  - *Impacto:* La persona sigue el consejo al pie de la letra y no sirve. Un Word con contraseña aparece como "dañado". Un .txt vacío aparece como "PDF escaneado". Una unión cancelada marca como fallidos los documentos buenos. Un archivo abierto en otro programa produce "comprueba el espacio en disco". Y al unir con un documento dañado no se escribe ningún resumen y se le pregunta si el disco está lleno.
  - *Evidencia:* (a) cifrado.docx con cabecera OLE D0CF11E0 → BadZipFile → error.corrupt_file. (b) split_formats.py:43 y splitting.py:143 usan NOTHING_TO_MEASURE, que tiene texto de PDF. (c) merging.py:132-133: la cancelación se convierte en NOTHING_TO_MERGE. (d) execution.py:77: cualquier OSError → WRITE_FAILED. (e) Confirmado en código (B4-01): prepare_root(root, MERGE_DIR_NAME) solo se ejecuta en la rama `else` de merging.py, así que con menos de 2 piezas ClearMD_Output no existe, writer.write falla en api/summaries.py:32-38 y _root_was_refused no lo cubre, y aparece 'summary_not_written (¿el disco está lleno?)'.
  - *Recomendación:* (a) Reconocer la firma OLE en .docx/.xlsx/.pptx como PASSWORD_PROTECTED. (b) Crear un código "archivo vacío". (c) Una unión cancelada sale como cancelada. (d) Separar PermissionError ("ciérralo en el programa que lo tenga abierto") del disco lleno. (e) Crear la carpeta de resultados antes de escribir el resumen también cuando Unir no produce archivo, y no adivinar la causa en summary_not_written. Una prueba por caso.
- **B1-04 — Al unir una carpeta, el orden es 1, 10, 11, 2, 3 y no se puede corregir**
  - *Impacto:* Una carpeta "Capítulo 1" a "Capítulo 11" se une con el capítulo 10 justo después del 1. Como la carpeta es un solo elemento en la lista, subir y bajar no ayudan.
  - *Evidencia:* scan_rules.py:50-52 ordena por entry.name.casefold(). planning.py conserva ese orden en Merge. presenter/intents/inputs.py:52 solo mueve entradas de primer nivel. Reproducido.
  - *Recomendación:* Usar orden natural, como el Explorador de Windows, al menos en Merge y en las listas que ve la persona.
- **B1-05 — Las partes de un texto o CSV dividido cambian la codificación y los saltos de línea**
  - *Impacto:* Al dividir un CSV con BOM o un .txt en ANSI, las partes "en su propio formato" salen en UTF-8 sin BOM y con LF. Al abrirlas en Excel, las tildes se ven dañadas.
  - *Evidencia:* El original empieza con EF BB BF y usa CRLF; la parte no tiene BOM y usa LF. cp1252 'A\xf1o' → UTF-8. pages.py _text + output_files.py:71-75 (UTF-8, \r\n → \n). Contradice el docstring de text_cut.py.
  - *Recomendación:* Cortar sobre los bytes originales, o volver a codificar como el original con BOM y CRLF. Agregar una prueba: unir las partes reproduce el archivo byte a byte.
- **B1-06 — El nombre de un resultado cambia si aparece otro archivo con el mismo nombre, y el viejo queda duplicado**
  - *Impacto:* Al agregar Informe.docx junto a Informe.pdf ya convertido, aparecen Informe (pdf).md e Informe (docx).md, y el viejo Informe.md se queda. La IA recibe el PDF dos veces.
  - *Evidencia:* paths.py resolve_names decide las etiquetas con el lote (incluidos los que fallan), no con lo que hay en disco. Reproducido con `--changed`: "2 converted" y tres archivos.
  - *Recomendación:* Mantener estable el nombre que ya tenía un original y dar la etiqueta al recién llegado. Como mínimo, avisar del resultado antiguo. Decidirlo en un ADR.
- **B1-08 — Unir en PDF valida los límites por archivo y no por el total, y falla al final culpando a todos**
  - *Impacto:* Al unir varios PDF grandes, si el total supera el tope, ClearMD trabaja hasta el final y marca todos los documentos como "No se pudo convertir", aunque ninguno tenga nada malo.
  - *Evidencia:* pages.py:77-80 rechaza resultados > max_result_bytes (512 MiB) con CONVERSION_FAILED; merging.py `_write` aplica ese problema a todos. planning.py:150 aplica a una copia de páginas la estimación de memoria de conversión. Deducido del código, sin ejecutarlo con más de 512 MiB.
  - *Recomendación:* Sumar los tamaños al planear y avisar antes de empezar con un mensaje propio ("únelos en dos grupos"). No usar la estimación de conversión para una copia de páginas.
- **B1-09 — "Reemplazar si el original cambió" ignora que la persona cambió las opciones**
  - *Impacto:* Si ayer dividió en 3 y hoy pide 5, todo aparece como "conservado" y la persona cree que su pedido se aplicó.
  - *Evidencia:* changes.py changed_since_result compara solo st_mtime; presenter/intents/conversion.py:27-28.
  - *Recomendación:* Avisar en Revisar o en el resumen que los cambios de opciones no cuentan como cambio. A futuro, guardar las opciones usadas y compararlas.

</details>

### Backend · Eficiencia — 6,5/10

Después del debate mantengo el diagnóstico de fondo. El backend usa la memoria con cuidado, el trabajador aislado con límites funciona y los ejecutables pesan 37 MB, pero las estimaciones de coste no corresponden a lo que de verdad pasa. Lo que más siente el usuario sigue siendo lo mismo. Las estimaciones por megabyte se equivocan en los dos sentidos: dan avisos falsos de "más de 10 minutos" en PDF ilustrados y se quedan cortas en PDF densos. Dividir un Excel es unas 4 veces más lento y pesado que convertirlo y no pasa por el control de memoria. Un PDF largo avanza sin dar progreso, y si pasa del límite se pierde entero. El debate me hizo ver que el problema es de clase y no solo de un formato. Unir en PDF, que solo copia páginas, toma prestada la estimación de memoria de convertir un PDF (lo confirmé en planning.py:149, en la línea que mencionó B1-08). Además, la ventana Frontend confirma por su lado que la interfaz carga librerías del trabajador y que el instalador pesa unas cinco veces lo que instala por defecto. Junto ambos hallazgos con los suyos. No hay nada catastrófico, pero hay avisos que asustan sin motivo, esperas sin explicación y trabajo que se pierde, y todo eso va contra "Claridad es cariño". Casi todo se arregla con un modelo de coste propio para cada tipo de trabajo.

**Fortalezas que vio:**

- Trabajador aparte con límites de tiempo y memoria revisados cada 0,1 s. Cancelar mata el proceso al instante y la ventana nunca se cuelga (supervisor.py, processes.py). F2 y B1 coinciden en que esto debe conservarse.
- El lector PDF va página por página con poca memoria: 1.299 páginas densas con 172 MiB de pico y un PDF real de 86 páginas con 44 MiB. Ese margen permite paralelizar en el futuro.
- Ejecutables livianos (37 MB), con una comprobación en CI que impide superar 50 MB o incluir numpy, pandas, onnxruntime o magika (packaging/check_executables.sh).
- La cola pone primero lo más barato, y la decisión se midió antes de tomarla (ADR-0050).
- Detección barata: primero la extensión, y el contenido se mira solo para archivos sin extensión (content_policy.py).
- La opción --changed compara solo fechas, sin leer ni calcular huellas de los archivos, y es instantánea en carpetas grandes. B1-09 señala con razón que no detecta cambios de opciones; la solución debe seguir siendo barata.
- Una imagen repetida (un logo en cada página) se guarda una sola vez, y el convertidor nunca escribe archivos.
- Hay cultura de medir: benchmarks reproducibles en tests/benchmark/ y límites con fuentes citadas (ADR-0015).

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B2-01 | 🔴 Alta | medio | alta | Dividir un Excel es mucho más lento y pesado que convertirlo, y se salta el control de memoria |
| B2-02 | 🔴 Alta | medio | alta | Las estimaciones de tiempo y memoria usan la unidad equivocada: los megabytes, y no lo que de verdad cuesta |
| B2-04 | 🟠 Media | medio | alta | Dentro de un archivo no hay progreso, y al llegar a los 10 minutos se pierde todo |
| B2-03 | 🟠 Media | medio | alta | El lector PDF va lento en texto denso: unas 11 páginas por segundo |
| B2-05 | 🟠 Media | medio | alta | Cada lote vuelve a arrancar el trabajador con todos los convertidores, y la interfaz carga librerías que no usa |
| B2-07 | 🟠 Media | pequeño | alta | El instalador pesa 176 MB para instalar por defecto un programa de 37 MB |
| B2-08 | ⚪ Baja | pequeño | alta | Los benchmarks no describen el lector PDF actual ni el ejecutable que recibe el usuario |
| B2-09 | ⚪ Baja | medio | media | Todo el archivo y todo el resultado viajan enteros por memoria, y la interfaz no tiene límite |

<details><summary>Detalle técnico y evidencia</summary>

- **B2-01 — Dividir un Excel es mucho más lento y pesado que convertirlo, y se salta el control de memoria**
  - *Impacto:* Quien divide un Excel grande, que es justo el caso en que dividir tiene sentido, espera unas cuatro veces más que si lo convirtiera entero. El tiempo estimado que ve no tiene relación con la realidad: unos 8 s frente a 138 s medidos. Con un Excel de 40 a 50 MB, la división puede terminar por falta de memoria o por el límite de 10 minutos después de una larga espera, y no queda nada. En Windows no hay tope de memoria del sistema, así que el portátil puede volverse muy lento antes de que llegue el error.
  - *Evidencia:* xlsx sintético de 10,9 MiB (4 hojas × 60.000 filas): cut_xlsx(path, 4) tardó 137,6 s con 1.056 MiB de pico, frente a 33,9 s y 236 MiB de XlsxConverter. services/split/xlsx_cut.py:35 llama a openpyxl.load_workbook(path) en modo completo una vez por parte; la línea 18 sí usa read_only, pero solo para contar. use_cases/planning.py:120-125: con split hace `continue` antes de inspect_archive y estimated_memory. use_cases/splitting.py:56-61: split_cost usa siempre la velocidad de PDF.
  - *Recomendación:* Cortar el Excel en su ZIP: copiar las entradas y quitar de workbook.xml y de sus relaciones las hojas que no van en cada parte. Esto no carga celdas. Si se mantiene openpyxl, cargar el libro una sola vez. Además, que la planificación de Dividir aplique a cada formato su propia estimación y la misma inspección del ZIP que la conversión. Si se hace así, también es más fácil escribir las partes en un temporal y moverlas al final, que es lo que pide B1-01.
- **B2-02 — Las estimaciones de tiempo y memoria usan la unidad equivocada: los megabytes, y no lo que de verdad cuesta**
  - *Impacto:* Un PDF ilustrado de más de unos 40 MB recibe el aviso "podría tardar más de 10 min" y la sugerencia de dividirlo, aunque se convierte en segundos. La persona se asusta o divide sin necesidad. Al revés, un PDF de texto denso tarda alrededor de un 40 % más de lo anunciado. Unir en PDF solo copia páginas, pero usa la estimación de memoria de convertir un PDF. En un portátil de 4 GB eso excluye PDF de unos 118 MB por una memoria que nunca usaría, y ese tope por archivo no impide que el resultado total supere el límite.
  - *Evidencia:* schemas/limits.py:22 y :47: PDF 15 s/MiB y 16 MiB/MiB. Medido en 5 PDF reales anónimos: entre 0,0 y 1,2 s/MiB, por ejemplo 2,64 MiB y 86 páginas en 3,1 s con 40 s estimados, y 44 MiB de memoria frente a 202 MiB estimados. PDF sintéticos densos: 261 páginas en 21,2 s (15 s estimados) y 1.299 páginas en 117 s (76 s estimados). Aviso en planning.py:187-191, corrección limitada en estimation.py:14-15 (MIN_FACTOR 0,2). En planning.py:149, `limits.estimated_memory(detection.format, ...)` se aplica también cuando merge no es None, y lo confirmé en esta ronda (en línea con B1-08).
  - *Recomendación:* Estimar los PDF por páginas y densidad, porque contar las páginas con PDFium es instantáneo (split/pdf_pages.py:36). Dar a cada tipo de trabajo (convertir, dividir y unir en PDF o en Markdown) su propio modelo de coste. Validar el total de una unión al planear, como propone B1-08. Llevar el factor de corrección por formato. Calibrar las constantes con PDF reales variados.
- **B2-04 — Dentro de un archivo no hay progreso, y al llegar a los 10 minutos se pierde todo**
  - *Impacto:* Durante un PDF de varios minutos, la persona solo ve que se está convirtiendo, sin páginas que avancen, y no sabe si el programa se colgó. Si el archivo pasa de 10 minutos, se detiene sin guardar nada, aunque llevara el 95 % hecho.
  - *Evidencia:* schemas/events.py no tiene eventos por página. El trabajador envía una sola respuesta por solicitud (worker/protocol.py, child.py:131-139). processes.py:107-114 mata el proceso al superar 600 s (limits.py:76) y lanza TIMED_OUT, y se descarta todo lo ya construido.
  - *Recomendación:* Que el trabajador envíe mensajes cortos de avance (página N de M) por la tubería que ya existe. Para el límite, usar "sin avance durante X s" en lugar de un tiempo total, o devolver lo convertido con una nota clara. Esto también le da a F1-07 datos reales que mostrar.
- **B2-03 — El lector PDF va lento en texto denso: unas 11 páginas por segundo**
  - *Impacto:* Un manual de 1.000 páginas densas tarda alrededor de un minuto y medio en esta máquina, y podría tardar el doble en un portátil modesto. El límite de 10 minutos alcanza para unas 6.500 páginas aquí y para bastantes menos en un equipo más lento.
  - *Evidencia:* cProfile de 261 páginas: page_chars.py:26 23,3 s; fonts.py:47 each_font 9,1 s, con 1,67 M de ctypes.cast; build_line 14,3 s. reader.py:30-32 recorre las páginas dos veces. Fuera del perfilador: entre 11 y 12 páginas por segundo, con 172 MiB de pico.
  - *Recomendación:* Reducir las llamadas ctypes por carácter (FPDFText_GetText por página para la primera pasada, sin cast por carácter) o fusionar las dos pasadas. Medirlo con el benchmark de B2-08. Como el PDF usa poca memoria, reconsiderar en ADR-0050 una excepción para PDF grandes que reparta los rangos de páginas entre dos núcleos.
- **B2-05 — Cada lote vuelve a arrancar el trabajador con todos los convertidores, y la interfaz carga librerías que no usa**
  - *Impacto:* Cada vez que se pulsa Convertir, Dividir o Unir, hay una espera fija de 1,2 a 1,8 s antes del primer archivo, y probablemente más en Windows con antivirus. En lotes pequeños, que son los habituales, esa espera es casi todo el tiempo. Además, la ventana y `clearmd --version` tardan más de 1 s en arrancar porque cargan las librerías de Excel y de PDF, que solo usa el trabajador.
  - *Evidencia:* api/__init__.py: plan_batch (:103) y run_batch (:146) crean cada uno su WorkerRunner y lo cierran en finally. Medido hasta Ready: 1,85, 1,81 y 3,45 s. registry.py:57-91 importa todos los convertidores, unos 2,2 s acumulados. Un lote de 10 fixtures tarda entre 2,9 y 3,1 s, y limits.py:81 worker_startup_seconds vale 0,7. Interfaz: `clearmd --version` tarda 1,13 s. La cadena supervisor.py:17 → child → pages → xlsx_cut → openpyxl coincide con la medición independiente de F2-05 (0,51 de 0,71 s del presenter vienen de composition). La palabra "persistente" de F2 vale dentro de un lote, no entre lotes.
  - *Recomendación:* Mantener un trabajador vivo durante la sesión de la ventana, arrancado en segundo plano y cerrado tras unos minutos sin uso, y compartirlo entre análisis y conversión. Cargar cada convertidor la primera vez que se pide su formato. Que el supervisor no importe el módulo del hijo, e importar pypdfium2 y openpyxl dentro de las funciones que los usan. Agregar una prueba de presupuesto de importación del presenter. Actualizar worker_startup_seconds con lo medido en Windows.
- **B2-07 — El instalador pesa 176 MB para instalar por defecto un programa de 37 MB**
  - *Impacto:* Quien sigue el README y elige el instalador descarga casi cinco veces lo que se le instala por defecto. Con conexión lenta o datos móviles es una espera y un gasto innecesarios. El paquete de Linux pesa 235 MB.
  - *Evidencia:* gh release view v2.8.1: Setup 176 MB; exe 37 MB; Qt 60 MB; Flet 80 MB; Linux 235 MB. clearmd.iss:134-152: el tipo por defecto es ttkonly, pero el instalador incluye los tres GUI y el CLI. F2-03 llegó de forma independiente a las mismas cifras, y F2-04 añade que el ttk instalado es onefile y se desempaqueta en cada arranque.
  - *Recomendación:* Subo la severidad a media, en línea con F2-03, y le doy más prioridad que la que tiene en el roadmap. Publicar un instalador liviano (ttk + CLI) y dejar el completo como opción. Separar el tar de Linux por ventana. Para el instalador, construir ttk en modo carpeta (F2-04). Agregar al 006b el tamaño de cada archivo publicado como métrica con límite.
- **B2-08 — Los benchmarks no describen el lector PDF actual ni el ejecutable que recibe el usuario**
  - *Impacto:* Las estimaciones que ve el usuario se basan en números que hoy nadie puede reproducir, y una regresión de velocidad pasaría sin que nadie la note.
  - *Evidencia:* docs/benchmarks/ solo tiene 001-004, y 001 mide pdfminer/markitdown. PDFium (ADR-0030) no tiene benchmark: limits.py:22 lo cita solo en un comentario. Todo se mide en el contenedor, con numpy y onnxruntime cargados, que el ejecutable excluye. F2-08 añade que flet-bench.yml falló en sus 3 últimas ejecuciones.
  - *Recomendación:* Crear el benchmark 005 del lector PDFium (páginas por segundo) con PDF sintéticos y reales públicos, más el arranque del trabajador medido en el ejecutable de Windows. Ejecutarlo a mano en CI antes de cada versión y compararlo con la anterior. Unirlo con las pruebas de presupuesto de interfaz que pide F2-08.
- **B2-09 — Todo el archivo y todo el resultado viajan enteros por memoria, y la interfaz no tiene límite**
  - *Impacto:* Con archivos cerca del máximo (250 MB), la memoria sube el doble de lo necesario, y el resultado completo llega al proceso de la ventana, que no tiene tope. Un equipo de 8 GB puede ponerse lento al final.
  - *Evidencia:* conversion/pdf/__init__.py:47 lee el archivo entero, y pdfium/document.py:27 lo copia de nuevo con create_string_buffer. child.py:94-99 permite enviar hasta 512 M caracteres por la tubería (limits.py:84), y las imágenes, hasta 200 MiB, viajan igual.
  - *Recomendación:* Evitar la segunda copia hacia PDFium. Para resultados grandes, que el trabajador escriba un temporal en ClearMD_Output y la interfaz solo lo mueva a su sitio, con cuidado de no reabrir el problema de temporales de B1-10. Darle prioridad al Job Object de Windows (006b) junto con B2-01.

</details>

### Backend · Experiencia de lo que entrega — 6,5/10

Después del debate mantengo el diagnóstico de la ronda 1, con más fuerza. Lo que ClearMD entrega suele ser confiable: un resumen bien ordenado, errores amables, títulos bien jerarquizados y fórmulas en LaTeX. Las fallas están en los lugares donde una persona no técnica no puede darse cuenta de que algo salió mal. Hay cuatro casos claros. Al dividir o unir, las imágenes quedan con enlaces rotos y el resumen igual muestra ✅. Un CSV con punto y coma (el de Excel en español, hallazgo B1-03) sale como una sola columna marcado como "convertido". Dos uniones hechas en el mismo minuto se pisan (B1-02). Y una unión con un documento dañado no deja ni resumen ni explicación (B4-01). En sentido contrario, casi todo PDF sale con "⚠️ necesita tu atención" por una limpieza que en realidad es buena noticia. Lo comprobé en content.py:73-77: cualquier nota, sea informativa o grave, cuenta como atención. Por eso los avisos de verdad se pierden entre los falsos. El resultado es una señal invertida: el producto da por buenos fallos reales y avisa de cosas buenas. Eso choca con "Claridad es cariño" más que cualquier detalle visual. Uní mi hallazgo de la línea de comandos con B4-07, que lo cubre mejor, y lo dejé solo en lo que es propio de mi lente: la promesa del roadmap y los códigos de salida. La jerga de las notas ya la cubre B4-06; me quedé con el defecto concreto de los números sueltos en letra de código. Todo se corrige con esfuerzo pequeño o medio y sin rediseñar nada.

**Fortalezas que vio:**

- El resumen (Resumen_ClearMD.md) tiene un orden ejemplar para una persona no técnica: primero una frase que dice qué pasó y cuántas cosas necesitan atención, después dónde están los archivos, luego qué revisar, y al final el detalle técnico plegado. Lo que ya cumple la persona no cuenta como problema: en el resumen, los conservados van aparte y no en atención (content.py:73-94). Esto no se debe perder.
- El resumen en PDF es limpio y lleva la identidad visual del producto.
- Los mensajes de error son amables y dicen qué hacer (archivo dañado, protegido con contraseña, "ya es Markdown"). El PDF con contraseña se reconoce con precisión.
- ClearMD es honesto con lo que no pudo leer: indica las páginas escaneadas con su rango exacto y los caracteres ilegibles, en vez de entregar el texto incompleto sin decir nada.
- Una tesis real sale con los títulos bien jerarquizados, y los encabezados, pies y números de página repetidos desaparecen. Las fórmulas salen como LaTeX legible.
- Es seguro por defecto: no sobrescribe sin permiso en Convertir, las escrituras son atómicas, cancelar nunca deja un resultado roto y no se descargan imágenes remotas.
- Los nombres de salida se resuelven con criterio: "sample (docx).md" cuando dos archivos chocan, "doc - parte 2 de 3" en el idioma elegido y la carpeta "_imagenes".
- Es rápido con documentos normales: 17 documentos de prueba en 4,9 s y una tesis de 90 páginas con 48 imágenes en unos 10 s.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B3-01 | 🔴 Alta | medio | alta | Unir o Dividir un Markdown con imágenes deja todas las imágenes rotas y el resumen dice que todo salió bien |
| B3-02 | 🔴 Alta | pequeño | alta | Casi todo PDF sale con "⚠️ necesita tu atención" por una limpieza que es buena noticia |
| B3-03 | 🔴 Alta | medio | alta | En las tablas de PDF sin líneas, cada celda larga se parte en muchas filas sueltas |
| B3-04 | 🟠 Media | pequeño | alta | Dividir un documento que ya cabe anuncia que "se dividió" y entrega una "parte 1 de 1" |
| B3-05 | 🟠 Media | pequeño | alta | Algunas notas del resumen muestran un número suelto en letra de código |
| B3-06 | 🟠 Media | medio | alta | El resumen se reemplaza en cada acción: se pierden los avisos anteriores y hasta se borra el resumen en PDF que la persona pidió |
| B3-08 | 🟠 Media | pequeño | alta | En el archivo unido no se ve dónde empieza cada documento, y el nombre no dice qué contiene |
| B3-07 | ⚪ Baja | pequeño | alta | El roadmap promete `clearmd split` y `clearmd merge`, y la CLI responde con un error engañoso |
| B3-09 | ⚪ Baja | pequeño | media | Las páginas web se convierten por defecto con menús, aviso de cookies y pie pegados al texto |
| B3-10 | ⚪ Baja | pequeño | alta | Las partes divididas no dicen de dónde vienen y las imágenes no tienen descripción |

<details><summary>Detalle técnico y evidencia</summary>

- **B3-01 — Unir o Dividir un Markdown con imágenes deja todas las imágenes rotas y el resumen dice que todo salió bien**
  - *Impacto:* El camino que el producto promueve es convertir con imágenes y después dividir o unir para pasárselo a una IA. Ese camino entrega archivos donde ninguna imagen se ve. El resumen muestra ✅, así que la persona no se entera hasta que abre el archivo, y no sabrá arreglarlo.
  - *Evidencia:* Convertí una tesis real con --images (48 PNG en '<nombre>_imagenes/'). Después `clearmd w/tesis.md --split-words 5000`: las 4 partes en OutputSep/tesis/ tienen 1+26+11+13 enlaces '![](<nombre>_imagenes/image-0NN.png)', y esa carpeta no tiene ninguna imagen. `clearmd *.md --merge markdown`: el archivo unido conserva los mismos enlaces relativos y en OutputUnif/ solo está el .md. El resumen dice '✅ Los 2 documentos se unieron en un solo archivo.' Pasa lo mismo con TeX sin --images: '![Un gráfico](img/plot)' queda roto y no aparece ninguna nota.
  - *Recomendación:* Al dividir o unir Markdown, reescribir los enlaces relativos para que apunten bien desde la nueva ubicación, o copiar la carpeta de imágenes junto al resultado. Si no se puede, poner una nota de atención en el resumen ("las imágenes no se copiaron"). Agregar una prueba de aceptación: convertir con imágenes, dividir, unir y comprobar que cada enlace lleva a un archivo que existe.
- **B3-02 — Casi todo PDF sale con "⚠️ necesita tu atención" por una limpieza que es buena noticia**
  - *Impacto:* Quitar los encabezados y números de página repetidos es un beneficio, pero se presenta como un problema. La persona aprende que las advertencias no significan nada. Cuando llegue una advertencia real (páginas escaneadas, caracteres ilegibles, imágenes rotas), la pasará por alto.
  - *Evidencia:* summary/content.py:76: `[self._noted(o, markdown) for o in converted if o.notes]` mete en la lista de atención cualquier archivo que tenga una nota, sin distinguir su tipo, y content.py:123 pone Mark.ATTENTION. Un PDF limpio dividido da '⚠️ **El documento se dividió.** Una cosa necesita tu atención.', y la única nota es pdf_running_removed (es.toml:273). La terminal dice 'convertido con notas (ver el resumen)'. NoteKind.PDF_RUNNING_REMOVED se emite en services/conversion/pdf/__init__.py:65 con el mismo peso que PDF_TEXT_UNREADABLE.
  - *Recomendación:* Dar a cada tipo de nota un nivel: "información" (lo que ClearMD mejoró: encabezados quitados, guiones unidos) o "atención" (lo que la persona debe revisar). Las notas informativas van en un apartado tranquilo, "Lo que ClearMD limpió", sin ⚠️, y no cuentan en el total de "necesitan tu atención". Agregar una prueba: un PDF limpio da ✅.
- **B3-03 — En las tablas de PDF sin líneas, cada celda larga se parte en muchas filas sueltas**
  - *Impacto:* En artículos académicos, donde las tablas no tienen bordes, un solo registro aparece repartido en 5 a 8 filas con trozos de frase. Una persona no puede leer la tabla, y una IA tiende a tomar cada trozo como una fila distinta y saca conclusiones equivocadas de los datos.
  - *Evidencia:* En un artículo real convertido (docs/Examples, sin citar), 84 de 157 filas de tabla empiezan con la primera celda vacía ('\| \| w) \| \| (w of w); \|'): son continuaciones. Una sola entrada se reparte en 8 filas. La AC-02 de la feature 013 solo cubre las tablas con líneas. Para tablas sin líneas no hay criterio equivalente. La tesis, con tablas con bordes, sale mejor (60 de 195).
  - *Recomendación:* Unir con la fila de arriba las filas de continuación (primera columna vacía y el resto con texto que sigue la frase) también en tablas sin líneas, y agregar un criterio de aceptación con un PDF de prueba al estilo de un artículo académico. En los benchmarks, medir el porcentaje de filas de continuación como indicador de calidad.
- **B3-04 — Dividir un documento que ya cabe anuncia que "se dividió" y entrega una "parte 1 de 1"**
  - *Impacto:* La persona pide partes de 20.000 palabras y recibe "Los 2 documentos se dividieron", con ⚠️, pero lo que obtiene es una sola "parte 1 de 1" dentro de una carpeta nueva. No entiende qué pasó ni si el archivo ya le sirve tal como estaba.
  - *Evidencia:* `clearmd real --split-words 20000 --keep markdown` con documentos de 16.565 y 9.142 palabras. La terminal dice '2 divididos'. El resumen dice '⚠️ **Los 2 documentos se dividieron.**', con '(1 parte)'. El archivo queda en 'OutputSep/real/<doc>/<doc> - parte 1 de 1.md'. El texto viene de parts.one (es.toml:219).
  - *Recomendación:* Cuando el resultado es una sola parte, decirlo con un texto propio ("Ya cabe en una sola parte de ese tamaño: no hacía falta dividirlo"), contarlo aparte de los "divididos" y entregar el archivo con su nombre normal, sin crear la carpeta de partes.
- **B3-05 — Algunas notas del resumen muestran un número suelto en letra de código**
  - *Impacto:* "las fórmulas que ClearMD no puede pasar a LaTeX se muestran con su fuente StarMath: `2`" no se entiende: ¿la fórmula 2? ¿dos fórmulas? Parece un error del programa. En el resumen en PDF, el detalle técnico se ve en inglés ('PDFium could not open it (error 3)') dentro de un documento en español.
  - *Evidencia:* Las notas reciben conteos como si fueran elementos de una lista: odt/writer/report.py:14,17,23,26 '(count,)', html/writer/state.py:69,73,76 y tex/writer/state.py:83,86. writer.py:153 los muestra como código con `_code(item.subject)`. Al dibujar el resumen en PDF se ve 'Detalle Técnico: PDFium could not open it (error 3)' sin plegar. La jerga general de las notas la cubre B4-06; aquí queda solo el defecto de tipo de dato.
  - *Recomendación:* Distinguir en el catálogo las notas con conteo de las notas con lista de nombres, y redactar las primeras en prosa ("2 fórmulas quedaron en su formato original"). En el PDF, anteponer al detalle técnico "Para quien dé soporte:" o mostrarlo en letra pequeña al final.
- **B3-06 — El resumen se reemplaza en cada acción: se pierden los avisos anteriores y hasta se borra el resumen en PDF que la persona pidió**
  - *Impacto:* Quien convierte con resumen en PDF y después divide o une en la misma carpeta pierde la lista de "Necesita tu atención" de la conversión, porque el historial solo guarda una línea con totales. Además, el Resumen_ClearMD.pdf que pidió desaparece sin aviso. Si pensaba revisar las páginas escaneadas o los errores, ya no tiene dónde verlos.
  - *Evidencia:* `clearmd s --summary-pdf` deja Resumen_ClearMD.md y Resumen_ClearMD.pdf. Después, `clearmd s --split-parts 3` deja solo el .md, sin el PDF, con las notas únicamente de la división y el historial '- ... · 1 convertido · 0 omitidos · 0 con error'. Al revés pasa lo mismo: `--summary-pdf-only` borra el .md anterior.
  - *Recomendación:* No borrar un archivo que la persona pidió de forma explícita: regenerarlo con lo último. Conservar en el historial plegado los avisos sin resolver de lotes anteriores ("Pendientes de antes"), o tener un resumen por herramienta dentro de ClearMD_Output.
- **B3-08 — En el archivo unido no se ve dónde empieza cada documento, y el nombre no dice qué contiene**
  - *Impacto:* Los límites entre documentos solo están en comentarios HTML, que ningún visor de Markdown muestra. La persona ve un texto continuo y no sabe dónde termina uno y empieza el otro. El nombre "Unidos 2026-11-09 00-05.md" no dice qué hay dentro. Como solo tiene precisión de minutos, dos uniones seguidas se pisan (B1-02).
  - *Evidencia:* En 'OutputUnif/Unidos 2026-11-09 00-05.md', las líneas 1, 1252 y 1727 son '<!-- ClearMD: ... -->' y no hay ningún separador visible. En el resumen de Unir la columna Carpeta sale '—'. El texto del nombre es name = "Unidos {stamp}" (es.toml:596), y la precisión de minuto viene de api/naming.py:9.
  - *Recomendación:* Agregar por documento un separador visible y discreto (una línea horizontal y "Documento 2 de 3: <nombre>") y mantener el comentario para las máquinas. Proponer como nombre el del primer documento más "y N más", con un sufijo (2), (3) si ya existe (esto resuelve también B1-02). Mostrar la carpeta de origen en el resumen.
- **B3-07 — El roadmap promete `clearmd split` y `clearmd merge`, y la CLI responde con un error engañoso**
  - *Impacto:* Quien escribe `clearmd split archivo.pdf`, como sugiere el roadmap, recibe "Not found: .../split" y "1 output(s) already exist", en inglés y sin relación con lo que pidió. Los códigos de salida tampoco se pueden predecir: "Nada que dividir" termina con 0 y ninguno está documentado en --help.
  - *Evidencia:* spec/roadmap.md:101-102: 'the command line gets `clearmd split` and `clearmd merge`'. `clearmd split in/sample.pdf` → 'Not found: /tmp/audit-B3/split' + '1 output(s) already exist. Run again with --overwrite or --skip.' EXIT=3. La traducción incompleta de argparse y los nombres internos de ajustes los documenta mejor B4-07; los dejo allí.
  - *Recomendación:* O corregir el roadmap, o crear los subcomandos como alias de las opciones actuales. Que una palabra que no es ruta y coincide con una herramienta dé un mensaje propio ("¿Quisiste decir --split-parts?"). Documentar los códigos de salida en el epílogo de --help.
- **B3-09 — Las páginas web se convierten por defecto con menús, aviso de cookies y pie pegados al texto**
  - *Impacto:* Una noticia guardada desde el navegador llega a la IA con el menú, el aviso de cookies y el pie, y el bloque de relacionados queda pegado al pie en la misma línea. Es ruido que la persona no sabe quitar y que la IA puede tomar por contenido.
  - *Evidencia:* news.md (modo por defecto 'full'): la primera línea es '[Inicio](/) [Deportes](/deportes) ... MENU-FIXTURE', después 'Usamos cookies ... Aceptar', y al final '[otra nota](/x)Diario de Prueba © 2026 · Términos' sin separación, aunque aside y footer son bloques distintos en el origen. En TeX, 'la ecuación (eq:pit)' deja ver una etiqueta interna.
  - *Recomendación:* Separar siempre con una línea en blanco los bloques de nivel superior (aside, footer, nav). Reconsiderar el modo por defecto, u ofrecer "solo el contenido principal" cuando se detecte un artículo claro. En TeX, mostrar las referencias como texto ("la ecuación 1").
- **B3-10 — Las partes divididas no dicen de dónde vienen y las imágenes no tienen descripción**
  - *Impacto:* Cuando la persona pega la "parte 3 de 4" en un chat de IA, el texto empieza a mitad de un capítulo, sin ninguna línea que diga a qué documento pertenece. La IA pierde el contexto. Las imágenes aparecen como '![]()' sin texto alternativo, así que ni la IA ni un lector de pantalla saben qué son.
  - *Evidencia:* 'tesis - parte 2 de 4.md' empieza directamente con '### 3.1 ...', y 'parte 4 de 4' empieza a mitad de una frase. Unir agrega '<!-- ClearMD: ... -->' y Dividir no, lo que es inconsistente. Las 51 imágenes de la tesis salen como '![](..._imagenes/image-001.png)'.
  - *Recomendación:* Empezar cada parte con una línea corta: "Parte 2 de 4 de «tesis» (continúa de la parte 1)". Dar a cada imagen un texto alternativo mínimo ("Imagen 3, página 12", o la leyenda cercana si existe).

</details>

### Backend · Claridad es cariño — 6,5/10

Tras leer a los otros siete auditores, mantengo el diagnóstico y lo refuerzo. ClearMD tiene una base de textos amable poco común: cada error trae mensaje y acción en los dos idiomas, el resumen abre con un titular humano y la promesa de privacidad es la misma en todas partes. Pero el producto pasó de una herramienta a tres (Convertir, Dividir, Unir) más rápido que sus textos. Cuatro auditores encontraron por separado que la Ayuda describe un recorrido que ya no existe, así que subo ese hallazgo a severidad alta. Lo más dañino para una persona no técnica son los mensajes que le dan un diagnóstico falso justo cuando algo sale mal. Uno es el '¿el disco está lleno?' al unir con un documento dañado, que reproduje. Otros los confirmaron colegas: cancelar una unión aparece como 'falló', un .txt vacío como 'PDF escaneado' y un Word cifrado como 'dañado'. Comprobé en el código que la cancelación se convierte en NOTHING_TO_MERGE. Además, la jerga técnica, el inglés crudo y las opciones de terminal se cuelan en la ventana y en el resumen. Las notas tampoco distinguen 'lo que ClearMD mejoró' de 'lo que debes revisar', lo que produce fatiga de alertas. Casi todo se arregla con cambios de texto y con pruebas que impidan que los textos vuelvan a envejecer.

**Fortalezas que vio:**

- Cada código de error tiene un par mensaje + acción en los dos idiomas (src/clearmd/i18n/es.toml:3-49), casi siempre con un paso concreto ('Quítale la contraseña…', 'Ciérralo en cualquier programa que lo tenga abierto (por ejemplo Excel)').
- Cuando el motivo es un límite, el mensaje da el valor medido junto al límite ('42 MB; límite 25 MB'), como pide spec/contracts/ux.md §3.
- El resumen abre con un titular humano y el conteo de lo que necesita atención, usa singular y plural correctos y deja el detalle técnico plegado. Los auditores B3 y F4 coinciden en que no se debe perder este orden.
- La promesa 'ClearMD nunca usa internet' es la misma en la Ayuda, el Inicio, el README y SECURITY, y el README avisa con honestidad sobre OneDrive y Dropbox.
- ClearMD es honesto con lo que no pudo leer: avisa de las páginas escaneadas con su rango exacto y de los caracteres ilegibles, en vez de entregar el texto incompleto sin decir nada (lo confirma B3).
- El desinstalador tranquiliza ('Tus documentos y tus carpetas ClearMD_Output nunca se tocan') y pregunta antes de borrar los ajustes.
- Un test exige que en.toml y es.toml tengan las mismas claves y los mismos marcadores: nunca falta una traducción.
- El botón principal desactivado siempre explica por qué (presenter/screens/primary.py, según F1): ningún botón queda muerto sin explicación.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| B4-01 | 🔴 Alta | pequeño | alta | Unir con un documento dañado deja a la persona sin resumen, sin explicación y con una alarma falsa de disco lleno |
| B4-02 | 🔴 Alta | pequeño | alta | Cuando falla algo raro, la única pista está en inglés técnico, y el 'repórtalo' no dice dónde |
| B4-03 | 🔴 Alta | pequeño | alta | La Ayuda describe un recorrido que ya no existe y deja fuera Dividir y Unir |
| B4-04 | 🟠 Media | pequeño | alta | Varios textos describen lo que el producto hacía antes, no lo que hace hoy |
| B4-05 | 🟠 Media | medio | alta | Comandos de terminal aparecen en la ventana, y nombres de botones aparecen en la terminal |
| B4-06 | 🟠 Media | pequeño | alta | Jerga técnica y palabras que asustan en los motivos, las notas y el resumen |
| B4-07 | 🟠 Media | medio | alta | La línea de comandos mezcla inglés y español, muestra nombres internos y usa códigos de salida confusos |
| B4-08 | 🟠 Media | medio | alta | El README muestra un ClearMD más viejo que el que se descarga |
| B4-09 | 🟠 Media | pequeño | media | El instalador y los accesos directos le hablan al público general en nombres de tecnología |
| B4-10 | ⚪ Baja | pequeño | alta | Vocabulario y conteos inconsistentes entre ventana, resumen y terminal |

<details><summary>Detalle técnico y evidencia</summary>

- **B4-01 — Unir con un documento dañado deja a la persona sin resumen, sin explicación y con una alarma falsa de disco lleno**
  - *Impacto:* Alguien une dos PDF y uno está dañado. Que ClearMD no escriba el archivo unido es correcto. Pero tampoco escribe el resumen, pregunta '¿el disco está lleno?' cuando hay espacio de sobra, señala una carpeta de resultados que no existe y marca el documento sano 'con error' sin decir por qué. La persona puede ponerse a borrar archivos para liberar un espacio que no hacía falta.
  - *Evidencia:* En el contenedor: `clearmd in/roto.pdf b.pdf --merge pdf --lang es --output-root m` produce '0 unidos · 0 omitidos · 2 con error', 'Resultados: …/m/ClearMD_Output' y '⚠ No se pudo escribir el resumen en … (¿el disco está lleno?).' con rc=1. Después, `find m` responde 'No such file or directory' y df muestra 891G libres. use_cases/merging.py:133 fija NOTHING_TO_MERGE, pero prepare_root (línea 138) solo se llama en la rama else, así que la carpeta nunca se crea. api/summaries.py:32-38 falla con OSError y _root_was_refused no cubre ese caso. Textos que adivinan la causa: es.toml:143 summary_not_written y es.toml:359 gui.result.no_summary ('Comprueba que el disco tiene espacio').
  - *Recomendación:* Crear la carpeta de resultados antes de escribir el resumen, aunque Unir no haya producido archivo. Mostrar en cada documento no unido su motivo (nothing_to_merge). Reescribir summary_not_written y no_summary para que digan solo lo que se sabe ('no se pudo escribir el resumen en …; comprueba que la carpeta existe y que puedes escribir en ella'). Agregar una prueba de aceptación: Unir con un documento dañado y uno sano.
- **B4-02 — Cuando falla algo raro, la única pista está en inglés técnico, y el 'repórtalo' no dice dónde**
  - *Impacto:* En un resumen en español, el 'Detalle Técnico' sale en inglés de programador ('BadZipFile: File is not a zip file', 'PDFium could not open it (error 4)'), y B3 confirma que también se ve en el resumen PDF. Para el error genérico, la única acción es 'Revisa el detalle técnico en el resumen': se manda a la persona a leer justo lo que no entiende. Ante un error inesperado, las dos ventanas y la terminal muestran el nombre interno de la excepción y piden 'repórtalo' sin decir cómo ni dónde.
  - *Evidencia:* es.toml:15-17 (error.conversion_failed, action 'Revisa el detalle técnico en el resumen.'). El resumen generado muestra '<details><summary>Detalle Técnico</summary>BadZipFile: …</details>'. presenter/intents/reset.py:24 arma detail = f"{type(error).__name__}: {error}" para es.toml:441 (gui.app.unexpected_error), y lo mismo pasa en frontend/cli/app.py:27 con es.toml:144. spec/contracts/ux.md §3: 'Never a traceback, an exception name or an error code alone'. F4-05, F1-07 y B1-07(e) llegan a lo mismo por caminos distintos.
  - *Recomendación:* Darle a conversion_failed una acción útil por sí sola ('Ábrelo en su programa original y guárdalo de nuevo; si sigue fallando, avísanos con el resumen adjunto'). Sacar el nombre de la excepción del texto principal de unexpected_error, llevarlo a un botón 'Copiar detalles' y añadir el enlace exacto de la página de issues. Encabezar el detalle técnico con 'Para quien te dé soporte:', para que la persona sepa que no necesita entenderlo.
- **B4-03 — La Ayuda describe un recorrido que ya no existe y deja fuera Dividir y Unir**
  - *Impacto:* La Ayuda es lo primero que abre quien se pierde. Explica un solo flujo ('Pulsa Convertir y revisa… Confirma'), pero en el paso 1 el botón se llama 'Siguiente' y no existe ningún botón 'Confirmar'. Tampoco menciona Dividir ni Unir, ni dónde quedan sus resultados (OutputSep, OutputUnif). Cuatro auditores lo encontraron por separado: una Ayuda equivocada es peor que no tener Ayuda.
  - *Evidencia:* es.toml:422-423 [gui.help] how/how_buttons: '2. Pulsa Convertir y revisa lo que va a pasar.'. No hay claves tool.split ni tool.merge que reemplacen gui.help.*, aunque [tool.split] y [tool.merge] sí reemplazan otras páginas. presenter/screens/primary.py:41-48 (los pasos 1 y 2 usan gui.nav.next). Captura docs/screenshots/016/5-help-light-es.png. Coinciden con esto F1-04, F3-06 y F4-02.
  - *Recomendación:* Reescribir la Ayuda según la herramienta activa: qué hace, qué archivos acepta, nombres reales de los botones y dónde quedan los resultados. Agregar una prueba que falle si una herramienta del Inicio no aparece en la Ayuda o si la Ayuda cita un botón que no existe en el catálogo.
- **B4-04 — Varios textos describen lo que el producto hacía antes, no lo que hace hoy**
  - *Impacto:* Algunos mensajes contradicen lo que el producto acepta. Dicen que Dividir solo recibe 'PDF o Markdown', aunque también recibe texto, CSV y Excel. Dicen que --keep solo va con dos opciones, aunque va con tres. Y 'Convierte más' remite a un botón que desapareció con la 033. La persona aprende que los mensajes no son de fiar.
  - *Evidencia:* es.toml [tool.split] gui.plan.nothing = '…elige archivos PDF o Markdown.'. cli.help.split_parts/split_pages dicen 'divide cada PDF…' y split_words 'cada PDF o Markdown'. cli.keep_needs_split = '--keep va con --split-parts o --split-pages.', pero frontend/cli/flow.py:45 también acepta --split-words. gui.settings.split_help omite 'unas N palabras'. cli.help.description = 'Convierte documentos a Markdown.'. gui.nav.done/nothing_written contienen 'Convierte más' (F4-09).
  - *Recomendación:* Revisar el catálogo completo contra las herramientas y formatos actuales. Generar las listas de formatos ('PDF, Markdown, texto, CSV o Excel') desde una sola fuente en el código. Cuando una feature quite un botón, buscar en el catálogo todas las frases que lo nombran y agregarlo a la lista de verificación de esa feature.
- **B4-05 — Comandos de terminal aparecen en la ventana, y nombres de botones aparecen en la terminal**
  - *Impacto:* En la ventana, la persona lee 'Conviértelo con --html full (la página completa de markitdown, sin la garantía de este modo)' o '(CLI: --overwrite)', instrucciones que no puede seguir desde ahí. En la terminal ocurre lo contrario: se le pide 'Elige En N partes' o 'Elige Un Markdown', nombres de botones que ahí no existen.
  - *Evidencia:* es.toml [skip_action] too_much_memory_for_article y existing_output. Se usan tal cual en la GUI (presenter/screens/review.py:24, results.py:34) y en el resumen (services/summary/content.py:172). En la terminal, `clearmd t.txt --split-pages 2 --lang es` imprime '…Elige En N partes o Partes de unas N palabras.' y `clearmd a.txt --merge pdf` imprime 'Elige Un Markdown…'. error.nothing_to_measure action = 'Divídelo mejor cada N páginas.' (es.toml:45) muestra la N literal. F4-07 encontró lo mismo.
  - *Recomendación:* Crear dos variantes de cada acción que cambie según el canal (por ejemplo skip_action.gui.* y skip_action.cli.*) y elegir según quién muestra el mensaje. En la ventana, nombrar el ajuste real ('Ajustes → Páginas Web → La página completa'). Agregar una prueba que prohíba '--' y nombres de librerías en los textos que llegan a la ventana.
- **B4-06 — Jerga técnica y palabras que asustan en los motivos, las notas y el resumen**
  - *Impacto:* El público general lee 'posible bomba ZIP', 'enlace simbólico', 'fuente StarMath: `2`' (un número suelto en letra de código), 'fuentes sin mapa de caracteres', '10 por KiB de fuente' o 'macros del autor'. 'Bomba', dicho de un archivo que pudo enviarle un colega, asusta. El resto no le dice si su documento quedó bien.
  - *Evidencia:* es.toml [skip]: symlink, archive_ratio '(posible bomba ZIP)'. [note]: formula_kept_as_source, pdf_text_decoded, encoding_guessed, macro_limit_reached. [note.reason]: expansions, nesting. B3-05 mostró la causa del número suelto: odt/writer/report.py:14-26 pasa conteos como ítems y summary/writer.py:153 los pinta con _code(). README.es.md repite 'posible bomba ZIP'.
  - *Recomendación:* Reescribir cada nota según lo que significa para la persona ('un acceso directo, no el archivo real'; 'este archivo se expande de forma sospechosa; por seguridad no se abre'; '2 fórmulas quedaron como texto original'). Tipar en el catálogo los parámetros de conteo frente a los de lista. Dejar KiB, niveles y nombres de motores solo en el detalle plegado. Las notas de LaTeX pueden seguir siendo técnicas.
- **B4-07 — La línea de comandos mezcla inglés y español, muestra nombres internos y usa códigos de salida confusos**
  - *Impacto:* Con --lang es, la ayuda dice 'usage', 'positional arguments', 'options', 'show this help message and exit' y 'error:'. Las descripciones nombran claves internas ('el ajuste html_strategy', 'el ajuste split_keep'). Cuando Unir no hace nada, imprime 'Nada que convertir.' y termina con 0, que el README define como 'todo convertido'. Además, se ignora el idioma del sistema (B3-07).
  - *Evidencia:* `clearmd --help --lang es`: 'usage:', 'positional arguments:', 'options:', '-h, --help show this help message and exit', '(por defecto: el ajuste recursive, activado)'. `clearmd a.txt --merge pdf --lang es` → 'Nada que convertir.' con rc=0. `clearmd t.txt --split-pages 2` → 'Nada que dividir.' antes del motivo, con rc=0. README.es.md: 'Códigos de salida: 0 todo convertido'. B3 reprodujo que `LANG=es_CO.UTF-8 clearmd --help` sale en inglés.
  - *Recomendación:* Traducir las cadenas propias de argparse con el catálogo. Cambiar 'el ajuste X' por el nombre visible en Ajustes. Usar 'Nada que unir' o 'Nada que dividir' según la herramienta e imprimir los motivos antes del cierre. Respetar el idioma del sistema cuando no haya preferencia guardada. Documentar los códigos de salida en un epílogo de --help.
- **B4-08 — El README muestra un ClearMD más viejo que el que se descarga**
  - *Impacto:* Quien llega al repositorio ve capturas de la 0.2 (sin Inicio, sin Dividir ni Unir). La tabla de opciones no trae las de Dividir y Unir, y 'Qué produce' solo nombra OutputMD. Quien instaló la línea de comandos con el instalador debe escribir 'clearmd-cli', pero el README solo enseña 'clearmd': copia el ejemplo y no funciona. Las cifras internas no cuadran (25 ADR frente a 52), lo que resta confianza.
  - *Evidencia:* README.es.md: 'Un vistazo' usa docs/screenshots/007/*. La tabla 'Opción \| Qué hace' no incluye --split-*, --merge, --changed, --summary-pdf ni --images. `ls docs/decisions \| wc -l` = 52. `grep clearmd-cli README.md` no da resultados, mientras clearmd.iss:109-110,122-123 y packaging/clearmd.spec:119 usan clearmd-cli. La insignia dice 'en construcción' en la 2.8.1. SECURITY.md usa 'ClearMD-Setup-1.2.0.exe' como ejemplo.
  - *Recomendación:* Actualizar el README a la 2.8.1: capturas actuales, una línea por herramienta en 'Qué produce' (y qué significan OutputMD, OutputSep y OutputUnif), las opciones de Dividir y Unir, y la nota 'si instalaste con el instalador, el comando es clearmd-cli'. Quitar las cifras que envejecen o generarlas automáticamente.
- **B4-09 — El instalador y los accesos directos le hablan al público general en nombres de tecnología**
  - *Impacto:* La primera decisión de una persona no técnica es elegir entre seis tipos de instalación con nombres de herramientas de programación (ttk, Qt, flet, Flutter, LGPL, PATH). Después ve tres accesos directos (ClearMD, ClearMD (Qt), ClearMD (flet)) y no sabe cuál abrir. La opción recomendada viene marcada, pero la página siembra la duda de si está eligiendo mal.
  - *Evidencia:* packaging/installer/clearmd.iss:85-105 (seis tipos; CompFlet 'ClearMD (flet) - La App Flutter'), 116-123 (CompareQt '…(LGPL)'), 109-110 TaskAddPath 'PATH', 188-190 (tres accesos directos, que F2-06 también señala). En inglés, RemoveSettings (línea 130) no es una pregunta; en español (131) sí.
  - *Recomendación:* Nombrar cada opción por lo que la persona nota: 'Recomendada (liviana)', 'Más nítida en pantallas grandes', 'Estilo móvil'. Dejar a la vista solo 'Recomendada' y 'Todo', y mover el resto a Personalizada. Llevar ttk, Qt, flet y LGPL a una línea secundaria. Que los accesos directos de las variantes digan lo mismo que su opción.
- **B4-10 — Vocabulario y conteos inconsistentes entre ventana, resumen y terminal**
  - *Impacto:* La misma cosa cambia de nombre según la pantalla: 'Fallidos' en la ventana, 'Con error' en el resumen y la terminal; 'computador' y 'equipo' en la misma ventana. Lo que la persona eligió conservar se cuenta como 'omitido' y aparece bajo 'Lo que Necesita Tu Atención' (F4-06). El mensaje del conversor caído culpa al archivo sin dar un siguiente paso.
  - *Evidencia:* es.toml:361-363 gui.result.stat_failed 'Fallidos' frente a summary.failed y count.failed.* 'Con error'. gui.app.subtitle '…en tu computador' frente a gui.app.local '…tu equipo'. presenter/screens/results.py:44-45 suma KEPT a los omitidos (hallazgo de F4). es.toml:47-49 worker_crashed action: '…puede que el archivo esté dañado'.
  - *Recomendación:* Fijar un glosario corto en spec/contracts/ux.md (resultado, conservado, omitido, con error, computador) y agregar una prueba que detecte sinónimos prohibidos. Sacar los conservados de la sección de atención. En worker_crashed, sugerir algo concreto ('ábrelo y guárdalo de nuevo, o divídelo; si sigue pasando, avísanos').

</details>

### Frontend · Lógica — 7/10

Después del debate mantengo el diagnóstico. La máquina de estados del frontend es sólida: un solo presentador, generaciones que descartan resultados viejos, una pausa contra el doble clic y una misma regla de cierre para las tres ventanas. Los fallos están en lo que el presentador cuenta y permite en los casos límite. Los otros auditores confirmaron tres de mis hallazgos por caminos distintos. F4-06 encontró, igual que F1-03, que lo que la persona decidió conservar se cuenta como problema. B4-01 mostró que Unir con un documento dañado también acaba "con menos de dos" y sin explicación, el mismo hueco que F1-02. F4-05 y B4-02 coinciden con F1-07 sobre el error inesperado. Por eso fusiono esos hallazgos y subo la prioridad del conteo engañoso al repetir una tanda: le pasa a cualquiera que convierta dos veces la misma carpeta con la opción por defecto. Agrego un hallazgo nuevo que me hizo notar B1-04: en Unir, una carpeta no se puede reordenar por dentro. La Ayuda desactualizada la reportaron cuatro auditores, así que dejo solo mi aporte propio: la Ayuda elige el texto según la ventana y no según si la ventana acepta arrastrar archivos. Nadie se queda atascado sin salida, pero hay trabajo repetido, conteos que no cuadran y pérdida del camino a los resultados.

**Fortalezas que vio:**

- Un único presentador (presenter/) decide estados, textos y navegación para las tres ventanas, y cada ventana solo dibuja. Por eso cancelar, cerrar, "¿Qué Sigue?" y "Conservar los archivos" se comportan igual en ttk, Qt y flet. Esto reduce mucho el costo de tener tres ventanas que señala F2-06.
- Cada trabajo lleva un número de generación (background.py:23-31). Lo que devuelve un análisis cancelado se descarta solo y nunca aparece en una pantalla vieja.
- Hay una pausa de medio segundo tras cada cambio de página (chrome/primary_gate.py), y Enter sostenido cuenta como una sola pulsación. Un doble clic no se salta Revisar y Convertir.
- Cerrar la ventana mientras convierte cancela la tanda, oculta la ventana y espera a que se escriba el resumen (chrome/close_policy.py), con la misma regla en las tres ventanas.
- La respuesta sobre los resultados existentes se guarda con el número del plan (plan_id). Cambiar idioma o tema no la borra, y un plan nuevo vuelve a la opción segura, Conservar.
- Un botón principal desactivado siempre explica por qué (screens/primary.py).
- Agregar dos veces el mismo archivo se ignora sin borrar el plan (inputs.py:24-33). Cambiar idioma o tema a mitad del recorrido vuelve a dibujar el plan y los resultados en el idioma nuevo.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F1-01 | 🔴 Alta | pequeño | alta | Una carpeta y un archivo de esa carpeta se convierten dos veces, en dos lugares distintos |
| F1-03 | 🔴 Alta | medio | alta | Al repetir una tanda, la app anuncia trabajo que no hará, cuenta lo conservado como problema y no deja abrir los resultados |
| F1-02 | 🟠 Media | pequeño | alta | Unir con menos de dos documentos útiles solo falla al final, sin explicación clara |
| F1-05 | 🟠 Media | medio | alta | "Dividir los PDF grandes" cambia sin avisar las preferencias de Dividir y reemplaza la lista de la persona |
| F1-06 | 🟠 Media | medio | alta | Quitar, reordenar o cambiar de herramienta borra el plan o los resultados sin avisar |
| F1-10 | 🟠 Media | pequeño | alta | En Unir, una carpeta entra como un bloque que no se puede reordenar y sale en orden 1, 10, 2 |
| F1-07 | 🟠 Media | medio | media | Un error inesperado borra la vista de lo hecho y muestra el nombre técnico del error |
| F1-04 | ⚪ Baja | pequeño | alta | La Ayuda elige su texto según la ventana, no según lo que la ventana permite en ese momento |
| F1-08 | ⚪ Baja | pequeño | alta | Convertir no recuerda lo que se decidió en Revisar sobre los resultados existentes |
| F1-09 | ⚪ Baja | pequeño | alta | Lo que se suelta en la ventana mientras trabaja se descarta sin ninguna señal |

<details><summary>Detalle técnico y evidencia</summary>

- **F1-01 — Una carpeta y un archivo de esa carpeta se convierten dos veces, en dos lugares distintos**
  - *Impacto:* Es muy común arrastrar una carpeta y además un documento importante que está dentro de ella. ClearMD convierte ese documento dos veces y crea dos carpetas ClearMD_Output, una junto a la carpeta y otra dentro de ella, cada una con su resumen. La persona no sabe cuál copia es la buena. En Unir el documento sale repetido dentro del archivo unido que se entrega a la IA.
  - *Evidencia:* Presentador real en el contenedor (/tmp/audit-logic/probe.py), add_paths([docs, docs/sample.pdf]): plan con ['sample.docx','sample.pdf','sample.pdf']; destinos w/ClearMD_Output/OutputMD/docs/sample (pdf).md y w/docs/ClearMD_Output/OutputMD/sample.md; dos Resumen_ClearMD.md. Unir [docs, docs/sample.docx] da ['sample.docx','sample.pdf','sample.docx'] hacia el mismo OutputUnif. planning.py:78 solo quita duplicados idénticos (dict.fromkeys); inputs.py:24-33 tampoco detecta la contención.
  - *Recomendación:* Al planear, quitar todo archivo que ya cubre una carpeta elegida y dejar una sola aparición por archivo real. En Revisar, avisarlo en una línea ("sample.pdf ya está dentro de docs: se convierte una sola vez"). Agregar una prueba para Convertir, Dividir y Unir.
- **F1-03 — Al repetir una tanda, la app anuncia trabajo que no hará, cuenta lo conservado como problema y no deja abrir los resultados**
  - *Impacto:* Pasa cada vez que alguien convierte de nuevo la misma carpeta con la opción por defecto, Conservar. El paso Convertir dice "Listo para convertir: 2". Al terminar no se escribe nada, lo conservado aparece como "Omitidos" y bajo "Lo que Necesita Tu Atención", el estado dice "con problemas" y "Abrir carpeta de resultados" queda apagado con "Este lote no escribió ningún archivo", aunque los resultados están en el disco. La persona se alarma por haber hecho lo correcto y no llega a sus archivos.
  - *Evidencia:* /tmp/audit-logic/probe2.py, segunda tanda: ready_line 'Ready to convert: 2', filas [EXISTS, EXISTS]; tras confirm(False): '0 converted · 2 skipped' y Primary(enabled=False). chrome/secondary.py:41 usa plan.stats[0] sin restar los conservados. screens/results.py:26-27 mete KEPT en la lista de filas con gui.result.kept; :45 y :53 suman KEPT a omitidos; :63-72 result_folders solo cuenta CONVERTED. Coincide con F4-06.
  - *Recomendación:* Contar con la decisión ya tomada: "2 ya existen y se conservan; no hay nada nuevo que convertir". Si todo se conserva, que la acción principal sea "Abrir resultados existentes". En Resultados, una categoría propia "Conservados" fuera de la sección de atención, sin marcar el lote como problemático, y result_folders debe incluir las carpetas de lo conservado. Probar siempre la segunda ejecución.
- **F1-02 — Unir con menos de dos documentos útiles solo falla al final, sin explicación clara**
  - *Impacto:* La persona elige un solo archivo en Unir, o dos con uno dañado, y recorre los cuatro pasos. Recién en Resultados se entera de que no había nada que unir. Según B4-01, en el caso del dañado ni siquiera recibe el motivo: solo una alarma falsa de disco lleno.
  - *Evidencia:* Probe: Unir con [sample.pdf] llega a WAITING_DECISION con 1 conversión. screens/primary.py:44-48 deja Siguiente activo con cualquier cantidad y no mira la herramienta. El límite solo existe en el backend: merging.py:133 NOTHING_TO_MERGE. B4-01 lo reprodujo por CLI con un PDF dañado.
  - *Recomendación:* En el paso 1 de Unir, desactivar Siguiente con menos de dos archivos y explicar por qué ("Agrega al menos dos documentos"). En Revisar, si las omisiones dejan uno solo, decirlo antes de convertir. En Resultados, mostrar el motivo nothing_to_merge en cada documento no unido.
- **F1-05 — "Dividir los PDF grandes" cambia sin avisar las preferencias de Dividir y reemplaza la lista de la persona**
  - *Impacto:* El atajo guarda como preferencia permanente "en N partes" y "conservar solo Markdown". La próxima vez que la persona use Dividir por su cuenta encuentra otras opciones; por ejemplo, ya no recibe los PDF partidos. Además, el resto de los archivos que había elegido en Convertir se pierde sin aviso.
  - *Evidencia:* presenter/intents/tools.py:50-55: choose_tool(Tool.SPLIT), s.inputs = [los PDF grandes], replace(settings, split_cut='parts', split_parts=parts, split_keep='markdown') y save(...). Valor por defecto split_keep='both' (backend/schemas/settings.py:30).
  - *Recomendación:* Aplicar esas opciones solo a esta tanda, sin guardarlas. Recordar la lista de Convertir y ofrecer volver a ella desde "¿Qué Sigue?".
- **F1-06 — Quitar, reordenar o cambiar de herramienta borra el plan o los resultados sin avisar**
  - *Impacto:* Desde Resultados, la persona vuelve a Elegir, quita un archivo o reordena uno en Unir, y los resultados desaparecen de la pantalla; "Abrir carpeta de resultados" se apaga. Lo mismo pasa al tocar otra herramienta o "Incluir Subcarpetas". No hay mensaje ni forma de deshacer. Los archivos siguen en el disco, pero la persona pierde el camino para llegar a ellos, y la pantalla tampoco muestra la ruta (F4-03).
  - *Evidencia:* presenter/intents/reset.py:10-20 editable(): plan=None, report=None, state=READY y view.forget_work(), sin mensaje. Se llama desde inputs.py (add, remove, move, clear, output), tools.py:30 y preferences.py:93-96. La regla viene de ADR-0029, pero no se comunica.
  - *Recomendación:* Cuando un cambio descarta un resultado, avisar en una línea ("Tus resultados anteriores siguen en su carpeta") y dejar "Abrir resultados anteriores" disponible hasta la próxima conversión.
- **F1-10 — En Unir, una carpeta entra como un bloque que no se puede reordenar y sale en orden 1, 10, 2**
  - *Impacto:* La persona agrega a Unir una carpeta de capítulos y espera el orden del Explorador. Los botones subir y bajar (032) solo mueven la carpeta entera, y por dentro el orden es alfabético. El capítulo 10 queda detrás del 1 y la persona no puede corregirlo desde la ventana.
  - *Evidencia:* presenter/intents/inputs.py:52-67 move_input solo permuta s.inputs (primer nivel). El orden interno lo da scan_rules.py:50-52 (casefold, no natural), reproducido por B1-04.
  - *Recomendación:* Además del orden natural que propone B1-04, al agregar una carpeta en Unir desplegar sus archivos como entradas propias de la lista, o al menos mostrar en Revisar el orden final con un aviso.
- **F1-07 — Un error inesperado borra la vista de lo hecho y muestra el nombre técnico del error**
  - *Impacto:* Si algo falla a mitad de una tanda larga, la app vuelve a Elegir con "lo ya convertido se conserva", pero no muestra qué se convirtió ni dónde está. Además, el texto incluye algo como "KeyError: ..." y pide reportar sin decir dónde (coinciden F4-05 y B4-02).
  - *Evidencia:* presenter/intents/conversion.py:95-97 llama a reset.unexpected; reset.py:23-32 pone report=None y plan=None, y detail=f"{type(error).__name__}: {error}". Contradice ux.md §3.
  - *Recomendación:* Abrir Resultados con lo que se alcanzó a escribir y un mensaje sencillo. El detalle técnico va detrás de un botón "Copiar detalles para reportar", junto con el enlace exacto a la página de issues.
- **F1-04 — La Ayuda elige su texto según la ventana, no según lo que la ventana permite en ese momento**
  - *Impacto:* Cuatro auditores ya reportaron que la Ayuda describe un recorrido viejo. Mi aporte es otro: en ttk, la Ayuda dice "o suéltalos en la ventana" aunque la ventana no acepte arrastrar archivos cuando falta tkdnd. La persona lo intenta y no pasa nada. En flet se usa la variante sin arrastrar incluso cuando sí se podría.
  - *Evidencia:* ttk/views/dialogs/help.py y pyside/views/dialogs/help.py usan siempre la clave 'how' (que menciona soltar); flet usa 'how_buttons' (flet/views/dialogs/help.py:15). En ttk el arrastre depende de self.drops (ttk/window/window.py:46). La reescritura de fondo de la Ayuda la cubren F4-02, F3-06 y B4-03.
  - *Recomendación:* Al reescribir la Ayuda (F4-02), elegir la variante con o sin arrastrar según la capacidad real de la ventana (por ejemplo, un dato que el presentador recibe de la vista), y probarlo.
- **F1-08 — Convertir no recuerda lo que se decidió en Revisar sobre los resultados existentes**
  - *Impacto:* La persona elige Reemplazar o Conservar en el paso 2 y pulsa Convertir en el paso 3 sin ver qué eligió. Reemplazar sobrescribe archivos.
  - *Evidencia:* ttk, pyside y flet window/primary_button.py leen review.overwrite_answer() al pulsar Convertir; chrome/secondary.py:37-41 (ready_line) solo muestra la cantidad.
  - *Recomendación:* Mostrar la decisión en la tarjeta de Convertir ("2 ya existen: se reemplazarán"). Si se acepta unir Revisar y Convertir (F3-10, F4-08), este problema desaparece solo.
- **F1-09 — Lo que se suelta en la ventana mientras trabaja se descarta sin ninguna señal**
  - *Impacto:* Durante el análisis o la conversión, la persona suelta más archivos en ttk o flet y no pasa nada. Cree que los agregó.
  - *Evidencia:* ttk/window/inputs.py:49-52 sin rama else; presenter/intents/inputs.py:32 retorna en silencio cuando editable() es False. PySide6 sí rechaza en drag_enter (pyside/window/inputs.py:55-57).
  - *Recomendación:* Mostrar "Espera a que termine para agregar más archivos", o guardarlos para la siguiente tanda y decirlo.

</details>

### Frontend · Eficiencia — 6/10

Mantengo el diagnóstico de la ronda 1 con dos correcciones honestas. La base es sana: el trabajo pesado va en un proceso aparte, el progreso se refresca una vez por segundo y la lista Qt escala bien. Primera corrección: en la ronda 1 dije que el icono de cada fila de ttk se leía del disco sin caché, y no es así (marks.icon lleva @cache). El costo real está en otra parte: por cada fila se dibujan dos casillas con supermuestreo y LANCZOS, se compone el número con PIL y se crean dos PhotoImage. Las mediciones no cambian: con 1.000 archivos, unos 3 s de ventana congelada, y con 3.000, casi 10, en la ventana que se instala por defecto. Segunda corrección: B2 tiene razón en que el trabajador vive durante un lote, no durante toda la sesión. Cada pulsación de Convertir paga entre 1,2 y 1,8 s de arranque, y en Windows con antivirus probablemente más. Junto con la importación innecesaria de librerías de conversión en la ventana (que B2 y yo encontramos por separado) y con el ejecutable que se desempaqueta en cada apertura, el usuario espera en sitios donde no hace falta. La descarga de 177 MB para instalar 38 MB la confirmamos dos auditores con los mismos datos. Mantener tres ventanas sigue siendo el costo de fondo que frena estos arreglos. Nada rompe el producto en lotes pequeños, pero con carpetas grandes una persona no técnica creerá que la aplicación se colgó.

**Fortalezas que vio:**

- La conversión corre en un proceso trabajador aparte (backend/services/worker/supervisor.py, WorkerRunner). Ninguna ventana se bloquea mientras convierte, y dentro de un mismo lote no se paga un arranque por cada archivo. Ojo: el arranque sí se paga en cada lote (ver F2-09).
- El progreso se actualiza una vez por segundo (presenter/intents/conversion.py:19, TICK_MILLISECONDS = 1000). En flet solo se redibuja la tarjeta de progreso (flet/window/window.py:115, page.narrow), y el conteo del escaneo se muestra a lo sumo cada 100 ms (presenter/intents/analysis.py:17).
- La lista Qt escala bien: 100 filas en 3 ms, 1.000 en 15 ms y 5.000 en 80 ms (medido en el contenedor, offscreen). Sus iconos están en caché (pyside/visuals/images.py:14). Es la referencia a imitar.
- En ttk, el icono de formato se lee una sola vez gracias a @cache (ttk/visuals/marks.py:15). Ya existe la mitad del patrón de caché que falta en las casillas y los números.
- Ya se trabajó el peso del ejecutable: se quitaron magika, onnxruntime, numpy y pandas, y babel quedó con dos idiomas, lo que lo bajó de 90 a 40 MB (ADR-0032). Una comprobación en CI impide que vuelva a crecer.
- El instalador marca por defecto la opción más liviana (clearmd.iss:134-153, ttkonly), y la ventana flet no descarga nada al arrancar (ADR-0042), lo que cumple la promesa de funcionar 100 % local.
- El arranque de las ventanas es razonable (ttk unos 2,1 a 2,4 s, Qt unos 1,9 a 2,5 s en el contenedor), y la pantalla de carga con porcentaje da sensación de avance.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F2-01 | 🔴 Alta | pequeño | alta | La ventana clásica (ttk) se congela varios segundos con listas de cientos o miles de archivos |
| F2-02 | 🟠 Media | medio | media | La lista de flet también rehace todas sus filas en cada cambio y no está virtualizada |
| F2-03 | 🟠 Media | pequeño | alta | El instalador pesa 177 MB para instalar por defecto un programa de unos 38 MB |
| F2-09 | 🟠 Media | medio | alta | Cada pulsación de Convertir, Dividir o Unir paga otra vez el arranque del trabajador |
| F2-04 | 🟠 Media | pequeño | media | La ventana clásica instalada se desempaqueta de nuevo cada vez que se abre |
| F2-06 | 🟠 Media | grande | media | Tres ventanas triplican el costo de cada función sin beneficio claro para el usuario no técnico |
| F2-05 | ⚪ Baja | pequeño | alta | La ventana carga librerías de conversión que solo usa el proceso trabajador |
| F2-07 | ⚪ Baja | pequeño | media | Cambios pequeños redibujan la lista entera: subir o bajar en Unir y cambiar el tema |
| F2-08 | ⚪ Baja | medio | alta | No hay métricas automáticas de rendimiento de las ventanas: arranque, listas grandes y descarga |

<details><summary>Detalle técnico y evidencia</summary>

- **F2-01 — La ventana clásica (ttk) se congela varios segundos con listas de cientos o miles de archivos**
  - *Impacto:* Quien elige una carpeta con 1.000 documentos espera unos 3 segundos con la ventana congelada en Revisar, y con 3.000 casi 10, sin poder moverla ni cerrarla. En Elegir pasa lo mismo cada vez que agrega un archivo, porque toda la lista se vuelve a dibujar. Una persona no técnica pensará que el programa se colgó. Es la ventana que el instalador pone por defecto y la que recomienda el README.
  - *Evidencia:* Medido con Xvfb en ClearMD_dev (/tmp/audit-efficiency/ttklist.py, FileList(checks=True)): n=100, show 418 ms; n=1000, 3071 ms; n=3000, 9562 ms; seleccionar todo, 1046 ms. Causa, revisada en la ronda 2: ttk/components/file_list.py:100-131 show() borra todas las filas y, por cada fila, llama dos veces a marks.numbered() (estados off y on) y a self._box(state), que llama a marks.checkbox() y lo dibuja con supermuestreo y resize LANCZOS (marks.py, alrededor de la línea 33) SIN caché, y además crea dos ImageTk.PhotoImage. CORRECCIÓN respecto a la ronda 1: marks.icon() sí está en caché (@cache, marks.py:15), así que el PNG no se relee. _sync_boxes (file_list.py:146-155) recorre todas las filas con tree.item() en cada selección.
  - *Recomendación:* Guardar en caché la casilla por estado y paleta (son solo 3 × 2 imágenes) y el número compuesto por cifra, ancho y estado, o poner el número en una columna de texto. En la selección, actualizar solo las filas que cambiaron. Agregar una prueba de presupuesto: 1.000 filas en menos de 300 ms en ttk, flet y Qt.
- **F2-02 — La lista de flet también rehace todas sus filas en cada cambio y no está virtualizada**
  - *Impacto:* Con carpetas grandes, la ventana flet tarda en mostrar Revisar o en agregar archivos: alrededor de un cuarto de segundo con 1.000 archivos y más de un segundo con 5.000, solo del lado de Python. Después hay que enviar todos esos controles al programa de ventana, un costo que no pude medir. El usuario lo percibe como una ventana que se traba.
  - *Evidencia:* /tmp/audit-efficiency/lists.py, FileList de flet con checks=True: n=100, 21 ms; n=1000, 235 ms; n=5000, 1258 ms (solo la construcción en Python, sin page.update). flet/components/file_list.py:66 usa ft.ListView(controls=...) sin item_extent; show_rows (103-107) crea unos 8 controles por fila, cada uno con tooltip (162). Las actualizaciones que no se acotan con narrow terminan en page.update() de toda la página (flet/window/flet_page.py:56-65).
  - *Recomendación:* Fijar la altura de fila (item_extent o prototype_item), reutilizar las filas que no cambian y acotar con narrow las actualizaciones de las listas, como ya se hace con el progreso. Medir page.update con 1.000 filas en Windows con flet-bench.
- **F2-03 — El instalador pesa 177 MB para instalar por defecto un programa de unos 38 MB**
  - *Impacto:* El README recomienda descargar ClearMD-Setup, que pesa casi 180 MB: cerca de cinco veces lo que se instala con la opción por defecto. Con conexiones lentas o con datos móviles, la descarga tarda varios minutos y gasta datos, y un archivo tan pesado genera desconfianza. En Linux el paquete pesa 235 MB porque trae las tres ventanas. B2-07 llegó a lo mismo por su cuenta.
  - *Evidencia:* gh release view v2.8.1: Setup 176728655 B; ClearMD-v2.8.1-windows.exe 37926305 B; Qt zip 60 MB; Flet zip 80 MB; linux.tar.gz 235042896 B. clearmd.iss:134-153: el tipo por defecto es ttkonly, pero en [Files] (172-182) entran ttk, Qt, flet y CLI, cada uno con su propio Python y su backend. packaging/package.sh:37-42 junta todo en un solo tar. README.md:24.
  - *Recomendación:* Publicar un instalador liviano (ventana principal y CLI) como descarga recomendada y dejar el completo como opción avanzada. Separar el tar de Linux por ventana. Subir esto por encima de lo que plantea el roadmap (spec/roadmap.md:86 solo lo trata como métrica) y poner un límite de tamaño por archivo publicado.
- **F2-09 — Cada pulsación de Convertir, Dividir o Unir paga otra vez el arranque del trabajador**
  - *Impacto:* En los lotes pequeños, que son los habituales, la persona espera entre 1,2 y 1,8 s fijos antes de que empiece el primer archivo, y en Windows con antivirus probablemente más. Si hay archivos sin extensión, ese arranque se paga dos veces (al revisar y al convertir). Desde la ventana, eso se ve como si "tardara en arrancar" cada vez. El hallazgo es de B2-05; lo incorporo porque lo nota quien usa la ventana.
  - *Evidencia:* backend/api/__init__.py: plan_batch (alrededor de :103) y run_batch (alrededor de :146) crean cada uno su WorkerRunner y lo cierran en su finally (lo comprobé: `finally: worker.close()`). B2 midió de 1,8 a 3,4 s hasta Ready en ClearMD_dev, y ADR-0050 midió 1,2 s. Esto corrige mi fortaleza de la ronda 1, que llamaba "persistente" al trabajador.
  - *Recomendación:* En las ventanas, arrancar el trabajador en segundo plano cuando la ventana ya está a la vista, compartirlo entre Revisar y Convertir, y cerrarlo tras unos minutos sin uso. La CLI puede seguir como está.
- **F2-04 — La ventana clásica instalada se desempaqueta de nuevo cada vez que se abre**
  - *Impacto:* Aunque ClearMD esté instalado, el ejecutable de un solo archivo copia unos 38 MB a una carpeta temporal en cada apertura, antes de mostrar la ventana. En Windows, con el antivirus revisando esa copia, son segundos de espera en cada arranque que una aplicación instalada no necesita.
  - *Evidencia:* clearmd.iss:172 instala dist\ClearMD.exe, que es el EXE onefile de clearmd.spec:84-108, con un Splash que tapa la espera. ADR-0028:30 aceptó ese costo para el exe descargado. Qt y flet ya usan onedir (COLLECT en clearmd_pyside.spec:106 y clearmd_flet.spec:98). No lo medí en Windows real.
  - *Recomendación:* Para el instalador, construir la ventana clásica en modo carpeta (onedir), igual que Qt y flet, y dejar el exe de un solo archivo solo para quien lo descarga suelto. Medir en Windows el arranque en frío de las dos variantes.
- **F2-06 — Tres ventanas triplican el costo de cada función sin beneficio claro para el usuario no técnico**
  - *Impacto:* El usuario ve tres accesos directos (ClearMD, ClearMD (Qt) y ClearMD (flet)) y un instalador que le pide elegir entre ttk, Qt, flet y Flutter (B4-09) sin forma de saber cuál le conviene. El autor paga cada función tres veces, y esa carga retrasa arreglos que sí se notan, como F2-01. Las diferencias entre ventanas producen errores que solo aparecen en una de ellas, como F1-09 y F3-02.
  - *Evidencia:* Líneas de código: ttk 4711, pyside 3616, flet 3632, frente a 1836 del presenter compartido. Archivos de prueba por ventana: 49, 28 y 32. La feature 033 necesitó una corrección solo para flet (e9299b4). El CI de main tarda unos 24 min. Listas con 1.000 filas: Qt 15 ms, flet 235 ms, ttk 3071 ms. Accesos directos: clearmd.iss:188-190.
  - *Recomendación:* Elegir con datos una ventana principal (arranque, fluidez de las listas, tamaño de descarga) y declarar las otras como alternativas congeladas, en un ADR. Hoy Qt es la que mejor escala. Al menos, no mostrar al público general tres accesos directos ni nombres de tecnología.
- **F2-05 — La ventana carga librerías de conversión que solo usa el proceso trabajador**
  - *Impacto:* Cerca de medio segundo del arranque de cada ventana, y más de 1 s de `clearmd --version`, se va en cargar código de Excel, PDF y del informe PDF que la ventana nunca usa. B2-06 llegó a la misma cadena de importaciones por otro camino.
  - *Evidencia:* python -X importtime -c 'import clearmd.frontend.presenter': de 0,71 s acumulados, 0,51 s vienen de backend.api.composition → worker.page_runner/supervisor → child → pages → split.xlsx_cut → openpyxl (0,26 s); summary.pdf_report 0,11 s; pypdfium2 0,075 s; 631 módulos cargados. B2 midió `clearmd --version` en unos 1,13 s.
  - *Recomendación:* Que el supervisor no importe el módulo del hijo (pasar el destino por nombre) e importar openpyxl, pypdfium2 y pdf_report dentro de las funciones que los usan. Agregar una prueba que falle si importar el presenter carga esas librerías.
- **F2-07 — Cambios pequeños redibujan la lista entera: subir o bajar en Unir y cambiar el tema**
  - *Impacto:* En Unir, cada clic en subir o bajar redibuja toda la lista. En ttk son unos 0,4 s con 100 documentos, así que ordenarlos se siente pesado. Cambiar entre tema claro y oscuro también vuelve a dibujar todas las filas.
  - *Evidencia:* ttk/views/choose.py:117 y 130 llaman a order.show(rows) completo en cada movimiento. ttk/components/file_list.py:79-96 apply_palette llama a show(). Con 100 filas, show tarda 418 ms (F2-01). flet/components/file_list.py:103-107 también reconstruye todo. El tiempo exacto por clic está estimado a partir de esa medición.
  - *Recomendación:* Mover solo las dos filas implicadas y recolorear con las imágenes ya guardadas en caché. Se resuelve casi solo junto con F2-01.
- **F2-08 — No hay métricas automáticas de rendimiento de las ventanas: arranque, listas grandes y descarga**
  - *Impacto:* F2-01, F2-03 y F2-09 llegaron a la 2.8.1 sin que nada los detectara. Sin una medición continua, cada función nueva puede volver la aplicación más lenta o más pesada sin que el autor lo note antes que el usuario.
  - *Evidencia:* docs/benchmarks/ solo mide conversores (001-004), y B2-08 confirma que tampoco cubre el lector PDFium. flet-bench.yml se lanza a mano y sus tres últimas ejecuciones fallaron (gh run list, 2026-11-06). No hay pruebas con 1.000 filas en tests/gui. La lección II.6 de docs/lessons-learned.md:124-128 ya pedía medir en el sistema del usuario.
  - *Recomendación:* Agregar al CI pruebas de presupuesto con límite: arranque hasta dibujar cada ventana, mostrar 1.000 filas, tamaño de cada archivo publicado y lista de módulos prohibidos al importar el presenter. Reparar flet-bench y correrlo antes de cada versión.

</details>

### Frontend · Estilo visual UI/UX — 7/10

Después del debate mantengo la nota: la identidad visual es coherente y está bien medida en las tres ventanas (riel de pasos, una sola acción principal por pantalla, medidas compartidas en design/). Los problemas siguen en el mismo lugar: donde la persona tiene que leer una explicación, la interfaz se la corta o la esconde. En Revisar, el motivo y la acción se truncan, y en ttk no hay forma de leerlos. La lista de Revisar en ttk esconde filas y no muestra barra. En Resultados, un fallo y una omisión se ven del mismo color. Ajustes no cabe en un portátil. Los colores derivados bajan de 4,5:1, aunque el ADR-0027 dice que todo pasa AA. Los colegas me hicieron ver dos cosas de mi lente que había infravalorado. La primera: Resultados no muestra en ningún lugar visible la ruta donde quedaron los archivos (F4-03). La segunda: la lista de ttk, además de verse mal, se congela con listas grandes (F2-01), y el arreglo es el mismo, imágenes en caché. Las agrego o las fusiono. Retiro mi sugerencia de reconsiderar el Title Case en español: es una doctrina explícita del dueño (ADR-0041:25), así que lo correcto es aplicarla de forma coherente y no discutirla. La Ayuda desactualizada queda como un hallazgo compartido de cuatro auditores. La dejo, pero en la mesa de textos le corresponde a F4. Casi todo se arregla con poco esfuerzo.

**Fortalezas que vio:**

- Identidad única y reconocible en las tres ventanas: riel oscuro con el logo C·M↓, cuatro pasos siempre visibles y numerados, y el mismo encabezado con contador, título y frase (docs/screenshots/007, 016 y 018, pantalla 1-choose).
- El contador de paso con estado («PASO 2 DE 4 · ESPERANDO TU DECISIÓN», «TERMINADO CON PROBLEMAS») cumple con elegancia la regla de un estado visible siempre (ux.md §1).
- Los colores base cumplen AA con holgura en ambos temas: texto sobre tarjeta 15,2:1 y 12,0:1, secundario 5,85 y 6,37, botón principal 5,47 y 9,19. El modo oscuro tiene acentos propios; no es una simple inversión.
- Una sola acción principal por pantalla, abajo a la derecha, y las secundarias se ven claramente como secundarias.
- Las tarjetas de cifras dan el resultado de un vistazo y solo llevan color cuando la cifra no es cero.
- Resultados muestra la explicación completa de la fila seleccionada debajo de la lista. Es el patrón correcto y hay que llevarlo a Revisar.
- Iconos de formato propios y legibles, iguales en las tres ventanas.
- Las medidas están centralizadas en design/metrics.py y typography.py: rejilla de 8 px, botones de 44 px y texto nunca menor de 14 px. Por eso las ventanas son consistentes.
- El diálogo «¿Qué Sigue?», con tres mosaicos y una casilla, es claro y amable.
- La lista de Qt escala bien con miles de filas (F2 midió 15 ms con 1.000), así que el diseño de la lista no está mal en sí.

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F3-01 | 🔴 Alta | pequeño | alta | En Revisar, el motivo de cada archivo omitido aparece cortado y no hay dónde leerlo completo |
| F3-02 | 🔴 Alta | pequeño | media | La lista de ttk esconde archivos, no muestra barra y se congela con listas grandes |
| F3-11 | 🔴 Alta | pequeño | alta | Resultados no muestra dónde quedaron los archivos |
| F3-03 | 🟠 Media | pequeño | alta | Un archivo fallido se ve igual que uno omitido, y la diferencia depende solo del color |
| F3-08 | 🟠 Media | pequeño | alta | Varios colores derivados bajan de 4,5:1, aunque el ADR-0027 asegura que todo pasa AA |
| F3-04 | 🟠 Media | medio | media | Ajustes no cabe en un portátil (Qt) y no avisa de que hay más opciones (flet) |
| F3-05 | 🟠 Media | pequeño | alta | Errores de texto visibles: «1 Fallidos», motivos en minúscula y Title Case aplicado de forma desigual |
| F3-07 | 🟠 Media | medio | alta | Con el tamaño mínimo de ventana las listas casi desaparecen y las opciones se cortan |
| F3-10 | 🟠 Media | medio | alta | Un paso Convertir casi vacío que repite la confirmación y no dice lo que va a pasar |
| F3-09 | ⚪ Baja | pequeño | alta | Las rutas de carpeta se cortan por el final y esconden justo el nombre que importa |

<details><summary>Detalle técnico y evidencia</summary>

- **F3-01 — En Revisar, el motivo de cada archivo omitido aparece cortado y no hay dónde leerlo completo**
  - *Impacto:* Justo antes de confirmar, la persona ve «ya es Markdown. No nec…» o «archivo ZIP. Descompríme…». Lo que se corta es precisamente lo que tiene que hacer. En ttk el texto se corta sin puntos suspensivos y no se puede leer de ninguna forma. En Qt y flet solo aparece al pasar el ratón por encima, algo que una persona no técnica no sabe que puede hacer. En Resultados la línea de detalle existe, pero solo para la fila seleccionada.
  - *Evidencia:* docs/screenshots/018/2-review-light-es.png, 016/2-review-dark-es.png («archivo ZIP. Descomprímelo y co…»), 007/2-review-light-es.png (corte duro «No necesita conv»), 018/4-results-light-es.png («Quítale la contr…»). El texto completo solo existe como tooltip: flet/components/file_list.py:161-162 y pyside/components/file_list.py:115. ttk no tiene tooltips. ttk/views/review.py:45 checks=False, sin línea de detalle (en Resultados sí la hay: ttk/views/results.py:48). Contradice ux.md §3-§4 («Nothing is reachable only by hover»). F4-04 llega a lo mismo por otro camino.
  - *Recomendación:* En Revisar, usar el patrón de Resultados: una línea de detalle de varias líneas debajo de la lista, con la primera fila con problema seleccionada por defecto. Así la persona ve la explicación sin tener que hacer nada. Como alternativa, dejar que la columna «Qué Pasará» ocupe dos líneas. Ampliar la regla del contrato: «nada solo por hover» también prohíbe el texto truncado sin otra forma de leerlo.
- **F3-02 — La lista de ttk esconde archivos, no muestra barra y se congela con listas grandes**
  - *Impacto:* En la ventana clásica, que es la que se instala por defecto, la lista de Revisar muestra 4 filas de 9 y ninguna barra lateral: la persona cree que solo se convertirán esos cuatro. Con carpetas grandes, la misma lista congela la ventana unos 3 segundos con 1.000 archivos y casi 10 con 3.000, y vuelve a pasar con cada archivo agregado, cada movimiento en Unir y cada cambio de tema. Parece que el programa se colgó.
  - *Evidencia:* docs/screenshots/007/2-review-light-es.png: las tarjetas suman 6+2+1 = 9, pero se ven 4 filas y no hay barra. En 007/1-choose-light-es.png la barra sí aparece. Causa probable: ttk/components/file_list.py:58-64 empaqueta el Treeview primero con expand=True y anchos fijos, y el Scrollbar después, así que la barra se queda sin espacio. review.py:44 fija height=4. Rendimiento (medido por F2-01, que yo no repetí): show() rehace todas las filas y crea por cada una iconos y casillas con PIL sin caché (ttk/visuals/marks.py:15-83).
  - *Recomendación:* Empaquetar la barra antes que la lista (side='right') o usar grid, y ajustar los anchos al espacio real. Guardar en caché cada imagen distinta (icono por tipo, casilla por estado y paleta, número como texto en una columna) y actualizar solo las filas que cambian. Agregar una prueba de GUI con 9 filas a 800×624 que exija la barra visible, y otra de presupuesto con 1.000 filas.
- **F3-11 — Resultados no muestra dónde quedaron los archivos**
  - *Impacto:* La primera pregunta al terminar es «¿dónde están mis archivos?». La pantalla de Resultados solo ofrece un botón. Si ese botón está apagado (cuando se conservaron los resultados que ya existían, como mostró F1-03) o la persona prefiere no abrir el explorador, no tiene ninguna ruta visible. El texto de «todo bien» nombra ClearMD_Output, pero no la subcarpeta real (OutputMD, OutputSep, OutputUnif).
  - *Evidencia:* Hallazgo de F4-03, verificado: presenter/screens/results.py:43-60 arma titular, conteos, filas, carpetas y oferta. Las carpetas (result_folders) solo alimentan el botón y no hay ninguna línea de texto con la ruta. 018/4-results-light-es.png y 016/4-results-light-es.png no muestran ninguna ruta. es.toml:367 all_good «…en la carpeta ClearMD_Output.».
  - *Recomendación:* Agregar en Resultados, siempre, una línea visible y seleccionable con la ruta exacta («Tus archivos están en: …\ClearMD_Output\OutputMD»), cortada por el medio si es larga (ver F3-09). Renombrar las subcarpetas es otra decisión, la de F4-03, y conviene tratarla en un ADR aparte.
- **F3-03 — Un archivo fallido se ve igual que uno omitido, y la diferencia depende solo del color**
  - *Impacto:* En Resultados, un archivo protegido con contraseña (que falló) aparece en el mismo naranja que uno «ya es Markdown» (que solo se omitió). La persona no distingue lo que debe arreglar de lo que puede ignorar. Además, el archivo que ella misma decidió conservar también va como omitido y entre «lo que necesita tu atención». Al seleccionar una fila naranja en tema claro, el contraste baja del mínimo.
  - *Evidencia:* 016/4-results-dark-es.png: filas de fallo y de omisión con el mismo color. Las filas solo tienen un indicador binario de advertencia (pyside/components/file_list.py:31 'warning: bool'; ttk tag 'warning'). results.py:45 y :53 suman KEPT a omitidos (len(report.skipped) + count[KEPT]), lo que confirma F4-06. Contraste: warning sobre fila seleccionada da 3,89:1 (Qt/flet en claro) y 4,14:1 (selección de ttk).
  - *Recomendación:* Dar a cada fila un tono propio (omitido = advertencia, fallido = peligro) y un indicador que no dependa del color: una palabra al inicio («Falló:», «Omitido:», «Conservado:») o un icono. Contar los conservados por decisión de la persona aparte y fuera de la sección de atención. En una fila seleccionada, usar el color de texto normal.
- **F3-08 — Varios colores derivados bajan de 4,5:1, aunque el ADR-0027 asegura que todo pasa AA**
  - *Impacto:* Al público objetivo le cuesta leer el texto atenuado (la tarjeta «0 Fallidos», «Listos para convertir» antes de tiempo), el texto secundario en una fila seleccionada y los botones deshabilitados. Eso incluye a personas mayores o con baja visión. Los bordes de los campos apenas se distinguen de la tarjeta.
  - *Evidencia:* Calculado con la fórmula WCAG sobre palette.py y colors.blend. Texto atenuado sobre tarjeta atenuada: 3,64:1 en claro (ttk/visuals/styles.py:35 comenta '3:1, review of 014'). Muted sobre fila seleccionada: 4,36:1 en oscuro. Deshabilitado sobre tarjeta: 2,13 y 2,69. Bordes de controles: 1,31 y 1,26 (WCAG 1.4.11 pide 3:1). Accent sobre shape: 4,51 y warning sobre ground: 4,59, apenas por encima. docs/decisions/0027-visual-identity.md: «Every text pair passes WCAG AA (measured: 5.0:1 the lowest)».
  - *Recomendación:* Subir DIM_TEXT hasta 4,5:1, o atenuar con peso o tamaño en lugar de color. Usar bordes de campo de al menos 3:1. Agregar una prueba de contraste que recorra todos los pares que pintan texto, incluidas las mezclas, en los dos temas. Corregir la frase del ADR-0027.
- **F3-04 — Ajustes no cabe en un portátil (Qt) y no avisa de que hay más opciones (flet)**
  - *Impacto:* En Qt, Ajustes mide 884 px de alto y no tiene desplazamiento: en un portátil de 1366×768, Guardar y Cancelar pueden quedar fuera de la pantalla. En flet la lista se corta a mitad de frase y no hay barra, así que la persona no sabe que abajo están Dividir, Unir y Bienvenida. En ttk la barra es una franja turquesa que llama más la atención que el contenido.
  - *Evidencia:* docs/screenshots/016/6-settings-light-es.png mide 720×884 (PIL). pyside/views/dialogs/settings.py no usa QScrollArea ni scroll_page. 018/6-settings-light-es.png se corta en «Imágenes» sin indicador. 007/6-settings-dark-es.png muestra una barra accent de unos 6 px. Las casillas se alinean distinto en cada ventana. Además, hay dos botones «Guardar» con significados distintos (F4-09: es.toml split_keep y save).
  - *Recomendación:* Fijar una altura máxima de unos 640 px, con contenido desplazable y botones fijos siempre visibles. Usar una barra discreta (color border o muted). Agrupar los ajustes por secciones. Alinear las casillas en la misma columna. Renombrar la opción de las partes a «Qué conservar» para que no compita con el botón Guardar.
- **F3-05 — Errores de texto visibles: «1 Fallidos», motivos en minúscula y Title Case aplicado de forma desigual**
  - *Impacto:* «1 Fallidos», «1 Omitidos» o «1 Ya Existen» parecen un error del programa y restan confianza. En una misma lista, unos motivos empiezan en minúscula y otros en mayúscula. La regla de mayúsculas del dueño se aplica a medias: en un mismo grupo hay opciones con estilos distintos y hay un encabezado que es una frase incompleta («Los Resultados Van»).
  - *Evidencia:* 016/2-review-dark-es.png («1 Ya Existen»), 016/4-results-dark-es.png («1 Fallidos»). Las tarjetas usan etiquetas fijas (es.toml:336 y :362-363 'Omitidos'/'Fallidos') aunque existen las claves count.*.one/.other. Motivos: es.toml:57-58. es.toml:503 output_title = «Los Resultados Van», cuando ya existe :512 pick_output_title = «¿Dónde Van los Resultados?». La regla está en ADR-0041:25 («Title Case (the owner's rule for every title)») y en la memoria del proyecto. Mezcla de estilos señalada por F4-10 (gui.split.keep_*, gui.merge.*).
  - *Recomendación:* Usar singular o plural según la cifra. Poner mayúscula inicial en los motivos que abren una celda. Reutilizar «¿Dónde Van los Resultados?» como encabezado. Aplicar el Title Case de forma uniforme según el tipo de clave (títulos y botones frente a opciones y explicaciones), con un linter del catálogo. Retiro mi recomendación anterior de reconsiderar el Title Case en español: es doctrina del dueño.
- **F3-07 — Con el tamaño mínimo de ventana las listas casi desaparecen y las opciones se cortan**
  - *Impacto:* La lista de archivos es el centro del paso 1, pero muestra de 2 a 4 filas, y a 800×624 solo dos. En Dividir, la tarjeta de opciones se corta a mitad de frase y una barra de página se superpone al contenido.
  - *Evidencia:* 016/1-choose-split-800-light-es.png («Nada de lo que hay dentro cambia» cortado, barra superpuesta); 018/1-choose-compact-dark-es.png (2 filas y media); 007/1-choose-light-es.png. Mínimos en design/metrics.py:17-18 (800×624).
  - *Recomendación:* Dar prioridad de altura a la lista y plegar la tarjeta de opciones en un resumen de una línea con «Cambiar…» cuando falte espacio. Fijar en el contrato un mínimo de 5 filas visibles y comprobarlo en las capturas a 800×624.
- **F3-10 — Un paso Convertir casi vacío que repite la confirmación y no dice lo que va a pasar**
  - *Impacto:* Tras Revisar y «Siguiente», la persona llega a una pantalla con el 70 % vacío y una sola línea («Listos para convertir: 6»), y tiene que confirmar otra vez. Esa línea, además, cuenta archivos que no se van a escribir si eligió conservar los existentes (F1-03), y no recuerda si eligió reemplazar (F1-08). La bienvenida habla de tres pasos y la ventana tiene cuatro (F4-08).
  - *Evidencia:* 016/3-convert-ready-light-es.png (una tarjeta de unos 100 px y el resto vacío); 018/3-convert-ready-light-es.png; F1-03 lo reprodujo con el presentador real ('Ready to convert: 2' con dos EXISTS conservados). chrome/secondary.py:40-44 solo muestra la cifra.
  - *Recomendación:* Aprovechar el espacio en vez de quitar el paso, que es un cambio mayor del recorrido. Mostrar el destino, la cifra real («4 nuevos · 2 ya existen y se conservan»), la decisión tomada y el tiempo estimado. Si todo se conserva, cambiar la acción principal por «Abrir resultados existentes». Unificar «tres pasos» o «cuatro pasos» en la Bienvenida.
- **F3-09 — Las rutas de carpeta se cortan por el final y esconden justo el nombre que importa**
  - *Impacto:* La columna Carpeta muestra «C:\Users\RUNNER~1\AppData\L…»: la parte que identifica la carpeta se pierde, mientras el comienzo, que se repite en cada fila, ocupa casi la mitad de la tabla y le quita espacio a la explicación (F3-01).
  - *Evidencia:* 018/1-choose-light-es.png, 018/2-review-light-es.png, 016/2-review-dark-es.png ('/tmp/Usuarios/ana/Docume…'). flet/components/file_list.py:161 TextOverflow.ELLIPSIS (corta por el final).
  - *Recomendación:* Mostrar solo la última carpeta, o cortar por el medio, y llevar la ruta completa a la línea de detalle. Dar a Carpeta menos ancho que a Nombre y a la explicación.

</details>

### Frontend · Claridad es cariño — 6,5/10

Después de leer a los ocho auditores, mantengo el diagnóstico y lo afino. ClearMD trata bien a la persona en el camino feliz: revisa antes de escribir nada, recuerda la privacidad y casi todos los errores dicen qué hacer. La confianza se rompe en los momentos de duda. Cuatro auditores (F1, F3, B4 y yo) encontramos por separado que la Ayuda describe un flujo viejo y no menciona Dividir ni Unir. Es el hallazgo más confirmado de toda la auditoría y el más barato de arreglar. Tres auditores encontramos que el texto que dice qué hacer con un archivo se corta en la tabla. Varios encontramos que la ventana muestra opciones de terminal y nombres de excepciones, y que el «repórtalo» no dice dónde. Los otros auditores me hicieron ver otro patrón: la interfaz da por problema lo que no lo es (resultados conservados, encabezados quitados, «parte 1 de 1»), y se queda callada cuando de verdad hay un problema (Unir con un solo archivo, Unir con un archivo dañado, el «¿el disco está lleno?» falso). Para una persona no técnica eso es lo más dañino: aprende a no creer en los avisos. Casi todo se arregla cambiando textos y con pruebas sencillas del catálogo.

**Fortalezas que vio:**

- Revisar es obligatorio antes de escribir nada («Nada se escribe hasta que confirmes») y se puede cancelar en cualquier momento: la persona siente que tiene el control.
- La privacidad se recuerda sin alarmismo en el inicio, en el riel y en la Ayuda («100 % local · nada sale de tu equipo»), y la promesa es la misma en README y SECURITY.
- El catálogo de errores casi siempre dice qué pasó y qué hacer, en palabras humanas (contraseña, archivo dañado, archivo abierto en Excel, disco lleno) y con el límite y el valor medido.
- Español natural y cercano, con tuteo coherente, y una prueba que obliga a que inglés y español tengan las mismas claves y los mismos marcadores.
- La pantalla de inicio con tres tarjetas del mismo rango (Convertir, Dividir, Unir) y el diálogo «¿Qué Sigue?» son claros y amables.
- Cada ajuste tiene debajo una línea de explicación, y las opciones se leen como frases («Reemplazarlo si el original cambió»).
- El botón principal desactivado siempre explica por qué. Nunca hay un botón muerto sin explicación (lo confirmó F1).
- Resultados ya muestra debajo de la lista la explicación completa de la fila seleccionada. Ese patrón hay que llevarlo a Revisar, no reemplazarlo.
- La pista de Dividir explica en lenguaje llano por qué existe la opción por palabras (una IA lee una cantidad limitada de texto).

**Sus hallazgos:**

| Código | Gravedad | Esfuerzo | Confianza | Hallazgo |
| --- | --- | --- | --- | --- |
| F4-02 | 🔴 Alta | pequeño | alta | La Ayuda describe un flujo que ya no existe y no menciona Dividir ni Unir |
| F4-04 | 🔴 Alta | pequeño | alta | En Revisar y Resultados, la explicación se corta justo en la parte que dice qué hacer |
| F4-03 | 🔴 Alta | pequeño | alta | Resultados no dice dónde quedaron los archivos, y las subcarpetas tienen nombres crípticos |
| F4-01 | 🔴 Alta | pequeño | alta | Nunca se explica qué es Markdown ni para qué sirve |
| F4-06 | 🟠 Media | pequeño | alta | La ventana trata como problema lo que no lo es, y los conteos no cuadran entre pantallas |
| F4-11 | 🟠 Media | pequeño | alta | Unir falla tarde y en silencio: con un solo documento, o con uno dañado, la persona no sabe qué pasó |
| F4-05 | 🟠 Media | pequeño | alta | El error inesperado muestra el nombre técnico, y «repórtalo» no dice dónde |
| F4-07 | 🟠 Media | medio | alta | La ventana muestra opciones de terminal, nombres internos y palabras que asustan |
| F4-08 | 🟠 Media | medio | alta | «Tres pasos» en la bienvenida, cuatro en la ventana, y un paso 3 casi vacío que repite la confirmación |
| F4-09 | ⚪ Baja | pequeño | alta | Textos viejos, ambiguos o con mayúsculas poco naturales |

<details><summary>Detalle técnico y evidencia</summary>

- **F4-02 — La Ayuda describe un flujo que ya no existe y no menciona Dividir ni Unir**
  - *Impacto:* Quien abre la Ayuda porque está perdido recibe instrucciones equivocadas. Le dice «Pulsa Convertir y revisa» y «Confirma», pero en Elegir el botón se llama «Siguiente», no hay ningún botón «Confirmar» y existe un paso 3 aparte. No menciona la pantalla de inicio ni las herramientas Dividir y Unir, y no dice dónde quedan las partes ni el archivo unido. Una Ayuda equivocada es peor que no tener Ayuda. Cuatro auditores lo encontramos por separado (F1-04, F3-06, B4-03 y este).
  - *Evidencia:* es.toml:422-423 gui.help.how_buttons / how: «2. Pulsa Convertir y revisa lo que va a pasar.\n3. Confirma: …». presenter/screens/primary.py:41-48 (páginas 1 y 2 = gui.nav.next «Siguiente»). No hay claves tool.split / tool.merge que reemplacen gui.help.*, aunque sí reemplazan otras páginas (es.toml:583, 626). ttk usa siempre «how» (suéltalos en la ventana) aunque falte tkdnd (F1-04). Captura docs/screenshots/018/5-help-light-es.png.
  - *Recomendación:* Reescribir la Ayuda con el flujo real (Inicio → herramienta → Elegir → Revisar → Convertir/Dividir/Unir → Resultados), con un párrafo corto por herramienta que diga qué recibe y dónde deja los resultados. Mostrar primero la sección de la herramienta activa. Elegir el texto con o sin arrastrar según si la ventana acepta arrastrar en ese momento. Agregar dos pruebas: que cada botón citado en la Ayuda exista en el catálogo, y que cada herramienta del Inicio aparezca en la Ayuda.
- **F4-04 — En Revisar y Resultados, la explicación se corta justo en la parte que dice qué hacer**
  - *Impacto:* Antes de confirmar, la persona lee «archivo ZIP. Descomprím…» o «Quítale la contr…»: justo lo que tiene que hacer es lo que desaparece. En ttk el texto se corta sin puntos suspensivos y no hay forma de leerlo completo. En Qt y flet solo se ve pasando el ratón por encima, algo que una persona no técnica no sabe que puede hacer. Mientras tanto, la columna Carpeta ocupa casi la mitad del ancho con rutas largas que además se cortan por el final, donde está el nombre que importa. Esto incumple la promesa central del producto: decir el motivo y qué hacer. F3-01 y F3-09 llegan a lo mismo.
  - *Evidencia:* Capturas 018/2-review-light-es.png (filas 1, 2 y 5 cortadas), 016/2-review-dark-es.png («archivo ZIP. Descomprímelo y co…»), 007/2-review-light-es.png (corte seco, sin «…») y 018/4-results-light-es.png («Quítale la contr…»). El texto completo solo existe como tooltip: flet/components/file_list.py:161-162 y pyside/components/file_list.py:115. ttk no tiene tooltips. ttk/views/review.py:45 no tiene línea de detalle. spec/contracts/ux.md §4: «Nothing is reachable only by hover».
  - *Recomendación:* Llevar a Revisar el patrón que ya funciona en Resultados: una línea de detalle debajo de la lista, de varias líneas, que muestre la explicación completa de la fila seleccionada (por defecto, la primera con problema). Mostrar en la columna Carpeta solo el nombre de la última carpeta y dejar la ruta completa en la línea de detalle. Ampliar la regla del contrato: el texto cortado cuenta como «solo por hover». Agregar una prueba que falle si un motivo queda cortado sin otra forma de leerlo.
- **F4-03 — Resultados no dice dónde quedaron los archivos, y las subcarpetas tienen nombres crípticos**
  - *Impacto:* La primera pregunta de la persona es «¿dónde están mis archivos?». Cuando hubo algún problema, Resultados no la responde: solo hay un botón, y ese botón se apaga si la tanda conservó lo que ya existía (F1-03). Al abrir la carpeta aparecen ClearMD_Output/OutputMD, OutputSep u OutputUnif, abreviaturas en inglés también para quien usa la app en español. Y el resumen se llama «Resumen_ClearMD» también en inglés. En Convertir, el mensaje de éxito ni siquiera nombra la subcarpeta, aunque Dividir y Unir sí lo hacen.
  - *Evidencia:* Capturas 018/4-results-light-es.png y 016/4-results-light-es.png: no aparece ninguna ruta. backend/schemas/formats.py:74-78 (OutputMD, OutputSep, OutputUnif, Resumen_ClearMD.md fijos en los dos idiomas). es.toml:367 gui.result.all_good dice «en la carpeta ClearMD_Output» sin OutputMD, mientras que es.toml:588 y 631 (Dividir y Unir) sí nombran OutputSep / OutputUnif: la inconsistencia está en el mismo catálogo.
  - *Recomendación:* Mostrar siempre en Resultados una línea con la ruta exacta y un botón para abrirla, haya habido problemas o no, y también cuando todo se conservó («Tus archivos están en: …\ClearMD_Output\OutputMD»). Como mínimo, igualar el texto de Convertir con los de Dividir y Unir. Los nombres traducidos y legibles (Convertidos/Divididos/Unidos) son una mejora mayor: requieren un ADR y un plan de migración para quien ya tiene carpetas antiguas, así que van después de la línea con la ruta, que es barata.
- **F4-01 — Nunca se explica qué es Markdown ni para qué sirve**
  - *Impacto:* La palabra central del producto («Convertir a Markdown», «Su Markdown», «Un Markdown», «Resumen: Markdown / Markdown + PDF / Solo PDF») no se explica en ninguna ventana, y tampoco se dice que el resultado sirve para dárselo a una IA. Una persona del público general no sabe qué va a recibir, con qué programa abrirlo ni por qué le conviene. Elige a ciegas.
  - *Evidencia:* es.toml [gui.home] convert = «Convertir a Markdown»; [gui.app] subtitle = «Documentos a Markdown, en tu computador»; [gui.help] no define Markdown ni habla de IA (en el catálogo, «IA» solo aparece en gui.split.hint). Capturas 018/0-home-light-es.png, 018/5-help-light-es.png y 018/1-choose-light-es.png.
  - *Recomendación:* Agregar una frase fija en el inicio, por ejemplo: «Markdown es texto simple, ordenado con títulos y listas, que las IA leen mejor. Se abre con el Bloc de notas». Agregar una sección «¿Qué es Markdown?» en la Ayuda. En el selector del resumen, nombrar las opciones por su uso («Para leer o imprimir (PDF)»).
- **F4-06 — La ventana trata como problema lo que no lo es, y los conteos no cuadran entre pantallas**
  - *Impacto:* La persona elige «Conservar» los resultados que ya existían. El paso 3 igual dice «Listo para convertir: 2» (F1-03). En Resultados esos archivos se suman a «Omitidos», aparecen en «Lo que Necesita Tu Atención» y el lote queda «Terminado con problemas», cuando ella decidió bien. En Revisar ve «2 Omitidos · 1 Ya Existen» y en Resultados «3 Omitidos». Los fallos se llaman «Fallidos» en la ventana y «Con error» en el resumen. Al mismo tiempo, casi todo PDF sale con «necesita tu atención» porque se quitaron los encabezados repetidos (B3-02), y una «parte 1 de 1» se anuncia como «se dividió» (B3-04). Con tantas alarmas falsas, la persona deja de creer en los avisos y pasa por alto los reales.
  - *Evidencia:* presenter/screens/results.py:44-45 y :53 suman OutcomeStatus.KEPT a los omitidos; la fila gui.result.kept entra en la lista de atención. chrome/secondary.py:43 y screens/review.py:42 cuentan len(plan.conversions) sin restar lo que se conserva (F1-03, reproducido con el presenter). es.toml gui.result.stat_failed = «Fallidos» frente a summary.failed = «Con error». B3-02: NoteKind.PDF_RUNNING_REMOVED pesa lo mismo que PDF_TEXT_UNREADABLE. Capturas 018/2-review-light-es.png frente a 018/4-results-light-es.png.
  - *Recomendación:* Usar las mismas categorías y las mismas palabras en Revisar, Convertir, Resultados y el resumen: Convertidos / Conservados / Omitidos / Con error. Calcular «Listo para convertir» según la decisión ya tomada. Lo que la persona eligió conservar y lo que ClearMD limpió no cuentan como problema ni tiñen el estado del lote. Fijar ese glosario en spec/contracts/ux.md, junto con una prueba que detecte sinónimos.
- **F4-11 — Unir falla tarde y en silencio: con un solo documento, o con uno dañado, la persona no sabe qué pasó**
  - *Impacto:* Con un solo archivo en Unir, la persona recorre los cuatro pasos y solo al final descubre que no había nada que unir (F1-02). Con un documento dañado y uno sano, no recibe resumen ni motivo, ve una carpeta de resultados que no existe y lee «¿el disco está lleno?» con el disco casi vacío (B4-01). Puede ponerse a borrar archivos para liberar espacio. El mensaje que sí explicaría el caso (nothing_to_merge) existe en el catálogo, pero no aparece.
  - *Evidencia:* F1-02: screens/primary.py:44-48 deja «Siguiente» activo con cualquier número de archivos; el límite solo está en merging.py:133. B4-01 (reproducido por B4): `clearmd roto.pdf b.pdf --merge pdf --lang es` → «⚠ No se pudo escribir el resumen … (¿el disco está lleno?)» y la carpeta no existe. Mismo supuesto en la GUI: es.toml gui.result.no_summary («Comprueba que el disco tiene espacio»), mostrado en presenter/screens/results.py:37-38.
  - *Recomendación:* En el paso 1 de Unir, desactivar «Siguiente» con menos de dos documentos y explicar por qué («Agrega al menos dos documentos para unirlos»). Si Revisar descarta documentos y queda uno, decirlo ahí. Cuando Unir no produce archivo, mostrar a cada documento su motivo. Cambiar no_summary para que no adivine la causa («No se pudo escribir el resumen en …: comprueba que la carpeta existe y que puedes escribir en ella»).
- **F4-05 — El error inesperado muestra el nombre técnico, y «repórtalo» no dice dónde**
  - *Impacto:* Si algo falla, la persona lee «Algo inesperado salió mal: KeyError: 'x'… Por favor repórtalo.»: jerga de programador y una petición que no puede cumplir porque no sabe dónde reportar. En el error genérico de conversión, la única acción es «Revisa el detalle técnico en el resumen», y ese detalle está en inglés técnico (B4-02). Además, si el fallo ocurre a mitad de una tanda, la vista de lo ya convertido desaparece (F1-07).
  - *Evidencia:* presenter/intents/reset.py:24-25 detail = f"{type(error).__name__}: {error}" → es.toml:441 gui.app.unexpected_error y es.toml:144. es.toml:15-17 error.conversion_failed action. spec/contracts/ux.md §3: «Never a traceback, an exception name or an error code alone». reset.py:23-32 pone report=None (F1-07).
  - *Recomendación:* Mostrar solo el mensaje tranquilizador, que ya existe. Llevar el detalle técnico a un botón «Copiar detalles para reportar», junto al enlace exacto de reporte (la página de issues). Rotular el detalle técnico del resumen como «Para quien te dé soporte». Darle a conversion_failed una acción útil por sí sola: abrirlo y guardarlo de nuevo, o dividirlo. Ante un error a mitad de la tanda, llevar a Resultados con lo que ya se escribió.
- **F4-07 — La ventana muestra opciones de terminal, nombres internos y palabras que asustan**
  - *Impacto:* En Revisar o Resultados, la persona puede leer «Conviértelo con --html full (la página completa de markitdown, sin la garantía de este modo)», «(CLI: --overwrite)», «posible bomba ZIP», «enlace simbólico» o «Divídelo cada N páginas», con la N literal. Son instrucciones que no puede seguir desde la ventana y palabras que la asustan. Al revés, la terminal le dice «Elige En N partes», el nombre de un botón que ahí no existe (B4-05).
  - *Evidencia:* es.toml [skip_action] too_much_memory_for_article y existing_output; [skip] archive_ratio y symlink; [error.nothing_to_measure] action. presenter/screens/results.py:33-34 y screens/review.py:24 muestran skip_action tal cual. B4-05 reprodujo la dirección contraria en la CLI. B3-05 y B4-06: «StarMath: `2`», «10 por KiB de fuente».
  - *Recomendación:* Separar los textos de acción para la ventana y para la terminal (por ejemplo skip_action.gui.* y skip_action.cli.*), igual que ya se hace con tool.split y tool.merge. En la ventana, nombrar el ajuste real («En Ajustes → Páginas Web, elige La página completa»). Reemplazar la N por el valor recomendado. Reescribir las palabras que asustan en lenguaje común. Agregar una prueba que prohíba «--», nombres de librerías y nombres de excepciones en los textos que llegan a la ventana.
- **F4-08 — «Tres pasos» en la bienvenida, cuatro en la ventana, y un paso 3 casi vacío que repite la confirmación**
  - *Impacto:* La bienvenida promete tres pasos, pero la ventana dice «Paso 1 de 4» y además tiene Inicio. El paso 3 es una pantalla casi en blanco que vuelve a decir «nada se escribe hasta que…»: un clic y una confirmación de más. Esa pantalla tampoco recuerda qué se eligió sobre los resultados existentes (F1-08), justo cuando «Reemplazar» va a sobrescribir archivos. En Revisar el botón dice «Siguiente» y no nombra la acción, así que no queda claro cuándo empieza el trabajo real.
  - *Evidencia:* es.toml gui.welcome intro «en tres pasos» frente a gui.steps.counter «Paso {step} de {total}» (4). Capturas 018/3-convert-ready-light-es.png y 016/3-convert-ready-light-es.png (una línea «Listos para convertir: 6» y el resto vacío, también señalado en F3-10). chrome/secondary.py:40-44 solo muestra la cantidad, no la decisión (F1-08).
  - *Recomendación:* Mientras no se decide el rediseño, usar el paso 3 para algo útil: destino, cuántos archivos se escriben y cuántos se conservan o reemplazan («2 ya existen: se reemplazarán»), y el tiempo estimado. Corregir la bienvenida para que cuente los mismos pasos que la ventana. Unir Revisar y Convertir en un solo botón («Convertir 6 archivos») es más limpio, pero toca las tres ventanas y las pruebas del recorrido: tiene que decidirse en un ADR.
- **F4-09 — Textos viejos, ambiguos o con mayúsculas poco naturales**
  - *Impacto:* «Mira los Resultados o Convierte más» remite a un botón que ya no existe (ahora es «¿Qué Sigue?»). En Ajustes hay dos «Guardar» con sentidos distintos. Dividir dice «elige archivos PDF o Markdown» aunque también acepta texto, CSV y Excel. «Incluir Subcarpetas» dice «se convierten», aunque aplica a las tres herramientas. «Las herramientas cambian archivos, nunca lo que hay dentro» se lee como una contradicción. «1 Fallidos» y «1 Ya Existen» parecen un error del programa. «Los Resultados Van» es una frase incompleta, y el Title Case en todo el catálogo español se lee como una traducción del inglés.
  - *Evidencia:* es.toml:450 y 453 gui.nav.done / nothing_written («Convierte más»), sin botón con ese texto tras la feature 033. gui.settings.split_keep = «Guardar» frente a save = «Guardar» (016/6-settings-light-es.png). tool.split «gui.plan.nothing». gui.settings.recursive_help. gui.home.files_note. es.toml:503 output_title = «Los Resultados Van» (en :512 ya existe «¿Dónde Van los Resultados?»). Etiquetas fijas en plural en las tarjetas (F3-05; 016/4-results-dark-es.png «1 Fallidos»).
  - *Recomendación:* «…o pulsa ¿Qué Sigue?». Cambiar el «Guardar» de las partes por «Conservar» o «Qué guardar de las partes». Listar los formatos reales de Dividir (mejor si la lista sale del código, como propone B4-04). Usar singular y plural en las tarjetas. Usar «¿Dónde Van los Resultados?». Proponer al dueño que, en español, la mayúscula vaya solo en la primera palabra, como recomienda la RAE, y mantener el Title Case en inglés. Es su decisión, porque contradice la doctrina vigente. Al cerrar cada feature, buscar en el catálogo las frases que nombran botones reemplazados.

</details>

## 10. Lecciones para las plantillas

Las lecciones de este ejercicio se incorporaron a
[`docs/lessons-learned.md`](../lessons-learned.md), Parte IX (en inglés, como el resto de ese archivo).
Lo que propuso la conciliadora:

- Toda operación que reemplaza un conjunto de archivos (partes, imágenes) debe ser atómica como conjunto: escribir lo nuevo aparte, moverlo al final y solo entonces borrar lo anterior. La plantilla debe traer la prueba de «cancelar a mitad conserva lo anterior».
- Todo nombre de salida generado por fecha u hora lleva un sufijo contra choques, y una prueba de «dos ejecuciones seguidas» lo comprueba.
- Deduplicar las entradas por archivo real después de expandir las carpetas, en el backend, con la prueba «carpeta más un archivo de su interior».
- Toda operación que mueve o combina Markdown valida que cada enlace local del resultado lleva a un archivo que existe.
- La taxonomía de notas nace con dos niveles (información y atención), y lo que la persona decidió (conservar) nunca cuenta como problema, ni en la ventana ni en el informe.
- Un mensaje nunca adivina una causa que el código no comprobó, y cada código de error tiene un solo significado. La plantilla debe traer pruebas de caminos tristes de punta a punta: archivo dañado, vacío, cifrado y una cancelación en cada herramienta.
- La Ayuda se verifica con pruebas: cada botón que cita existe, y cada herramienta del Inicio tiene su sección. Al cerrar una feature que cambia un botón, buscar en el catálogo todas las frases que lo nombran.
- Separar desde el principio los textos de ventana y de terminal, con un linter que prohíba «--opciones», nombres de librerías y de excepciones en la ventana, y que exija las formas singular y plural junto a un número.
- La pantalla final de todo flujo muestra la ruta exacta del resultado como texto, y ningún texto explicativo queda truncado sin otra forma de leerlo que no dependa del ratón.
- Toda lista de interfaz trae una prueba de presupuesto con 1.000 filas y la barra de desplazamiento visible al tamaño mínimo de ventana. Toda imagen por fila va en caché.
- El tamaño de cada archivo publicado tiene un límite en CI: el instalador por defecto pesa lo que instala por defecto.
- Los fixtures incluyen los formatos regionales reales del público: CSV con ';', BOM y cp1252, y Office antiguo (.doc, .xls, .ppt) con un mensaje propio.
- Si el instalador habla el idioma de la persona, la app debe arrancar en ese idioma: pasar la elección del instalador a la configuración inicial.
- Proceso de auditoría: cada auditor debe consultar los ADR antes de recomendar algo que los contradiga, y citar el ADR al hacerlo.
- Proceso de auditoría: en el debate, una afirmación adoptada de otro auditor debe volver a verificarse en el código antes de subirle la severidad. La coincidencia de varios auditores confirma el hecho, no su gravedad.
- Proceso de auditoría: la ronda de debate debe comparar con la ronda anterior para no dejar caer hallazgos reales (aquí, el idioma de arranque y el Office antiguo).
