"""The OpenDocument namespaces and styles (feature 003)."""

ODT_MIME = "application/vnd.oasis.opendocument.text"
ODS_MIME = "application/vnd.oasis.opendocument.spreadsheet"
ODF_NAMESPACES = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:xlink="http://www.w3.org/1999/xlink" '
    'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:math="http://www.w3.org/1998/Math/MathML" '
    'office:version="1.3"'
)
_MANIFEST_NS = 'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"'

ODT_FONTS = (
    "<office:font-face-decls>"
    '<style:font-face style:name="Liberation Mono" svg:font-family="&apos;Liberation Mono&apos;" '
    'style:font-pitch="fixed"/>'
    '<style:font-face style:name="Liberation Serif" svg:font-family="&apos;Liberation Serif&apos;" '
    'style:font-pitch="variable"/>'
    "</office:font-face-decls>"
)
# Named styles as LibreOffice writes them (styles.xml), parents included.
ODT_NAMED_STYLES = (
    "<office:styles>"
    '<style:style style:name="Standard" style:family="paragraph"/>'
    '<style:style style:name="Heading" style:family="paragraph" '
    'style:parent-style-name="Standard"/>'
    '<style:style style:name="Title" style:family="paragraph" style:parent-style-name="Heading"/>'
    '<style:style style:name="Subtitle" style:family="paragraph" '
    'style:parent-style-name="Heading"/>'
    '<style:style style:name="Quotations" style:family="paragraph" '
    'style:parent-style-name="Standard"/>'
    '<style:style style:name="Preformatted_20_Text" style:display-name="Preformatted Text" '
    'style:family="paragraph" style:parent-style-name="Standard"/>'
    '<style:style style:name="Emphasis" style:family="text">'
    '<style:text-properties fo:font-style="italic"/></style:style>'
    '<style:style style:name="Strong_20_Emphasis" style:display-name="Strong Emphasis" '
    'style:family="text"><style:text-properties fo:font-weight="bold"/></style:style>'
    '<style:style style:name="Source_20_Text" style:display-name="Source Text" style:family="text">'
    '<style:text-properties style:font-name="Liberation Mono"/></style:style>'
    "</office:styles>"
)
ODT_AUTOMATIC_STYLES = (
    "<office:automatic-styles>"
    '<style:style style:name="T1" style:family="text">'
    '<style:text-properties fo:font-weight="bold"/></style:style>'
    '<style:style style:name="T2" style:family="text">'
    '<style:text-properties fo:font-style="italic"/></style:style>'
    '<style:style style:name="T3" style:family="text">'
    '<style:text-properties style:text-underline-style="solid"/></style:style>'
    '<style:style style:name="T4" style:family="text">'
    '<style:text-properties style:text-line-through-style="solid"/></style:style>'
    '<style:style style:name="T5" style:family="text">'
    '<style:text-properties style:text-position="super 58%"/></style:style>'
    '<style:style style:name="T6" style:family="text">'
    '<style:text-properties style:text-position="sub 58%"/></style:style>'
    '<style:style style:name="T7" style:family="text">'
    '<style:text-properties style:font-name="Liberation Mono"/></style:style>'
    '<style:style style:name="T8" style:family="text" style:parent-style-name="Strong_20_Emphasis">'
    '<style:text-properties fo:font-style="italic"/></style:style>'
    '<style:style style:name="P1" style:family="paragraph" style:parent-style-name="Quotations"/>'
    '<style:style style:name="P2" style:family="paragraph" '
    'style:parent-style-name="Preformatted_20_Text"/>'
    '<text:list-style style:name="L1">'
    '<text:list-level-style-bullet text:level="1" text:bullet-char="•"/>'
    '<text:list-level-style-number text:level="2" style:num-format="1"/>'
    "</text:list-style>"
    '<text:list-style style:name="L2">'
    '<text:list-level-style-number text:level="1" style:num-format="1" text:start-value="3"/>'
    "</text:list-style>"
    "</office:automatic-styles>"
)
