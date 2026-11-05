"""The patterns of headings and captions, and a table of contents' entry (008, 013)."""

import re

MAX_HEADING_LINES = 3  # a heading wrapped on several lines is one heading; more is a paragraph


# A table of contents' entry ends with its page, after leaders: "Encuesta ....... 16" (013).
_TOC_PAGE = re.compile(r"(?<![\w])(?:\d{1,5}|[ivxlcdm]{1,8}|[IVXLCDM]{1,8})$")


# A table's or a figure's caption starts its own block (013): "Table 3: …", "Figura 2. …".
CAPTION = re.compile(
    r"(?:Table|Tabla|Cuadro|Figure|Figura|Fig\.|Gráfico|Gráfica|Ilustración)\s+[0-9IVXLC]+[.:]\s"
)


# "2 Methodology", "3.1 Data", "IV. RESULTADOS": numbered, then a capital (or "¿").
NUMBERED = re.compile(r"(?:(\d{1,2}(?:\.\d{1,2}){0,3})\.?|([IVXL]{1,5})\.)\s+[A-ZÁÉÍÓÚÑ¿]")
INSIDE_SENTENCE = re.compile(r"[.?!]\s+\S|=")


def toc_entry(text: str) -> bool:
    """A table of contents' entry: its leaders, then its page ("Encuesta ....... 16"). Read from
    the end of the line, never a pattern over it (a line of dots costs nothing; review of 013)."""
    stripped = text.rstrip()
    found = _TOC_PAGE.search(stripped[-12:])
    if found is None:
        return False
    before = stripped[: len(stripped) - len(found.group())].rstrip()
    return before.endswith(("....", "……", ". . . ."))
