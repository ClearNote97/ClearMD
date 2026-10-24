# visuals/templates — Plantillas de render / documento

Ficheros **plantilla** que el código rellena con datos para producir un artefacto:
LaTeX (`.tex`, `.cls`), Jinja2 (→ LaTeX / HTML / Markdown), plantillas de reporte, de correo, etc.

**Qué va aquí:** los ficheros de plantilla en sí, organizados por propósito (una subcarpeta por
familia de plantilla si crecen). El código de render (en `src/…`) los localiza y los rellena.

**Imágenes y estáticos que la plantilla referencia:**
- Imágenes institucionales **compartidas** (logos, banners) → `../images/`.
- Fuentes / estáticos no-imagen → `../assets/`.
- Estáticos **acoplados** a una plantilla concreta (un `.cls`, un fondo propio) → junto a la
  plantilla, en su subcarpeta aquí.

**Estado 0:** la carpeta **viaja** con la plantilla; su **contenido depende del proyecto** (agnóstico —
no trae material institucional). Llénala cuando tu proyecto genere documentos.

> Ejemplo (proyecto tipo AutoCV): `templates/cv/altacv.cls` + `templates/cv/cv.tex.jinja`; el render en
> `src/…` carga la plantilla de aquí, la rellena con los datos y compila a PDF.
