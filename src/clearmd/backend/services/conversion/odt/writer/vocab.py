"""The names the ODT subset knows: limits, field elements, and elements with nothing to show.

Every limit that bounds what a document may make ClearMD write lives here.
"""

MAX_NOTES = 10_000
# What a document may make ClearMD write beyond its own size (repeated formulas, repeated table
# cells): the same rule as the author's macros in .tex (ADR-0022), 4x the text plus 1 MiB.
GROWTH_FACTOR = 4
GROWTH_EXTRA = 1024**2
FORMULA_WORD = {"es": "Fórmula", "pt": "Fórmula", "fr": "Formule", "it": "Formula", "de": "Formel"}
MAX_SPACES = 256
MAX_UNKNOWN = 1000
MAX_LIST_LEVEL = 10  # LibreOffice's deepest; deeper lists are flattened into the tenth level

# Field elements: what matters is the text they show.
FIELDS = frozenset(
    {
        "text:page-number", "text:page-count", "text:page-continuation", "text:date", "text:time",
        "text:author-name", "text:author-initials", "text:creator", "text:title", "text:subject",
        "text:description", "text:keywords", "text:initial-creator", "text:creation-date",
        "text:creation-time", "text:modification-date", "text:modification-time",
        "text:print-date", "text:print-time", "text:printed-by", "text:editing-cycles",
        "text:editing-duration", "text:chapter", "text:file-name", "text:template-name",
        "text:sequence", "text:sequence-ref", "text:reference-ref", "text:bookmark-ref",
        "text:note-ref", "text:variable-get", "text:variable-set", "text:variable-input",
        "text:user-field-get", "text:user-field-input", "text:user-defined", "text:expression",
        "text:text-input", "text:placeholder", "text:conditional-text", "text:database-display",
        "text:sheet-name", "text:meta", "text:meta-field", "text:measure", "text:table-formula",
    }
)  # fmt: skip
# Inline elements with nothing to show (layout, anchors, marks, revisions handled apart).
DROPPED_INLINE = frozenset(
    {
        "text:soft-page-break", "text:bookmark", "text:bookmark-start", "text:bookmark-end",
        "text:reference-mark", "text:reference-mark-start", "text:reference-mark-end",
        "text:toc-mark", "text:toc-mark-start", "text:toc-mark-end", "text:alphabetical-index-mark",
        "text:alphabetical-index-mark-start", "text:alphabetical-index-mark-end",
        "text:user-index-mark", "text:user-index-mark-start", "text:user-index-mark-end",
        "text:bibliography-mark", "text:change", "text:change-start", "text:change-end",
        "office:annotation-end", "text:number", "text:hidden-paragraph",
    }
)  # fmt: skip
# Block elements with nothing to show: declarations, forms, generated indexes.
DROPPED_BLOCKS = frozenset(
    {
        "text:sequence-decls", "text:variable-decls", "text:user-field-decls",
        "text:dde-connection-decls", "office:forms", "text:soft-page-break",
        "text:table-of-content", "text:illustration-index", "text:table-index",
        "text:object-index", "text:user-index", "text:alphabetical-index", "text:bibliography",
        "table:table-columns", "table:table-column", "text:bookmark", "text:bookmark-start",
        "text:bookmark-end", "text:change", "text:change-start", "text:change-end",
        "text:hidden-paragraph",
    }
)  # fmt: skip
SPAN_LIKE = frozenset({"text:span"})
