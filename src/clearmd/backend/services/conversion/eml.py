"""An e-mail (.eml) to Markdown (feature 029, ADR-0049): its subject as the title, who sent it,
to whom and when, its text, and the names of its attachments (never their contents, which stay in
the e-mail). An HTML-only body is written by ClearMD's own page writer, in memory. Standard
library email parser."""

from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.services.conversion.html.page import page_tree
from clearmd.backend.services.conversion.html.render import ArticleRenderer
from clearmd.backend.services.conversion.safe_files import NotARegularFile, read_regular_file
from clearmd.backend.services.conversion.xmltree import Element

MAX_BYTES = 64 * 1024**2
HEADERS = ("From", "To", "Cc", "Date")


def _cell(value: str) -> str:
    return " ".join(value.split()).replace("|", "\\|")


class EmlConverter:
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
        body, notes = self._body(message)
        lines += ["", body.strip()] if body.strip() else []
        attachments = [part.get_filename() for part in message.iter_attachments()]
        names = [_cell(name) for name in attachments if name]
        if names:
            lines += ["", "**Attachments:** " + ", ".join(names)]
        return ConversionResult("\n".join(lines).strip() + "\n", notes)

    def _body(self, message: EmailMessage) -> tuple[str, tuple[ConversionNote, ...]]:
        part = message.get_body(preferencelist=("plain", "html"))
        if part is None:
            return "", ()
        content = part.get_content()
        if part.get_content_type() == "text/plain":
            return str(content), ()
        # An HTML-only body is written in memory by ClearMD's own page writer: never a file in the
        # system's temporary folder (audit v3, B2-07), never a page's markup or remote images.
        tree, _ = page_tree(str(content))
        renderer = ArticleRenderer(language="en", source_size=len(str(content)))
        return renderer.document(tree or Element("body")), renderer.notes()
