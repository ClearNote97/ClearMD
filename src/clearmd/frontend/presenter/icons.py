"""Which file icon a row shows (ADR-0027): the asset's name under ``frontend/assets/icons``."""

from pathlib import Path

from clearmd.backend.schemas.formats import EXTENSIONS, MARKDOWN_EXTENSIONS, FormatId

FOLDER = "folder"
MARKDOWN = "markdown"
UNKNOWN = "unknown"
ICONS: frozenset[str] = frozenset(
    {*(f.value for f in FormatId if f is not FormatId.MARKDOWN), FOLDER, MARKDOWN, UNKNOWN}
)


def icon_for(path: Path, *, is_folder: bool) -> str:
    """The icon of a folder, of Markdown (skipped), of a supported format, or the unknown one."""
    if is_folder:
        return FOLDER
    extension = path.suffix.lower()
    if extension in MARKDOWN_EXTENSIONS:
        return MARKDOWN
    found = EXTENSIONS.get(extension)
    return found.value if found is not None else UNKNOWN


def icon_of_format(format_id: FormatId) -> str:
    """The icon of a detected format (a file without an extension still gets its format's icon)."""
    return MARKDOWN if format_id is FormatId.MARKDOWN else format_id.value
