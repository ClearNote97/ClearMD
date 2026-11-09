"""Text, CSV and Excel split into parts of their own format (feature 027, ADR-0047): cut in the
worker, written here; each part's Markdown too when asked."""

from dataclasses import replace

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import PlannedConversion
from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.schemas.split import SplitSpec
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.output_files import (
    atomic_write,
    atomic_write_bytes,
    remove_regular_file,
)
from clearmd.backend.use_cases.part_stage import PartStage
from clearmd.backend.use_cases.ports import ConversionRunner, PageCutter
from clearmd.backend.use_cases.split_names import part_name
from clearmd.backend.use_cases.split_notes import over_size

OWN_FORMAT_PARTS = frozenset({FormatId.TXT, FormatId.CSV, FormatId.XLSX})


def _parts(
    item: PlannedConversion, spec: SplitSpec, cutter: PageCutter, cancel: CancelToken
) -> tuple[list[bytes | str], tuple[int, ...]]:
    if item.detection.format is FormatId.XLSX:
        return list(cutter.xlsx_parts(item, spec.size, cancel)), ()
    kind = item.detection.format.value
    texts, over = cutter.text_parts(item, kind, spec.cut.value, spec.size, cancel)
    return list(texts), over


def split_file(
    item: PlannedConversion,
    spec: SplitSpec,
    runner: ConversionRunner,
    cutter: PageCutter,
    cancel: CancelToken,
    stage: PartStage,
) -> tuple[int, tuple[ConversionNote, ...]]:
    parts, over = _parts(item, spec, cutter, cancel)
    if not parts:
        raise ConversionError(ErrorCode.NOTHING_TO_MEASURE, "an empty file")
    suffix = "." + item.detection.format.value
    notes: list[ConversionNote] = []
    for index, data in enumerate(parts, start=1):
        name = part_name(spec, item.target.name, index, len(parts))
        path = stage.at(item.target / f"{name}{suffix}")
        if isinstance(data, bytes):
            atomic_write_bytes(path, data, inside=item.output_root)
        else:  # LF endings, UTF-8: the line breaks themselves are kept
            atomic_write(path, data, inside=item.output_root)
        if spec.keep.markdown:
            part = replace(
                item, source=path, target=stage.at(item.target / f"{name}.md"), split=None
            )
            result = runner.convert(part, cancel)
            atomic_write(part.target, result.markdown, inside=item.output_root)
            notes.extend(result.notes)
            if not spec.keep.original:
                remove_regular_file(path, inside=item.output_root)
    return len(parts), tuple(dict.fromkeys(notes)) + over_size(over)
