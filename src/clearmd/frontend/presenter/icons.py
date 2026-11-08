"""Which file icon a row shows (ADR-0027): the asset's name under ``frontend/assets/icons``."""

from pathlib import Path

from clearmd.backend.schemas.formats import EXTENSIONS, MARKDOWN_EXTENSIONS, FormatId

FOLDER = "folder"
MARKDOWN = "markdown"
UNKNOWN = "unknown"
# Formats drawn with another format's icon (features 024, 029).
SHARED: dict[FormatId, str] = {
    FormatId.MARKDOWN: MARKDOWN,
    FormatId.EML: FormatId.TXT.value,
    FormatId.RTF: FormatId.DOCX.value,
    FormatId.SRT: FormatId.TXT.value,
    FormatId.VTT: FormatId.TXT.value,
}
ICONS: frozenset[str] = frozenset(
    {*(f.value for f in FormatId if f not in SHARED), FOLDER, MARKDOWN, UNKNOWN}
)


def icon_for(path: Path, *, is_folder: bool) -> str:
    """The icon of a folder, of Markdown (skipped), of a supported format, or the unknown one."""
    if is_folder:
        return FOLDER
    extension = path.suffix.lower()
    if extension in MARKDOWN_EXTENSIONS:
        return MARKDOWN
    found = EXTENSIONS.get(extension)
    return icon_of_format(found) if found is not None else UNKNOWN


def icon_of_format(format_id: FormatId) -> str:
    """The icon of a detected format (a file without an extension still gets its format's icon)."""
    return SHARED.get(format_id, format_id.value)
