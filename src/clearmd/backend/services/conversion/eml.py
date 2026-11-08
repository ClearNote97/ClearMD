"""An e-mail (.eml) to Markdown (feature 029, ADR-0049): its subject as the title, who sent it,
to whom and when, its text, and the names of its attachments (never their contents, which stay in
the e-mail). An HTML-only body goes through the HTML converter. Standard library email parser."""

import tempfile
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.services.conversion.registry import DocumentConverter
from clearmd.backend.services.conversion.safe_files import NotARegularFile, read_regular_file

MAX_BYTES = 64 * 1024**2
HEADERS = ("From", "To", "Cc", "Date")


def _cell(value: str) -> str:
    return " ".join(value.split()).replace("|", "\\|")


class EmlConverter:
    def __init__(self, html: DocumentConverter) -> None:
        self._html = html

    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        try:
            data = read_regular_file(source, MAX_BYTES)
        except (OSError, NotARegularFile) as error:
            raise ConversionError(ErrorCode.SOURCE_UNREADABLE, str(error)) from error
        message = BytesParser(policy=policy.default).parsebytes(data)
        if not isinstance(message, EmailMessage) or not message.keys():
            raise ConversionError(ErrorCode.CORRUPT_FILE, "not an e-mail message")
        lines = [f"# {_cell(str(message.get('Subject', '')) or source.stem)}", ""]
        for name in HEADERS:
            if message.get(name):
                lines.append(f"- **{name}:** {_cell(str(message[name]))}")
        body, notes = self._body(message, target)
        lines += ["", body.strip()] if body.strip() else []
        attachments = [part.get_filename() for part in message.iter_attachments()]
        names = [_cell(name) for name in attachments if name]
        if names:
            lines += ["", "**Attachments:** " + ", ".join(names)]
        return ConversionResult("\n".join(lines).strip() + "\n", notes)

    def _body(self, message: EmailMessage, target: Path) -> tuple[str, tuple[ConversionNote, ...]]:
        part = message.get_body(preferencelist=("plain", "html"))
        if part is None:
            return "", ()
        content = part.get_content()
        if part.get_content_type() == "text/plain":
            return str(content), ()
        with tempfile.TemporaryDirectory(prefix="clearmd-eml-") as folder:
            page = Path(folder) / "body.html"
            page.write_text(str(content), encoding="utf-8")
            result = self._html.convert(
                page, Detection(FormatId.HTML, DetectionMethod.EXTENSION), target
            )
        return result.markdown, result.notes
