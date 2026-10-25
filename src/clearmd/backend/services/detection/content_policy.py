"""Content detection runs only for files without an extension.

``escaneado`` says nothing about itself, so its content decides (plain text included: ``README``).
A file with an extension ClearMD does not know (``.tex`` until feature 002, ``.log``, ``.dat``) is
"unsupported format" without looking inside: what is not contemplated is not accepted.
"""

from pathlib import Path

from clearmd.backend.schemas.models import Detection
from clearmd.backend.use_cases.ports import FormatDetector


class ExtensionlessOnly:
    def __init__(self, content: FormatDetector) -> None:
        self._content = content

    def detect(self, path: Path) -> Detection | None:
        return None if path.suffix else self._content.detect(path)
