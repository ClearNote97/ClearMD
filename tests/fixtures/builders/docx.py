"""The docx fixtures: a minimal document and a zip bomb."""

import io
import zipfile

from builders.common import BOMB_UNCOMPRESSED_BYTES, MARKERS, _write_zip, _zip_info

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
