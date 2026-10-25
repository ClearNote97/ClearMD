"""What content detection may decide, depending on the file name.

A file without an extension is whatever its content says, plain text included (``README``). A file
with an extension ClearMD does not know is accepted only when its content is a real document (a docx
renamed ``report.dat``): plain text with an unknown extension — ``.tex``, ``.log``, ``.yaml`` — is
source or configuration, not a document to turn into Markdown.
"""

from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection
from clearmd.backend.use_cases.ports import FormatDetector

TEXT_LIKE = frozenset({FormatId.TXT, FormatId.CSV, FormatId.HTML, FormatId.IPYNB})


class DocumentsOnlyWithExtension:
    def __init__(self, content: FormatDetector) -> None:
        self._content = content

    def detect(self, path: Path) -> Detection | None:
        detection = self._content.detect(path)
        if detection is not None and path.suffix and detection.format in TEXT_LIKE:
            return None
        return detection
