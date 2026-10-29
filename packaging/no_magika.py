# PyInstaller runtime hook: the executables ship without magika and onnxruntime (feature 010,
# ADR-0032). markitdown imports magika when it loads, but only uses it in MarkItDown(), which
# ClearMD never builds: its own signatures detect content. This empty stand-in satisfies the import.
import sys
import types


class _NotShipped:
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError("magika is not in ClearMD's executables")


_stub = types.ModuleType("magika")
_stub.Magika = _NotShipped  # type: ignore[attr-defined]
sys.modules.setdefault("magika", _stub)
