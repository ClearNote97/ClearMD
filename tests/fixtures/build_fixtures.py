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
\input{chapters/sections/deeper}
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


# --- OpenDocument text (feature 003) -------------------------------------------------------------

ODT_DIR = Path(__file__).parent / "odt"
ODT_MIME = "application/vnd.oasis.opendocument.text"
ODS_MIME = "application/vnd.oasis.opendocument.spreadsheet"
ODF_NAMESPACES = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:xlink="http://www.w3.org/1999/xlink" '
    'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:math="http://www.w3.org/1998/Math/MathML" '
    'office:version="1.3"'
)
_MANIFEST_NS = 'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"'

ODT_FONTS = (
    "<office:font-face-decls>"
    '<style:font-face style:name="Liberation Mono" svg:font-family="&apos;Liberation Mono&apos;" '
    'style:font-pitch="fixed"/>'
    '<style:font-face style:name="Liberation Serif" svg:font-family="&apos;Liberation Serif&apos;" '
    'style:font-pitch="variable"/>'
    "</office:font-face-decls>"
)
# Named styles as LibreOffice writes them (styles.xml), parents included.
ODT_NAMED_STYLES = (
    "<office:styles>"
    '<style:style style:name="Standard" style:family="paragraph"/>'
    '<style:style style:name="Heading" style:family="paragraph" '
    'style:parent-style-name="Standard"/>'
    '<style:style style:name="Title" style:family="paragraph" style:parent-style-name="Heading"/>'
    '<style:style style:name="Subtitle" style:family="paragraph" '
    'style:parent-style-name="Heading"/>'
    '<style:style style:name="Quotations" style:family="paragraph" '
    'style:parent-style-name="Standard"/>'
    '<style:style style:name="Preformatted_20_Text" style:display-name="Preformatted Text" '
    'style:family="paragraph" style:parent-style-name="Standard"/>'
    '<style:style style:name="Emphasis" style:family="text">'
    '<style:text-properties fo:font-style="italic"/></style:style>'
    '<style:style style:name="Strong_20_Emphasis" style:display-name="Strong Emphasis" '
    'style:family="text"><style:text-properties fo:font-weight="bold"/></style:style>'
    '<style:style style:name="Source_20_Text" style:display-name="Source Text" style:family="text">'
    '<style:text-properties style:font-name="Liberation Mono"/></style:style>'
    "</office:styles>"
)
ODT_AUTOMATIC_STYLES = (
    "<office:automatic-styles>"
    '<style:style style:name="T1" style:family="text">'
    '<style:text-properties fo:font-weight="bold"/></style:style>'
    '<style:style style:name="T2" style:family="text">'
    '<style:text-properties fo:font-style="italic"/></style:style>'
    '<style:style style:name="T3" style:family="text">'
    '<style:text-properties style:text-underline-style="solid"/></style:style>'
    '<style:style style:name="T4" style:family="text">'
    '<style:text-properties style:text-line-through-style="solid"/></style:style>'
    '<style:style style:name="T5" style:family="text">'
    '<style:text-properties style:text-position="super 58%"/></style:style>'
    '<style:style style:name="T6" style:family="text">'
    '<style:text-properties style:text-position="sub 58%"/></style:style>'
    '<style:style style:name="T7" style:family="text">'
    '<style:text-properties style:font-name="Liberation Mono"/></style:style>'
    '<style:style style:name="T8" style:family="text" style:parent-style-name="Strong_20_Emphasis">'
    '<style:text-properties fo:font-style="italic"/></style:style>'
    '<style:style style:name="P1" style:family="paragraph" style:parent-style-name="Quotations"/>'
    '<style:style style:name="P2" style:family="paragraph" '
    'style:parent-style-name="Preformatted_20_Text"/>'
    '<text:list-style style:name="L1">'
    '<text:list-level-style-bullet text:level="1" text:bullet-char="•"/>'
    '<text:list-level-style-number text:level="2" style:num-format="1"/>'
    "</text:list-style>"
    '<text:list-style style:name="L2">'
    '<text:list-level-style-number text:level="1" style:num-format="1" text:start-value="3"/>'
    "</text:list-style>"
    "</office:automatic-styles>"
)

ODT_REPORT_BODY = (
    '<text:p text:style-name="Title">Informe de prueba</text:p>'
    '<text:p text:style-name="Subtitle">Un subtítulo</text:p>'
    '<text:h text:outline-level="1">Introducción</text:h>'
    "<text:p>Texto con "
    '<text:span text:style-name="T1">negrita</text:span>, '
    '<text:span text:style-name="T2">itálica</text:span>, '
    '<text:span text:style-name="T3">subrayado</text:span>, '
    '<text:span text:style-name="T4">tachado</text:span>, '
    'm<text:span text:style-name="T5">2</text:span>, '
    'H<text:span text:style-name="T6">2</text:span>O, '
    '<text:span text:style-name="T7">código</text:span>, '
    '<text:span text:style-name="Emphasis">énfasis</text:span>, '
    '<text:span text:style-name="Strong_20_Emphasis">fuerte</text:span> y '
    '<text:span text:style-name="T8">ambos</text:span>. Marcador: fixture-odt-report.</text:p>'
    '<text:h text:outline-level="2">Listas y enlaces</text:h>'
    '<text:list text:style-name="L1">'
    "<text:list-item><text:p>uno</text:p></text:list-item>"
    "<text:list-item><text:p>dos</text:p>"
    "<text:list><text:list-item><text:p>anidado</text:p></text:list-item></text:list>"
    "</text:list-item>"
    "</text:list>"
    '<text:list text:style-name="L2">'
    "<text:list-item><text:p>tres</text:p></text:list-item>"
    "<text:list-item><text:p>cuatro</text:p></text:list-item>"
    "</text:list>"
    '<text:p>Un <text:a xlink:type="simple" xlink:href="https://example.org">enlace</text:a>'
    ' y una nota.<text:note text:id="ftn1" text:note-class="footnote">'
    "<text:note-citation>1</text:note-citation>"
    "<text:note-body><text:p>Una nota al pie.</text:p></text:note-body></text:note>"
    ' Y otra al final.<text:note text:id="edn1" text:note-class="endnote">'
    "<text:note-citation>i</text:note-citation>"
    "<text:note-body><text:p>Una nota final.</text:p></text:note-body></text:note></text:p>"
    '<text:h text:outline-level="2">Citas, código y espacios</text:h>'
    '<text:p text:style-name="P1">Una cita.</text:p>'
    '<text:p text:style-name="P2">def f(x):</text:p>'
    '<text:p text:style-name="P2"><text:s text:c="4"/>return x</text:p>'
    '<text:p>a<text:s text:c="3"/>b<text:tab/>c<text:line-break/>d</text:p>'
    '<text:p>Página <text:page-number text:select-page="current">7</text:page-number>'
    ' del <text:date text:date-value="2026-10-25">25/10/2026</text:date>.'
    '<text:hidden-text text:condition="" text:string-value="oculto" text:is-hidden="true"/>'
    '<text:bookmark text:name="b1"/><text:soft-page-break/></text:p>'
    '<text:hidden-paragraph text:condition="" text:is-hidden="true"/>'
    '<text:table-of-content text:name="Indice"><text:index-body>'
    "<text:p>Introducción ..... 1</text:p></text:index-body></text:table-of-content>"
    '<text:h text:outline-level="3">Tabla</text:h>'
    '<table:table table:name="T"><table:table-column table:number-columns-repeated="2"/>'
    "<table:table-header-rows><table:table-row>"
    "<table:table-cell><text:p>A</text:p></table:table-cell>"
    "<table:table-cell><text:p>B</text:p></table:table-cell>"
    "</table:table-row></table:table-header-rows>"
    "<table:table-row><table:table-cell><text:p>1</text:p></table:table-cell>"
    '<table:table-cell><text:p><text:span text:style-name="T1">2</text:span></text:p>'
    "</table:table-cell></table:table-row>"
    "</table:table>"
)
ODT_MERGED_BODY = (
    "<text:p>Antes. Marcador: fixture-odt-merged.</text:p>"
    "<table:table>"
    "<table:table-row>"
    '<table:table-cell table:number-columns-spanned="2"><text:p>Junta</text:p></table:table-cell>'
    "<table:covered-table-cell/>"
    "</table:table-row>"
    "<table:table-row><table:table-cell><text:p>a</text:p></table:table-cell>"
    "<table:table-cell><text:p>b</text:p></table:table-cell></table:table-row>"
    "</table:table>"
)
ODT_REVISIONS_BODY = (
    "<text:tracked-changes>"
    '<text:changed-region text:id="c1"><text:deletion><office:change-info>'
    "<dc:creator>Ana</dc:creator><dc:date>2026-10-25T10:00:00</dc:date></office:change-info>"
    "<text:p>borrado</text:p></text:deletion></text:changed-region>"
    "</text:tracked-changes>"
    '<text:p>Texto final<text:change text:change-id="c1"/>. Marcador: fixture-odt-revisions.'
    "<office:annotation><dc:creator>Luis</dc:creator><text:p>Un comentario</text:p>"
    "</office:annotation></text:p>"
)
ODT_UNKNOWN_BODY = (
    "<text:p>Antes. Marcador: fixture-odt-unknown.</text:p>"
    '<draw:custom-shape draw:name="Forma"><text:p>texto en forma</text:p></draw:custom-shape>'
    "<text:p><text:ruby><text:ruby-base>漢字</text:ruby-base></text:ruby> fin</text:p>"
)
ODT_IMAGES_BODY = (
    "<text:p>Marcador: fixture-odt-images.</text:p>"
    '<text:p><draw:frame draw:name="Imagen1" text:anchor-type="paragraph" svg:width="2cm" '
    'svg:height="2cm"><draw:image xlink:href="Pictures/map.png" xlink:type="simple"/>'
    "<svg:title>Mapa de la región</svg:title></draw:frame></text:p>"
    '<text:p><draw:frame draw:name="Imagen2"><draw:image xlink:href="Pictures/map.png"/>'
    "<svg:desc>Una descripción</svg:desc></draw:frame></text:p>"
    '<text:p><draw:frame draw:name="Logo"><draw:image xlink:href="Pictures/map.png"/>'
    "</draw:frame></text:p>"
)
MATHML_SUBSET = (
    '<math:math xmlns:math="http://www.w3.org/1998/Math/MathML" display="block"><math:semantics>'
    "<math:mrow><math:mfrac><math:mi>a</math:mi><math:mi>b</math:mi></math:mfrac>"
    "<math:mo>+</math:mo><math:msup><math:mi>x</math:mi><math:mn>2</math:mn></math:msup>"
    "<math:mo>+</math:mo><math:msqrt><math:mi>y</math:mi></math:msqrt>"
    "<math:mo>+</math:mo><math:mi>α</math:mi></math:mrow>"
    '<math:annotation encoding="StarMath 5.0">{a over b} + x^2 + sqrt{y} + %alpha</math:annotation>'
    "</math:semantics></math:math>"
)
MATHML_SUM = (
    '<math:math xmlns:math="http://www.w3.org/1998/Math/MathML"><math:semantics>'
    "<math:mrow><math:munderover><math:mo>∑</math:mo>"
    "<math:mrow><math:mi>i</math:mi><math:mo>=</math:mo><math:mn>1</math:mn></math:mrow>"
    "<math:mi>n</math:mi></math:munderover><math:mi>i</math:mi></math:mrow>"
    '<math:annotation encoding="StarMath 5.0">sum from{i=1} to{n} i</math:annotation>'
    "</math:semantics></math:math>"
)
MATHML_OUTSIDE = (
    '<math:math xmlns:math="http://www.w3.org/1998/Math/MathML"><math:semantics>'
    '<math:mrow><math:menclose notation="box"><math:mi>z</math:mi></math:menclose></math:mrow>'
    '<math:annotation encoding="StarMath 5.0">boxed z</math:annotation>'
    "</math:semantics></math:math>"
)
ODT_FORMULAS_BODY = (
    "<text:p>Marcador: fixture-odt-formulas.</text:p>"
    '<text:p><draw:frame draw:name="F1" text:anchor-type="as-char">'
    '<draw:object xlink:href="./Object 1" xlink:type="simple"/></draw:frame></text:p>'
    '<text:p>En línea <draw:frame draw:name="F2" text:anchor-type="as-char">'
    '<draw:object xlink:href="./Object 2"/></draw:frame> y fin.</text:p>'
    '<text:p>Fuera: <draw:frame draw:name="F3" text:anchor-type="as-char">'
    '<draw:object xlink:href="./Object 3"/></draw:frame>.</text:p>'
    '<text:p>Afuera: <draw:frame draw:name="F4" text:anchor-type="as-char">'
    '<draw:object xlink:href="../escape"/></draw:frame>.</text:p>'
)


def _odt_xml(root: str, body: str, *, automatic: str = ODT_AUTOMATIC_STYLES) -> bytes:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><office:{root} {ODF_NAMESPACES}>'
        f"{ODT_FONTS}{automatic}<office:body><office:text>{body}</office:text></office:body>"
        f"</office:{root}>"
    ).encode()


def _odt_styles() -> bytes:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><office:document-styles {ODF_NAMESPACES}>'
        f"{ODT_FONTS}{ODT_NAMED_STYLES}</office:document-styles>"
    ).encode()


def _odt_manifest(entries: list[str], *, encrypted: bool = False, mime: str = ODT_MIME) -> bytes:
    encryption = (
        '<manifest:encryption-data manifest:checksum-type="SHA1/1K" manifest:checksum="AAAA">'
        '<manifest:algorithm manifest:algorithm-name="Blowfish CFB" '
        'manifest:initialisation-vector="AA"/>'
        '<manifest:key-derivation manifest:key-derivation-name="PBKDF2" '
        'manifest:iteration-count="1024" '
        'manifest:salt="AA"/></manifest:encryption-data>'
    )
    files = "".join(
        f'<manifest:file-entry manifest:full-path="{name}" manifest:media-type="text/xml">'
        f"{encryption if encrypted and name == 'content.xml' else ''}</manifest:file-entry>"
        for name in entries
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><manifest:manifest {_MANIFEST_NS} '
        f'manifest:version="1.3"><manifest:file-entry manifest:full-path="/" '
        f'manifest:media-type="{mime}"/>{files}</manifest:manifest>'
    ).encode()


def odt_package(
    content: bytes,
    *,
    extra: dict[str, bytes] | None = None,
    mime: str = ODT_MIME,
    encrypted: bool = False,
) -> bytes:
    """An OpenDocument package as the standard says: ``mimetype`` first and stored."""
    parts = {"content.xml": content, "styles.xml": _odt_styles(), **(extra or {})}
    entries = [
        ("mimetype", mime.encode()),
        ("META-INF/manifest.xml", _odt_manifest(list(parts), encrypted=encrypted, mime=mime)),
        *parts.items(),
    ]
    return _write_zip(entries, stored=frozenset({"mimetype"}))


def _odt(body: str) -> bytes:
    return odt_package(_odt_xml("document-content", body))


def _math_object(mathml: str) -> bytes:
    return f'<?xml version="1.0" encoding="UTF-8"?>{mathml}'.encode()


def _hostile_odt() -> dict[str, bytes]:
    doctype = (
        b'<?xml version="1.0"?><!DOCTYPE office:document-content [<!ENTITY a "aaaa">]>'
        + _odt_xml("document-content", "<text:p>&a;</text:p>")[
            len(b'<?xml version="1.0" encoding="UTF-8"?>') :
        ]
    )
    entities = (
        '<?xml version="1.0"?><!DOCTYPE d ['
        + '<!ENTITY l0 "ha">'
        + "".join(f'<!ENTITY l{n} "{("&l" + str(n - 1) + ";") * 10}">' for n in range(1, 10))
        + "]>"
    ).encode() + _odt_xml("document-content", "<text:p>&l9;</text:p>")[
        len(b'<?xml version="1.0" encoding="UTF-8"?>') :
    ]
    deep = "<text:span>" * 20_000 + "hondo" + "</text:span>" * 20_000
    many = "<text:p>x</text:p>" * 300_000
    bomb_body = "<text:p>ClearMD odt bomb fixture</text:p>"
    return {
        "doctype.odt": odt_package(doctype),
        "entities.odt": odt_package(entities),
        "deep.odt": _odt(f"<text:p>{deep}</text:p>"),
        "many_elements.odt": _odt(many),
        "object_outside.odt": odt_package(
            _odt_xml("document-content", ODT_FORMULAS_BODY),
            extra={"Object 1/content.xml": _math_object(MATHML_SUBSET)},
        ),
        "bomb.odt": _odt_zip_bomb(bomb_body),
    }


def _odt_zip_bomb(paragraph: str) -> bytes:
    """An .odt whose content.xml expands ~1000:1, like the docx zip bomb of feature 001."""
    head = _odt_xml("document-content", "")
    open_body, close_body = head.split(b"</office:text>")
    buffer = io.BytesIO()
    repeat = paragraph.encode()
    count = (BOMB_UNCOMPRESSED_BYTES - len(head)) // len(repeat)
    with zipfile.ZipFile(buffer, "w", compresslevel=9) as archive:
        archive.writestr(_zip_info("mimetype", zipfile.ZIP_STORED), ODT_MIME.encode())
        archive.writestr(
            _zip_info("META-INF/manifest.xml", zipfile.ZIP_DEFLATED), _odt_manifest(["content.xml"])
        )
        with archive.open(_zip_info("content.xml", zipfile.ZIP_DEFLATED), "w") as entry:
            entry.write(open_body)
            chunk = repeat * 4096
            for _ in range(count // 4096):
                entry.write(chunk)
            entry.write(b"</office:text>" + close_body)
    return buffer.getvalue()


def build_odt(destination: Path) -> dict[str, Path]:
    """Write the OpenDocument fixtures (generated; ``odt/real/`` holds LibreOffice's own files)."""
    report = _odt(ODT_REPORT_BODY)
    files: dict[str, bytes] = {
        "report.odt": report,
        "no_extension_odt": report,
        "merged.odt": _odt(ODT_MERGED_BODY),
        "revisions.odt": _odt(ODT_REVISIONS_BODY),
        "unknown.odt": _odt(ODT_UNKNOWN_BODY),
        "images.odt": odt_package(
            _odt_xml("document-content", ODT_IMAGES_BODY), extra={"Pictures/map.png": tiny_png()}
        ),
        "formulas.odt": odt_package(
            _odt_xml("document-content", ODT_FORMULAS_BODY),
            extra={
                "Object 1/content.xml": _math_object(MATHML_SUBSET),
                "Object 2/content.xml": _math_object(MATHML_SUM),
                "Object 3/content.xml": _math_object(MATHML_OUTSIDE),
            },
        ),
        "spreadsheet.odt": odt_package(_odt_xml("document-content", ""), mime=ODS_MIME),
        "encrypted.odt": odt_package(
            _odt_xml("document-content", "<text:p>x</text:p>"), encrypted=True
        ),
        "damaged.odt": report[: len(report) // 2],
        **{f"hostile/{name}": data for name, data in _hostile_odt().items()},
    }
    written = {}
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        written[name] = path
    return written


# --- HTML pages for article mode (feature 004) ---------------------------------------------------

HTML_DIR = Path(__file__).parent / "html"
_ARTICLE_PARAGRAPHS = [
    "La cuenca del río Magdalena recibe cada año más lluvias de las que sus bosques pueden "
    "retener, "
    "y los municipios ribereños llevan una década midiendo el cambio con estaciones comunitarias.",
    "Las estaciones registran precipitación, caudal y temperatura del agua; los datos se publican "
    "cada semana y cualquier persona puede descargarlos sin registrarse.",
    "Según el informe de este año, los picos de caudal llegan en promedio once días antes que hace "
    "veinte años, lo que adelanta también la temporada de siembra en las veredas cercanas.",
]
NEWS_HTML = (
    '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
    "<title>Estaciones comunitarias en el Magdalena | Diario de Prueba</title>"
    '<script>trackVisitor("fixture")</script></head><body>'
    '<nav class="menu"><a href="/">Inicio</a> <a href="/deportes">Deportes</a> '
    '<a href="/opinion">Opinión</a> MENU-FIXTURE</nav>'
    '<div class="cookies">Usamos cookies para mejorar tu experiencia. COOKIES-FIXTURE '
    "<button>Aceptar</button></div>"
    "<main><article>"
    "<h1>Estaciones comunitarias miden el cambio en el Magdalena</h1>"
    f"<p>{_ARTICLE_PARAGRAPHS[0]} Marcador: fixture-html-article.</p>"
    "<h2>Qué miden</h2>"
    f"<p>{_ARTICLE_PARAGRAPHS[1]} Los datos tienen <strong>licencia abierta</strong> y "
    '<em>formato CSV</em>; el código está en <a href="https://example.org/estaciones">el '
    "repositorio del proyecto</a>.</p>"
    "<ul><li>Precipitación diaria</li><li>Caudal del río<ul><li>en metros cúbicos por segundo</li>"
    "</ul></li><li>Temperatura del agua</li></ul>"
    "<ol><li>Instalar la estación</li><li>Calibrarla</li><li>Publicar los datos</li></ol>"
    '<figure><img src="https://cdn.example.org/estacion.jpg" alt="Una estación junto al río">'
    "<figcaption>Una estación en Honda.</figcaption></figure>"
    "<h2>Lo que dicen los datos</h2>"
    f"<p>{_ARTICLE_PARAGRAPHS[2]}</p>"
    "<blockquote><p>Ahora sabemos cuándo sembrar antes de que llegue el agua.</p></blockquote>"
    "<table><tr><th>Año</th><th>Días de adelanto</th></tr>"
    "<tr><td>2016</td><td>4</td></tr><tr><td>2026</td><td>11</td></tr></table>"
    "<pre><code>python analizar.py --estacion honda</code></pre>"
    "<p>El próximo informe se publica en marzo, con las estaciones nuevas de la cuenca alta y "
    "una comparación con los registros oficiales de los últimos treinta años.</p>"
    "</article>"
    '<aside class="related">Te puede interesar: ASIDE-FIXTURE <a href="/x">otra nota</a></aside>'
    "</main>"
    "<footer>Diario de Prueba © 2026 · Términos · Privacidad FOOTER-FIXTURE</footer>"
    "</body></html>"
)
NO_ARTICLE_HTML = (
    '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ingreso</title></head><body>'
    '<form><label>Usuario <input name="u"></label> <button>Entrar</button></form>'
    '<p><a href="/a">A</a> · <a href="/b">B</a></p> Marcador: fixture-html-no-article.'
    "</body></html>"
)
HOSTILE_HTML = (
    '<!DOCTYPE html><html><head><meta charset="utf-8">'
    "<title>Hostil &lt;img src=x&gt;</title></head>"
    "<body><article><h1>Un artículo hostil</h1>"
    "<p>Texto con &lt;img src=x onerror=alert(1)&gt; y ![x](http://evil.example/b.png) y "
    "[t](javascript:alert(1)) escritos como texto, suficiente para que haya un artículo que "
    "extraer y medir con cuidado. Marcador: fixture-html-hostile.</p>"
    '<p>Un <a href="javascript:alert(1)">enlace con script</a>, otro con '
    '<a href="javascript&#58;alert(1)">entidad</a> y uno '
    '<a href="//evil.example/x">sin esquema</a>, '
    "en un párrafo bastante largo para que el extractor lo considere parte del contenido.</p>"
    "<p># no es un título<br>- ni una lista<br>&gt; ni una cita<br>=== ni un subrayado, y "
    "aún más texto para que este párrafo cuente como contenido del artículo principal.</p>"
    '<script>steal()</script><iframe src="https://evil.example/frame"></iframe>'
    '<img src="https://evil.example/beacon.png" alt="baliza">'
    "</article></body></html>"
)


def build_html(destination: Path) -> dict[str, Path]:
    """Write the HTML pages of feature 004 and return them."""
    files = {
        "news.html": NEWS_HTML,
        "no_article.html": NO_ARTICLE_HTML,
        "hostile.html": HOSTILE_HTML,
    }
    written = {}
    for name, text in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written[name] = path
    return written


if __name__ == "__main__":
    built = [
        *build(DOCUMENTS_DIR).values(),
        *build_tex(TEX_DIR).values(),
        *build_odt(ODT_DIR).values(),
        *build_html(HTML_DIR).values(),
    ]
    for path in built:
        shown = path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path
        print(f"{path.stat().st_size:>8}  {shown}")
