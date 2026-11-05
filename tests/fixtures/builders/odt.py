"""The OpenDocument fixtures (feature 003)."""

from pathlib import Path

from builders.odt_bodies import (
    MATHML_OUTSIDE,
    MATHML_SUBSET,
    MATHML_SUM,
    ODT_FORMULAS_BODY,
    ODT_IMAGES_BODY,
    ODT_MERGED_BODY,
    ODT_REPORT_BODY,
    ODT_REVISIONS_BODY,
    ODT_UNKNOWN_BODY,
)
from builders.odt_package import _hostile_odt, _math_object, _odt, _odt_xml, odt_package
from builders.odt_styles import ODS_MIME
from builders.png import tiny_png

ODT_DIR = Path(__file__).parent.parent / "odt"


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
