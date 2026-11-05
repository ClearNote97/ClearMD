r"""LaTeX nodes → Markdown: the supported subset of spec 002, everything else kept and reported.

Text-mode nodes follow the subset table; math is re-serialized as written (comments dropped, the
author's macros expanded); a command that neither this renderer nor pylatexenc's ``latex2text``
knows is written back as is and listed in a note. A source pylatexenc cannot read at all (deep
nesting) is kept whole as a LaTeX code block, with a note: a file never fails as a whole (AC-21).
"""

import re
from collections.abc import Callable

from clearmd.backend.schemas.models import ConversionResult
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.markdown_out import MARK, fence_for, neutralize
from clearmd.backend.services.conversion.tex.images import name_only_image
from clearmd.backend.services.conversion.tex.macros import (
    build_expander,
    collect_definitions,
    opens_or_closes_an_environment,
    substitute_structural,
)
from clearmd.backend.services.conversion.tex.parsing import Unparseable, make_context, parse
from clearmd.backend.services.conversion.tex.writer import (
    ImageHandler,
    Renderer,
    is_spanish,
    top_level,
)

# "file, line N" for a position of the source (documents made of several files).
Locator = Callable[[int], str]


def _kept_as_latex(text: str, cause: str, refused: tuple[NoteItem, ...]) -> ConversionResult:
    fence = fence_for(text)
    markdown = f"{fence}latex\n{text.strip(chr(10))}\n{fence}\n"
    notes = [
        ConversionNote(NoteKind.PARSE_RECOVERED, (NoteItem(cause, NoteReason.KEPT_AS_LATEX.value),))
    ]
    if refused:
        notes.insert(0, ConversionNote(NoteKind.INCLUDE_NOT_FOLLOWED, refused))
    return ConversionResult(markdown, tuple(notes))


def render_source(
    text: str,
    *,
    image: ImageHandler | None = None,
    locate: Locator | None = None,
    refused: tuple[NoteItem, ...] = (),
) -> ConversionResult:
    """Markdown and notes for a whole LaTeX source (its includes already in place).

    Whatever happens inside, the file is converted: at worst kept whole as LaTeX (AC-21).
    """
    # The document can never forge ClearMD's own block marks; every line ends with "\n" (a lone
    # "\r" is a line ending to CommonMark too).
    text = re.sub(r"\r\n?", "\n", text.replace(MARK, ""))
    try:
        nodes, error = parse(text, make_context())
        macros, again = build_expander(nodes, len(text))
        if macros is not None:
            substituted = substitute_structural(text, nodes, macros)
            if substituted is not None:
                text, nodes, original = substituted
                if locate is not None:
                    locate = _through(locate, original)
                remaining = {
                    name: definition
                    for name, definition in collect_definitions(nodes).items()
                    if not opens_or_closes_an_environment(definition)  # uses already in place
                }
                macros.redefine(remaining)
                again = True
            if again:
                nodes, error = parse(text, macros.context)
        renderer = Renderer(
            level=top_level(nodes, macros.definitions if macros is not None else None),
            spanish=is_spanish(nodes),
            image=image,
            macros=macros,
            known_refused=frozenset(item.subject for item in refused),
            listed=len(refused),
        )
        markdown = neutralize(renderer.document(nodes))
    except MemoryError:
        raise  # the worker reports it as out of memory
    except (Unparseable, RecursionError) as problem:
        cause = str(problem) if isinstance(problem, Unparseable) else type(problem).__name__
        return _kept_as_latex(text, cause, refused)
    except Exception as problem:  # a converter bug must not lose a thesis (AC-21)
        return _kept_as_latex(text, type(problem).__name__, refused)
    notes = list(renderer.state.notes())
    not_followed = (*refused, *renderer.state.refused)
    if not_followed:
        notes.append(ConversionNote(NoteKind.INCLUDE_NOT_FOLLOWED, not_followed))
    recovered = [NoteItem(problem) for problem in renderer.state.recovered]
    if error is not None:
        place = f"{locate(error.position)}: " if locate is not None else ""
        recovered.insert(0, NoteItem(place + error.message))
    if recovered:
        notes.append(ConversionNote(NoteKind.PARSE_RECOVERED, tuple(recovered)))
    return ConversionResult(markdown, tuple(notes))


def _through(locate: Locator, original: Callable[[int], int]) -> Locator:
    return lambda position: locate(original(position))


def render_latex(text: str) -> ConversionResult:
    """Convert one LaTeX source on its own (no includes followed: see ``convert_document``)."""
    return render_source(text, image=name_only_image)
