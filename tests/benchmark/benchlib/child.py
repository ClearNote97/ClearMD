"""Measurement, child side: what runs inside the spawned process."""

import sys
import time
from collections.abc import Callable
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

import psutil

from benchlib.common import MIB


def _peak_rss_mib() -> float:
    if sys.platform == "win32":  # no resource module: the peak working set instead
        import psutil

        return float(psutil.Process().memory_info().peak_wset) / MIB
    import resource

    # ru_maxrss is in KiB on Linux.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _convert_with(engine: str, extension: str) -> Callable[[str], dict[str, Any]]:
    if engine == "article":
        from clearmd.backend.schemas.formats import FormatId
        from clearmd.backend.schemas.models import Detection, DetectionMethod
        from clearmd.backend.services.conversion.html import ArticleConverter

        article = ArticleConverter()
        page = Detection(FormatId.HTML, DetectionMethod.EXTENSION)

        def convert_article(path: str) -> dict[str, Any]:
            result = article.convert(Path(path), page, Path(path).with_suffix(".md"))
            notes = [note.kind.value for note in result.notes]
            return {"ok": True, "markdown_mib": len(result.markdown) / MIB, "notes": notes}

        return convert_article
    if engine == "odt":
        from clearmd.backend.schemas.formats import FormatId
        from clearmd.backend.schemas.models import Detection, DetectionMethod
        from clearmd.backend.services.conversion.odt import OdtConverter

        odt = OdtConverter()
        found = Detection(FormatId.ODT, DetectionMethod.EXTENSION)

        def convert_odt(path: str) -> dict[str, Any]:
            result = odt.convert(Path(path), found, Path(path).with_suffix(".md"))
            notes = [note.kind.value for note in result.notes]
            return {"ok": True, "markdown_mib": len(result.markdown) / MIB, "notes": notes}

        return convert_odt
    if engine == "tex":
        from clearmd.backend.schemas.formats import FormatId
        from clearmd.backend.schemas.models import Detection, DetectionMethod
        from clearmd.backend.services.conversion.tex import TexConverter

        tex = TexConverter()
        detection = Detection(FormatId.TEX, DetectionMethod.EXTENSION)

        def convert_tex(path: str) -> dict[str, Any]:
            result = tex.convert(Path(path), detection, Path(path).with_suffix(".md"))
            notes = [note.kind.value for note in result.notes]
            return {"ok": True, "markdown_mib": len(result.markdown) / MIB, "notes": notes}

        return convert_tex
    from markitdown import MarkItDown, StreamInfo

    markitdown = MarkItDown(enable_plugins=False)

    def convert_markitdown(path: str) -> dict[str, Any]:
        result = markitdown.convert_local(path, stream_info=StreamInfo(extension=extension))
        return {"ok": True, "markdown_mib": len(result.markdown) / MIB}

    return convert_markitdown


def _measure_child(connection: Connection, path: str, extension: str, engine: str) -> None:
    started = time.perf_counter()
    convert = _convert_with(engine, extension)
    ready = time.perf_counter() - started
    baseline = psutil.Process().memory_info().rss / MIB
    began = time.perf_counter()
    try:
        outcome = convert(path)
    except Exception as error:
        outcome = {"ok": False, "error": f"{type(error).__name__}: {str(error)[:200]}"}
    outcome.update(
        startup_s=ready,
        seconds=time.perf_counter() - began,
        baseline_mib=baseline,
        peak_mib=_peak_rss_mib(),
    )
    connection.send(outcome)


def _startup_child(connection: Connection) -> None:
    started = time.perf_counter()
    import magika
    from markitdown import MarkItDown

    MarkItDown(enable_plugins=False)
    ready = time.perf_counter() - started
    after_markitdown = psutil.Process().memory_info().rss / MIB
    magika.Magika()
    after_second_magika = psutil.Process().memory_info().rss / MIB
    connection.send(
        {
            "import_and_init_s": ready,
            "rss_after_markitdown_mib": after_markitdown,
            "second_magika_mib": after_second_magika - after_markitdown,
        }
    )
