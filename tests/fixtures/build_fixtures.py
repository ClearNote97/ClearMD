"""Build the sample documents used by the tests, reproducibly.

Run inside the container:  uv run python tests/fixtures/build_fixtures.py

Every document carries a unique marker (``MARKERS``) so a test can check that its text survived the
conversion. ZIP-based documents get fixed timestamps, so rebuilding yields the same bytes.
"""

import io
import json
import re
import zipfile
from collections.abc import Callable
from pathlib import Path

# openpyxl and python-pptx come with markitdown's xlsx/pptx extras; openpyxl ships no type
# information (mypy override in pyproject.toml).
import openpyxl
import pptx
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, ByteStringObject

DOCUMENTS_DIR = Path(__file__).parent / "documents"

FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
FIXED_ISO_TIME = "2026-01-01T00:00:00Z"
PDF_PASSWORD = "clearmd"
BOMB_UNCOMPRESSED_BYTES = 20 * 1024**2

MARKERS = {
    "sample.pdf": "fixture-pdf",
    "encrypted.pdf": "fixture-pdf",
    "sample.docx": "fixture-docx",
    "docx_without_extension": "fixture-docx",
    "sample.pptx": "fixture-pptx",
    "sample.xlsx": "fixture-xlsx",
    "sample.html": "fixture-html",
    "sample.csv": "fixture-csv",
    "sample.epub": "fixture-epub",
    "sample.ipynb": "fixture-ipynb",
    "sample.txt": "fixture-txt",
}

# Files whose bytes cannot be reproduced exactly (e.g. encryption salts); the tests check their
# properties instead.
NON_DETERMINISTIC: frozenset[str] = frozenset()


# --- ZIP helpers ---------------------------------------------------------------------------------


def _zip_info(name: str, compress_type: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.compress_type = compress_type
    info.external_attr = 0o644 << 16
    return info


def _write_zip(entries: list[tuple[str, bytes]], *, stored: frozenset[str] = frozenset()) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in entries:
            compress = zipfile.ZIP_STORED if name in stored else zipfile.ZIP_DEFLATED
            archive.writestr(_zip_info(name, compress), data)
    return buffer.getvalue()


def _normalize_office_zip(data: bytes) -> bytes:
    """Rewrite a library-made Office file with fixed timestamps (entries and core properties)."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = [(info.filename, archive.read(info)) for info in archive.infolist()]
    normalized = []
    for name, content in entries:
        if name == "docProps/core.xml":
            text = content.decode("utf-8")
            text = re.sub(
                r"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)",
                rf"\g<1>{FIXED_ISO_TIME}\g<2>",
                text,
            )
            content = text.encode("utf-8")
        normalized.append((name, content))
    return _write_zip(normalized)


# --- PDF -----------------------------------------------------------------------------------------


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def minimal_pdf(lines: list[str]) -> bytes:
    """A one-page PDF with Helvetica text, written by hand with correct xref offsets."""
    text_ops = " 0 -16 Td ".join(f"({_pdf_escape(line)}) Tj" for line in lines)
    stream = f"BT /F1 12 Tf 72 720 Td {text_ops} ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode()
    out += f"startxref\n{xref_at}\n%%EOF\n".encode()
    return bytes(out)


def encrypted_pdf(source: bytes) -> bytes:
    writer = PdfWriter()
    writer.append(PdfReader(io.BytesIO(source)))
    # A fixed file identifier: with RC4 the encryption keys derive only from it and the passwords.
    file_id = ByteStringObject(b"clearmd-fixture!")
    writer._ID = ArrayObject([file_id, file_id])
    writer.encrypt(user_password=PDF_PASSWORD, algorithm="RC4-128")
    writer.add_metadata({"/Producer": "ClearMD fixtures"})
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# --- Office and e-book documents ------------------------------------------------------------------

_DOCX_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    "</Types>"
)
_DOCX_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    "</Relationships>"
)
_DOCX_DOCUMENT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
    'Target="styles.xml"/>'
    "</Relationships>"
)
_DOCX_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style>'
    "</w:styles>"
)
_W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _docx_document(body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:document {_W_NS}><w:body>{body}</w:body></w:document>"
    )


def minimal_docx() -> bytes:
    body = (
        '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        "<w:r><w:t>ClearMD fixture</w:t></w:r></w:p>"
        '<w:p><w:r><w:t xml:space="preserve">Text from a DOCX document: </w:t></w:r>'
        f"<w:r><w:rPr><w:b/></w:rPr><w:t>{MARKERS['sample.docx']}</w:t></w:r></w:p>"
    )
    return _write_zip(
        [
            ("[Content_Types].xml", _DOCX_CONTENT_TYPES.encode()),
            ("_rels/.rels", _DOCX_ROOT_RELS.encode()),
            ("word/_rels/document.xml.rels", _DOCX_DOCUMENT_RELS.encode()),
            ("word/styles.xml", _DOCX_STYLES.encode()),
            ("word/document.xml", _docx_document(body).encode()),
        ]
    )


def zip_bomb_docx() -> bytes:
    """A docx whose document.xml expands ~1000:1 — small on disk, large in memory."""
    paragraph = b"<w:p><w:r><w:t>ClearMD zip bomb fixture</w:t></w:r></w:p>"
    head = f'<?xml version="1.0" encoding="UTF-8"?><w:document {_W_NS}><w:body>'.encode()
    tail = b"</w:body></w:document>"
    repeats = (BOMB_UNCOMPRESSED_BYTES - len(head) - len(tail)) // len(paragraph)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compresslevel=9) as archive:
        archive.writestr(
            _zip_info("[Content_Types].xml", zipfile.ZIP_DEFLATED), _DOCX_CONTENT_TYPES
        )
        archive.writestr(_zip_info("_rels/.rels", zipfile.ZIP_DEFLATED), _DOCX_ROOT_RELS)
        with archive.open(_zip_info("word/document.xml", zipfile.ZIP_DEFLATED), "w") as entry:
            entry.write(head)
            chunk = paragraph * 4096
            for _ in range(repeats // 4096):
                entry.write(chunk)
            entry.write(paragraph * (repeats % 4096))
            entry.write(tail)
    return buffer.getvalue()


def minimal_pptx() -> bytes:
    presentation = pptx.Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "ClearMD fixture"
    slide.placeholders[1].text = f"Text from a PPTX slide: {MARKERS['sample.pptx']}"
    buffer = io.BytesIO()
    presentation.save(buffer)
    return _normalize_office_zip(buffer.getvalue())


def minimal_xlsx() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Data"
    sheet.append(["Name", "Value"])
    sheet.append([MARKERS["sample.xlsx"], 1])
    sheet.append(["second row", 2])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return _normalize_office_zip(buffer.getvalue())


def minimal_epub() -> bytes:
    container = (
        '<?xml version="1.0"?>'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/>'
        "</rootfiles></container>"
    )
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:identifier id="id">clearmd-fixture</dc:identifier><dc:title>ClearMD fixture</dc:title>'
        "<dc:creator>ClearMD</dc:creator><dc:language>en</dc:language></metadata>"
        '<manifest><item id="chapter1" href="chapter1.xhtml" '
        'media-type="application/xhtml+xml"/></manifest>'
        '<spine><itemref idref="chapter1"/></spine></package>'
    )
    chapter = (
        '<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml">'
        "<head><title>Chapter 1</title></head><body><h1>Chapter 1</h1>"
        f"<p>Text from an EPUB chapter: {MARKERS['sample.epub']}</p></body></html>"
    )
    return _write_zip(
        [
            ("mimetype", b"application/epub+zip"),
            ("META-INF/container.xml", container.encode()),
            ("OEBPS/content.opf", opf.encode()),
            ("OEBPS/chapter1.xhtml", chapter.encode()),
        ],
        stored=frozenset({"mimetype"}),
    )


# --- Plain-text formats --------------------------------------------------------------------------


def minimal_html() -> bytes:
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>ClearMD fixture</title></head>'
        "<body><h1>ClearMD fixture</h1>"
        f"<p>Text from an HTML page: {MARKERS['sample.html']}</p></body></html>\n"
    ).encode()


def minimal_csv() -> bytes:
    return f"name,value\n{MARKERS['sample.csv']},1\nsecond row,2\n".encode()


def minimal_txt() -> bytes:
    return f"Text from a plain-text file: {MARKERS['sample.txt']}\n".encode()


def minimal_ipynb() -> bytes:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# ClearMD fixture\n", MARKERS["sample.ipynb"]],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["1 + 1"],
            },
        ],
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return (json.dumps(notebook, indent=1) + "\n").encode()


# --- Build ---------------------------------------------------------------------------------------


def build(destination: Path) -> dict[str, Path]:
    """Write every fixture into ``destination`` and return them by name."""
    pdf = minimal_pdf(["ClearMD fixture", f"Text from a PDF document: {MARKERS['sample.pdf']}"])
    docx = minimal_docx()
    builders: dict[str, Callable[[], bytes]] = {
        "sample.pdf": lambda: pdf,
        "encrypted.pdf": lambda: encrypted_pdf(pdf),
        # A PDF header followed by garbage: no objects, no trailer.
        "corrupt.pdf": lambda: b"%PDF-1.4\n" + b"\x00garbage\x00" * 64,
        "sample.docx": lambda: docx,
        "docx_without_extension": lambda: docx,
        # The first half of a valid docx: its ZIP central directory is missing.
        "corrupt.docx": lambda: docx[: len(docx) // 2],
        "zip_bomb.docx": zip_bomb_docx,
        "sample.pptx": minimal_pptx,
        "sample.xlsx": minimal_xlsx,
        "sample.epub": minimal_epub,
        "sample.html": minimal_html,
        "sample.csv": minimal_csv,
        "sample.txt": minimal_txt,
        "sample.ipynb": minimal_ipynb,
    }
    destination.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, make in builders.items():
        path = destination / name
        path.write_bytes(make())
        written[name] = path
    return written


# --- LaTeX (feature 002) -------------------------------------------------------------------------

TEX_DIR = Path(__file__).parent / "tex"

PAPER_TEX = r"""\documentclass{article}
\usepackage[spanish]{babel}
\usepackage{graphicx,hyperref,listings,amsmath}
\title{Un art\'iculo de prueba}
\author{Ana P\'erez}
\date{2026}
\begin{document}
\maketitle
\begin{abstract}
Resumen breve con $x^2$.
\end{abstract}
\section{Introducci\'on}
Texto con \textbf{negrita}, \textit{it\'alica}, \emph{\'enfasis}, \texttt{c\'odigo} y
\underline{subrayado}. Marcador: fixture-tex-paper.
Ver \cite{knuth84,lamport94} y la ecuaci\'on~\eqref{eq:pit}.\footnote{Una nota al pie.}
\subsection{Listas}
\begin{itemize}
  \item uno
  \item dos
  \begin{enumerate}
    \item anidado
  \end{enumerate}
\end{itemize}
\begin{description}
  \item[T\'ermino] Su definici\'on.
\end{description}
\subsection{Matem\'aticas}
En l\'inea $E=mc^2$ y \(a+b\) y $\alpha_{i}~\text{texto}$.
\[ \int_0^1 x\,dx \]
\begin{equation}\label{eq:pit} a^2+b^2=c^2 \end{equation}
\begin{align} x &= 1 \\ y &= 2 \end{align}
\subsection{C\'odigo y citas}
\begin{lstlisting}[language=Python]
print("hola $no math$ \section{no}")
\end{lstlisting}
El comando \verb|\foo| en l\'inea.
\begin{quote}Una cita.\end{quote}
\href{https://example.org}{un enlace} y \url{https://example.org/b} -- rango --- raya ``comillas''.
\subsection{Tablas y figuras}
\begin{table}\centering
\begin{tabular}{|l|c|}\hline
A & B \\ \hline
1 & $x$ \\ \hline
\end{tabular}
\caption{Una tabla}
\end{table}
\begin{figure}\centering
\includegraphics[width=0.5\textwidth]{img/plot}
\caption{Un gr\'afico}
\end{figure}
\newpage
% un comentario que desaparece
\end{document}
"""

UNKNOWN_TEX = r"""\documentclass{article}
\begin{document}
\section{Desconocidos}
Texto \customcommand{x} y \otherthing.
\begin{weirdenv}dentro\end{weirdenv}
\end{document}
"""

MULTICOLUMN_TEX = r"""\documentclass{article}
\begin{document}
\begin{tabular}{lcc}
\multicolumn{2}{c}{Encabezado} & C \\
1 & 2 & 3 \\
\end{tabular}
\end{document}
"""

MALFORMED_TEX = r"""\documentclass{article}
\begin{document}
\section{Abierto
Texto despu\'es de un grupo sin cerrar, fixture-tex-malformed.
\end{itemize}
\end{document}
"""

LATIN1_BODY = (
    "\\section{Introducción}\nCañón, acción y ñandú: fixture-tex-latin1.\n\\end{document}\n"
)
LATIN1_DECLARED = (
    "\\documentclass{article}\n\\usepackage[latin1]{inputenc}\n\\begin{document}\n" + LATIN1_BODY
)
LATIN1_UNDECLARED = "\\documentclass{article}\n\\begin{document}\n" + LATIN1_BODY

THESIS_MAIN = r"""\documentclass{report}
\usepackage[spanish]{babel}
\input{macros}
\graphicspath{{img/}}
\title{Una tesis}
\author{Autor}
\begin{document}
\maketitle
\input{chapters/ch1}
\include{chapters/ch2}
\end{document}
"""
THESIS_MACROS = r"""\newcommand{\R}{\mathbb{R}}
\newcommand{\norm}[1]{\left\lVert #1 \right\rVert}
\newcommand{\pair}[2][0]{(#1, #2)}
\DeclareMathOperator{\argmax}{arg\,max}
\def\ClearMD{ClearMD}
"""
THESIS_CH1 = r"""\chapter{Primer cap\'itulo}
Sea $x \in \R$ con $\norm{x} \le 1$ y $\pair{a}$, $\pair[b]{c}$. Herramienta: \ClearMD{}.
Marcador: fixture-tex-ch1.
\begin{figure}\includegraphics{plot}\caption{Desde graphicspath}\end{figure}
"""
THESIS_CH2 = r"""\chapter{Segundo cap\'itulo}
$\argmax_{\theta} f(\theta)$. Marcador: fixture-tex-ch2.
\input{sections/deeper}
"""
THESIS_DEEPER = r"""\section{M\'as hondo}
Marcador: fixture-tex-deeper.
"""


def _document(body: str) -> str:
    return f"\\documentclass{{article}}\\begin{{document}}{body}\\end{{document}}\n"


def _bomb_name(level: int) -> str:
    """Letters only: in LaTeX a digit ends a macro name (\\mac0 is \\mac followed by 0)."""
    return "\\bomb" + chr(ord("a") + level // 26) + chr(ord("a") + level % 26)


BOMB_LEVELS = 40
HOSTILE = {
    "absolute.tex": _document("\\input{/etc/passwd}"),
    "parent.tex": _document("\\input{../paper}"),
    "not_tex.tex": _document("\\input{data.csv}"),
    "missing.tex": _document("\\input{nowhere}"),
    "cycle_a.tex": "A \\input{cycle_b}\n",
    "cycle_b.tex": "B \\input{cycle_a}\n",
    "recursive_macro.tex": (
        "\\documentclass{article}\\newcommand{\\loop}{x\\loop}"
        "\\begin{document}Antes $\\loop$ despues\\end{document}\n"
    ),
    # 2**40 copies of "x" if nothing stopped it.
    "exponential_macro.tex": (
        "\\documentclass{article}"
        + "".join(
            f"\\def{_bomb_name(i)}{{{_bomb_name(i + 1)}{_bomb_name(i + 1)}}}"
            for i in range(BOMB_LEVELS)
        )
        + f"\\def{_bomb_name(BOMB_LEVELS)}{{x}}"
        + f"\\begin{{document}}${_bomb_name(0)}$\\end{{document}}\n"
    ),
    "data.csv": "a,b\n1,2\n",
}
for level in range(10):
    following = f"\\input{{deep{level + 1}}}" if level < 9 else "fondo"
    HOSTILE[f"deep{level}.tex"] = f"nivel {level} {following}\n"


def tiny_png() -> bytes:
    """A valid 1x1 PNG, so image paths can be checked against a real file."""
    import struct
    import zlib

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    pixels = zlib.compress(b"\x00\xff\xff\xff", 9)
    return (
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", pixels) + chunk(b"IEND", b"")
    )


def build_tex(destination: Path) -> dict[str, Path]:
    """Write the LaTeX fixtures (relative names, folders included) and return them."""
    files: dict[str, bytes] = {
        "paper.tex": PAPER_TEX.encode(),
        "img/plot.png": tiny_png(),
        "unknown.tex": UNKNOWN_TEX.encode(),
        "multicolumn.tex": MULTICOLUMN_TEX.encode(),
        "malformed.tex": MALFORMED_TEX.encode(),
        "latin1.tex": LATIN1_DECLARED.encode("latin-1"),
        "latin1_undeclared.tex": LATIN1_UNDECLARED.encode("latin-1"),
        "no_extension_latex": PAPER_TEX.encode(),
        "thesis/main.tex": THESIS_MAIN.encode(),
        "thesis/macros.tex": THESIS_MACROS.encode(),
        "thesis/chapters/ch1.tex": THESIS_CH1.encode(),
        "thesis/chapters/ch2.tex": THESIS_CH2.encode(),
        "thesis/chapters/sections/deeper.tex": THESIS_DEEPER.encode(),
        "thesis/img/plot.png": tiny_png(),
        **{f"hostile/{name}": text.encode() for name, text in HOSTILE.items()},
    }
    written = {}
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        written[name] = path
    return written


if __name__ == "__main__":
    for path in [*build(DOCUMENTS_DIR).values(), *build_tex(TEX_DIR).values()]:
        shown = path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path
        print(f"{path.stat().st_size:>8}  {shown}")
