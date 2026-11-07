"""Choose: the input rows and the output choice, and how a path is shown and compared."""

import os
from collections.abc import Sequence
from pathlib import Path

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter.icons import icon_for
from clearmd.frontend.presenter.models import InputRow, OutputChoice, OutputMode
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import Catalog, printable


def input_rows(inputs: Sequence[Path]) -> tuple[InputRow, ...]:
    rows = []
    for path in inputs:
        is_folder = path.is_dir()
        name = path.name or str(path)
        icon = icon_for(path, is_folder=is_folder)
        location = printable(str(path.parent))
        rows.append(InputRow(path, printable(name), location, is_folder, icon))
    return tuple(rows)


def output_choice(
    catalog: Catalog, output_folder: Path | None, settings: Settings, tool: Tool = Tool.CONVERT
) -> OutputChoice:
    remembered = settings.last_output_folder
    suggestion = Path(remembered) if remembered else None
    if output_folder is None:
        mode, label = OutputMode.NEXT_TO, catalog.text("gui.output.next_to_detail")
    else:
        mode = OutputMode.FOLDER
        label = catalog.text("gui.output.folder", path=printable(str(output_folder)))
    return OutputChoice(
        mode,
        output_folder,
        suggestion,
        label,
        settings.summary_format,
        settings.images,
        tool,
        settings.split_cut,
        settings.split_parts,
        settings.split_pages,
        settings.split_keep,
    )


def shown(path: Path, *, is_dir: bool = False) -> tuple[str, str]:
    """A path's name and folder as a view may show them: invisible and line-breaking
    characters escaped, as the CLI does (security review of 005)."""
    name = path.name + ("/" if is_dir else "")
    return printable(name), printable(str(path.parent))


def key(path: Path) -> str:
    """How two inputs are the same: the same absolute, normalized path."""
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))
