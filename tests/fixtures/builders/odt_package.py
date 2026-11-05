"""Building OpenDocument packages by hand (feature 003)."""

import io
import zipfile

from builders.common import BOMB_UNCOMPRESSED_BYTES, _write_zip, _zip_info
from builders.odt_bodies import MATHML_SUBSET, ODT_FORMULAS_BODY
from builders.odt_styles import (
    _MANIFEST_NS,
    ODF_NAMESPACES,
    ODT_AUTOMATIC_STYLES,
    ODT_FONTS,
    ODT_MIME,
    ODT_NAMED_STYLES,
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
    # An embedded object's folder, as LibreOffice declares a formula's.
    files += "".join(
        f'<manifest:file-entry manifest:full-path="{name.rpartition("/")[0]}/" '
        'manifest:media-type="application/vnd.oasis.opendocument.formula"/>'
        for name in entries
        if name.endswith("/content.xml")
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
