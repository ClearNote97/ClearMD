"""Error codes and skip reasons. Each maps to catalog keys with a human message (ADR-0013)."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Why a planned conversion failed."""

    UNSUPPORTED_FORMAT = "unsupported_format"
    PASSWORD_PROTECTED = "password_protected"
    CORRUPT_FILE = "corrupt_file"
    CONVERSION_FAILED = "conversion_failed"
    PERMISSION_DENIED = "permission_denied"
    TIMED_OUT = "timed_out"
    OUT_OF_MEMORY = "out_of_memory"
    WORKER_CRASHED = "worker_crashed"

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
    UNSAFE_ARCHIVE = "unsafe_archive"
    UNSUPPORTED_FORMAT = "unsupported_format"
    EXISTING_OUTPUT = "existing_output"

    @property
    def key(self) -> str:
        return f"skip.{self.value}"


class ConversionError(Exception):
    """A conversion failed for a known reason; ``detail`` is technical and goes to the summary."""

    def __init__(self, code: ErrorCode, detail: str = "") -> None:
        super().__init__(f"{code.value}: {detail}" if detail else code.value)
        self.code = code
        self.detail = detail


class Cancelled(Exception):
    """The user cancelled while a file was being converted."""
