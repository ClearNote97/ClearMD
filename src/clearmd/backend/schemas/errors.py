"""Error codes and skip reasons. Each maps to catalog keys with a human message (ADR-0013)."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Why a planned conversion failed."""

    UNSUPPORTED_FORMAT = "unsupported_format"
    PASSWORD_PROTECTED = "password_protected"
    CORRUPT_FILE = "corrupt_file"
    CONVERSION_FAILED = "conversion_failed"
    # The output folder cannot be written: every file of that ClearMD_Output fails.
    PERMISSION_DENIED = "permission_denied"
    # This one source cannot be opened (locked by another program, no permission, not a file).
    SOURCE_UNREADABLE = "source_unreadable"
    # This one result could not be saved (disk full, name too long, a folder in the way...).
    WRITE_FAILED = "write_failed"
    TIMED_OUT = "timed_out"
    OUT_OF_MEMORY = "out_of_memory"
    WORKER_CRASHED = "worker_crashed"
    # Split by words: a PDF without any text (scanned) has nothing to measure (feature 024).
    NOTHING_TO_MEASURE = "nothing_to_measure"
    # Merge: fewer than two documents could be joined, so nothing was written (feature 026).
    NOTHING_TO_MERGE = "nothing_to_merge"
    # Split: a text, CSV or Markdown file with nothing in it (audit 2026-11-08, B1-07b).
    EMPTY_FILE = "empty_file"
    # The conversion gave no text (a scanned PDF, an empty presentation): never "converted", the
    # owner's empty-file rule applied to the result (audit v4, B1-03).
    EMPTY_RESULT = "empty_result"

    @property
    def message_key(self) -> str:
        return f"error.{self.value}.message"

    @property
    def action_key(self) -> str:
        return f"error.{self.value}.action"


class SkipReason(StrEnum):
    """Why a file or folder was left out of the plan, or an existing output kept."""

    OUTPUT_FOLDER = "output_folder"
    SYMLINK = "symlink"
    HIDDEN = "hidden"
    LOCK_FILE = "lock_file"
    TOO_LARGE = "too_large"
    ALREADY_MARKDOWN = "already_markdown"
    ZIP_ARCHIVE = "zip_archive"
    ARCHIVE_TOO_LARGE = "archive_too_large"  # the checks of a ZIP-based file (ADR-0015)
    ARCHIVE_RATIO = "archive_ratio"
    ARCHIVE_ENTRIES = "archive_entries"
    UNSUPPORTED_FORMAT = "unsupported_format"
    EXISTING_OUTPUT = "existing_output"
    UNREADABLE = "unreadable"
    TOO_MUCH_MEMORY = "too_much_memory"
    TOO_MUCH_MEMORY_FOR_ARTICLE = "too_much_memory_for_article"  # HTML in article mode (004)
    TOO_DEEP = "too_deep"
    NOT_SPLITTABLE = "not_splittable"  # Split takes PDF and Markdown (features 023, 024)
    CUT_NOT_FOR_MARKDOWN = "cut_not_for_markdown"  # "every N pages" means nothing for Markdown
    NO_PAGES_TO_CUT = "no_pages_to_cut"  # text and CSV have no pages (feature 027)
    CUT_BY_SHEETS = "cut_by_sheets"  # Excel is cut by whole sheets only (feature 027)
    NOT_FOR_PDF_MERGE = "not_for_pdf_merge"  # one PDF can only be made of PDFs (feature 026)
    # A file chosen again through a folder that holds it: used once (audit 2026-11-08, B1-11).
    ALREADY_INCLUDED = "already_included"
    OLD_OFFICE = "old_office"  # .doc, .xls, .ppt: saved again as .docx... (audit, C-2)
    IMAGE = "image"  # a picture: ClearMD reads no text inside images

    @property
    def key(self) -> str:
        return f"skip.{self.value}"


class ConversionError(Exception):
    """A conversion failed for a known reason; ``detail`` is technical and goes to the summary."""

    def __init__(self, code: ErrorCode, detail: str = "", *, limit: float | None = None) -> None:
        super().__init__(f"{code.value}: {detail}" if detail else code.value)
        self.code = code
        self.detail = detail
        self.limit = limit  # the limit a stop reached: seconds (time) or bytes (memory)


class Cancelled(Exception):
    """The user cancelled while a file was being converted."""
