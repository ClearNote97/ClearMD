"""Frames: an image as a placeholder or link, a formula as LaTeX, a text box as its text."""

from clearmd.backend.services.conversion.inline import LINE_BREAK
from clearmd.backend.services.conversion.markdown_out import escape_text, link_target
from clearmd.backend.services.conversion.odt.writer.formulas import formula_markdown
from clearmd.backend.services.conversion.odt.writer.paragraphs import (
    hidden,
    own_paragraphs,
    paragraph_props,
)
from clearmd.backend.services.conversion.odt.writer.state import Writer
from clearmd.backend.services.conversion.xmltree import Element


def frame_markdown(w: Writer, frame: Element) -> str:
    """An image as a placeholder, a formula as LaTeX, a text box as its text."""
    formula = frame.find("draw:object")
    if formula is not None:  # its draw:image is LibreOffice's replacement picture
        shown = formula_markdown(w, formula, display=False)
        if shown is not None:
            return shown
        # Not a formula (a chart, another embedded object): a placeholder, like an image.
    if formula is not None or frame.find("draw:image") is not None:
        title = frame.find("svg:title")
        description = frame.find("svg:desc")
        label = next(
            (
                " ".join(text.split())
                for text in (
                    title.text() if title is not None else "",
                    description.text() if description is not None else "",
                    frame.get("draw:name"),
                )
                if text.strip()
            ),
            "",
        )
        image = frame.find("draw:image")
        if image is not None and w.state.pictures is not None and formula is None:
            link = w.state.pictures(image.get("xlink:href"))
            if link is not None:
                return f"![{escape_text(label)}]({link_target(link)})"
        else:  # a placeholder; a picture the images folder left out is counted there
            w.state.counts.images += 1
        shown = f"{w.state.image_word}: {label}" if label else w.state.image_word
        return f"*{escape_text(shown)}*"
    box = frame.find("draw:text-box")
    if box is not None:  # its lists and tables too; never glued to the text around it
        visible = [p for p in own_paragraphs(w, box) if not hidden(w, p)]
        texts = [w.inline(p, paragraph_props(w, p)).replace(LINE_BREAK, " ") for p in visible]
        joined = " ".join(text for text in texts if text)
        return f" {joined} " if joined else ""
    w.state.note_unknown(frame.tag)
    return escape_text(" ".join(frame.text().split()))
