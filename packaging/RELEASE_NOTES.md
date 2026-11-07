**ClearMD — documents to Markdown, 100 % local.** / **Documentos a Markdown, 100 % local.**

**New in 1.2.0 / Novedades de la 1.2.0**
- flet: before anything is chosen, the list shows two large tiles, **Add Files** and **Add Folder**,
  each with what it takes. / flet: antes de elegir nada, la lista muestra dos tarjetas grandes,
  **Agregar Archivos** y **Agregar Carpeta**, cada una con lo que recibe.
- Titles, buttons and the summary's headings in Title Case, in the three apps and in
  `Resumen_ClearMD` (Markdown and PDF). / Títulos, botones y encabezados del resumen con mayúscula
  inicial en cada palabra, en las tres apps y en `Resumen_ClearMD` (Markdown y PDF).

**New in 1.1.0 / Novedades de la 1.1.0**
- A third summary format, **PDF only**: just `Resumen_ClearMD.pdf`, no Markdown summary. Choose it
  on step 1 or in Settings, or use `--summary-pdf-only`. / Un tercer formato de resumen, **Solo
  PDF**: únicamente `Resumen_ClearMD.pdf`, sin el resumen en Markdown. Elígelo en el paso 1 o en
  Ajustes, o usa `--summary-pdf-only`.

**New in 1.0.1 / Novedades de la 1.0.1**
- The flet app converts at full speed: Windows could slow ClearMD's converter down as background
  work while flet's window was in front (a PDF took 19 s instead of 5). The converter now asks
  Windows not to; the window also redraws only the progress while converting. / La app flet
  convierte a toda velocidad: Windows podía frenar el convertidor de ClearMD como trabajo de fondo
  mientras la ventana de flet estaba al frente (un PDF tardaba 19 s en vez de 5). Ahora el
  convertidor le pide a Windows que no lo haga; además, la ventana solo redibuja el avance.
- flet: "Convert more" and Settings answer at the first press; the empty list and the cards look
  as in the other apps. The installer is always light. / flet: "Convertir más" y Ajustes responden
  a la primera; la lista vacía y las tarjetas se ven como en las otras apps. El instalador es
  siempre claro.

**ClearMD 1.0.0**
- The same app drawn with flet (Flutter), the third toolkit: `ClearMD-Flet-1.0.0-windows.zip` —
  unzip it and open `ClearMD-Flet.exe` in the folder — or tick "ClearMD (flet)" in the installer.
  Same steps, texts and look as the other two; files are added with its two buttons. With it,
  ClearMD offers its three apps and reaches version 1.0. / La misma app dibujada con flet
  (Flutter), el tercer toolkit: `ClearMD-Flet-1.0.0-windows.zip` — descomprímela y abre
  `ClearMD-Flet.exe` en la carpeta — o marca "ClearMD (flet)" en el instalador. Los mismos pasos,
  textos y aspecto que las otras dos; los archivos se añaden con sus dos botones. Con ella,
  ClearMD ofrece sus tres apps y llega a la versión 1.0.

**New in 0.13.2 / Novedades de la 0.13.2**
- The installer (`ClearMD-Setup-0.13.2.exe`) now looks like ClearMD: its logo and colours, light or
  dark as your Windows, and the three parts shown as cards, the recommended one marked. What it
  installs and how it uninstalls do not change. / El instalador (`ClearMD-Setup-0.13.2.exe`) ahora
  se ve como ClearMD: su logo y sus colores, claro u oscuro según tu Windows, y las tres partes
  como tarjetas, con la recomendada marcada. Lo que instala y cómo se desinstala no cambia.

**New in 0.12.0 / Novedades de la 0.12.0**
- An installer for Windows: `ClearMD-Setup-0.12.0.exe`. It installs for your user only (no
  administrator) and lets you choose the classic app (the lightest, the default), the modern
  app (Qt), the command line, or all of them; each with a short explanation. Remove it from
  *Installed apps*: it asks before deleting your settings. / Un instalador para Windows:
  `ClearMD-Setup-0.12.0.exe`. Instala solo para tu usuario (sin administrador) y te deja elegir la
  app clásica (la más liviana, la marcada), la moderna (Qt), la línea de comandos, o todas; cada
  una con una explicación corta. Se quita desde *Aplicaciones instaladas*: pregunta antes de
  borrar tus ajustes.

**New in 0.11.0 / Novedades de la 0.11.0**
- The same app drawn with Qt (PySide6): `ClearMD-Qt-0.11.0-windows.zip` — unzip it and open
  `ClearMD-Qt.exe` in the folder. Same steps, texts and look as the other app; try both. / La
  misma app dibujada con Qt (PySide6): `ClearMD-Qt-0.11.0-windows.zip` — descomprímela y abre
  `ClearMD-Qt.exe` en la carpeta. Los mismos pasos, textos y aspecto que la otra app; prueba las dos.

**New in 0.10.1 / Novedades de la 0.10.1**
- Fixed: with "Images: in a folder", every LaTeX (.tex) and Excel file failed to convert. They
  convert again. / Corregido: con "Imágenes: en una carpeta", todos los archivos LaTeX (.tex) y
  Excel fallaban al convertir. Ya convierten de nuevo.
- Inside: the code reorganized into small files, one concern each, with nothing changed in what
  ClearMD writes. / Por dentro: el código reorganizado en archivos pequeños, cada uno con una sola
  tarea, sin cambiar nada de lo que ClearMD escribe.

**New in 0.10.0 / Novedades de la 0.10.0**
- A PDF's equations as LaTeX: fractions, sums with their limits, brackets and scripts rebuilt
  from the drawing, shown as formulas in VS Code, GitHub or Obsidian, and copyable; equations
  with no number found too. / Las ecuaciones de un PDF como LaTeX: fracciones, sumatorias con sus
  límites, corchetes y subíndices rehechos desde el dibujo; se ven como fórmulas en VS Code,
  GitHub u Obsidian y se pueden copiar; también se encuentran las ecuaciones sin número.

**New in 0.9.0 / Novedades de la 0.9.0**
- A PDF's sub- and superscripts read as such (EFᵗₒ, Rᴺ₊, a footnote's ²) and its equations stay
  whole; one margin around and inside the page; each step's cards shown faded before there is
  anything in them. / Los subíndices y superíndices de un PDF se leen como tales (EFᵗₒ, Rᴺ₊, la
  llamada ² de una nota) y sus ecuaciones salen enteras; un solo margen alrededor y dentro de la
  página; las tarjetas de cada paso se ven atenuadas mientras no hay nada en ellas.

**New in 0.8.0 / Novedades de la 0.8.0**
- A PDF's tables become Markdown tables (ruled or not, upright or sideways), its numbered
  equations stay whole (a picture with the images folder), its table of contents one entry per
  line. / Las tablas de un PDF salen como tablas Markdown (con o sin bordes, derechas o giradas),
  sus ecuaciones numeradas enteras (como imagen con la carpeta de imágenes) y su índice con una
  entrada por línea.

**New in 0.7.0 / Novedades de la 0.7.0**
- Optionally, each document's images in a folder next to its Markdown (`report_images`;
  `_imagenes` in Spanish): docx, pptx, ODT, EPUB and PDF. Chosen on step 1 and in Settings; off
  by default. / Opcional: las imágenes de cada documento en una carpeta junto a su Markdown
  (`informe_imagenes`): docx, pptx, ODT, EPUB y PDF. Se elige en el paso 1 y en Ajustes; apagado
  por defecto.

**New in 0.6.0 / Novedades de la 0.6.0**
- Settings and Help are sections of the rail; the page sits in a soft card under a whole shape;
  every step says what is missing. / Ajustes y Ayuda son secciones del riel; la página va en un
  área demarcada bajo una nube entera; cada paso dice qué falta.

**New in 0.5.0 / Novedades de la 0.5.0**
- **Less than half the size**: the app weighs about 40 MB instead of 90, and starts faster. /
  **Menos de la mitad de peso**: la app pesa unos 40 MB en vez de 90, y abre más rápido.
- Excel workbooks convert faster and with far less memory. / Los libros de Excel se convierten
  más rápido y con mucha menos memoria.

**New in 0.4.0 / Novedades de la 0.4.0**
- **A summary you can read at a glance**: how it went first, where your files are, what needs
  your attention and what to do, names instead of long paths, the history folded. / **Un resumen
  que se entiende de un vistazo**: primero cómo te fue, dónde están tus archivos, qué necesita tu
  atención y qué hacer, nombres en vez de rutas largas, el historial plegado.
- **The summary as a PDF too**, in the app's look: choose "Markdown + PDF" on the first step or
  in Settings. / **El resumen también en PDF**, con el aspecto de la app: elige
  "Markdown + PDF" en el primer paso o en Ajustes.

**New in 0.3.0 / Novedades de la 0.3.0**
- **PDFs come out readable**: words keep their spaces; headers, footers and page numbers that
  repeat on the pages are left out; paragraphs, footnotes and headings are found. / **Los PDF
  salen legibles**: las palabras conservan sus espacios; se quitan los encabezados, pies y números
  de página que se repiten; se reconocen párrafos, notas al pie y títulos.
- Text in fonts without a character map is read back; what cannot be read, and scanned pages,
  are told in the summary. / El texto en fuentes sin mapa de caracteres se recupera; lo que no se
  puede leer, y las páginas escaneadas, se avisan en el resumen.

| File | What |
|---|---|
| `ClearMD-…-windows.exe` | The desktop app for Windows: download it and double-click it. / La app de escritorio para Windows: descárgala y ábrela con doble clic. |
| `clearmd-cli-…-windows.exe` | The command line for Windows. / La línea de comandos para Windows. |
| `ClearMD-…-linux.tar.gz` | Both, for Linux (x86-64). / Ambas, para Linux (x86-64). |
| `THIRD-PARTY-NOTICES.txt` | The licenses of the libraries inside. / Las licencias de las librerías incluidas. |

- **Windows may warn that the app is not recognized** (it is not code-signed yet). Click
  *More info → Run anyway*. / **Windows puede advertir que la app no es reconocida** (aún no está
  firmada). Pulsa *Más información → Ejecutar de todas formas*.
  [Code signing policy](https://github.com/ClearNote97/ClearMD/blob/main/CODE_SIGNING.md).
- **Uninstall:** delete the file; nothing else is installed. / **Desinstalar:** borra el archivo;
  no se instala nada más.
- The first start takes a few seconds (the app unpacks itself). / El primer inicio tarda unos
  segundos (la app se descomprime).
- Nothing leaves your computer: ClearMD never uses the internet. / Nada sale de tu computador:
  ClearMD nunca usa internet.
