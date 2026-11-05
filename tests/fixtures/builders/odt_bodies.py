"""The OpenDocument bodies and MathML snippets (feature 003)."""

ODT_REPORT_BODY = (
    '<text:p text:style-name="Title">Informe de prueba</text:p>'
    '<text:p text:style-name="Subtitle">Un subtítulo</text:p>'
    '<text:h text:outline-level="1">Introducción</text:h>'
    "<text:p>Texto con "
    '<text:span text:style-name="T1">negrita</text:span>, '
    '<text:span text:style-name="T2">itálica</text:span>, '
    '<text:span text:style-name="T3">subrayado</text:span>, '
    '<text:span text:style-name="T4">tachado</text:span>, '
    'm<text:span text:style-name="T5">2</text:span>, '
    'H<text:span text:style-name="T6">2</text:span>O, '
    '<text:span text:style-name="T7">código</text:span>, '
    '<text:span text:style-name="Emphasis">énfasis</text:span>, '
    '<text:span text:style-name="Strong_20_Emphasis">fuerte</text:span> y '
    '<text:span text:style-name="T8">ambos</text:span>. Marcador: fixture-odt-report.</text:p>'
    '<text:h text:outline-level="2">Listas y enlaces</text:h>'
    '<text:list text:style-name="L1">'
    "<text:list-item><text:p>uno</text:p></text:list-item>"
    "<text:list-item><text:p>dos</text:p>"
    "<text:list><text:list-item><text:p>anidado</text:p></text:list-item></text:list>"
    "</text:list-item>"
    "</text:list>"
    '<text:list text:style-name="L2">'
    "<text:list-item><text:p>tres</text:p></text:list-item>"
    "<text:list-item><text:p>cuatro</text:p></text:list-item>"
    "</text:list>"
    '<text:p>Un <text:a xlink:type="simple" xlink:href="https://example.org">enlace</text:a>'
    ' y una nota.<text:note text:id="ftn1" text:note-class="footnote">'
    "<text:note-citation>1</text:note-citation>"
    "<text:note-body><text:p>Una nota al pie.</text:p></text:note-body></text:note>"
    ' Y otra al final.<text:note text:id="edn1" text:note-class="endnote">'
    "<text:note-citation>i</text:note-citation>"
    "<text:note-body><text:p>Una nota final.</text:p></text:note-body></text:note></text:p>"
    '<text:h text:outline-level="2">Citas, código y espacios</text:h>'
    '<text:p text:style-name="P1">Una cita.</text:p>'
    '<text:p text:style-name="P2">def f(x):</text:p>'
    '<text:p text:style-name="P2"><text:s text:c="4"/>return x</text:p>'
    '<text:p>a<text:s text:c="3"/>b<text:tab/>c<text:line-break/>d</text:p>'
    '<text:p>Página <text:page-number text:select-page="current">7</text:page-number>'
    ' del <text:date text:date-value="2026-10-25">25/10/2026</text:date>.'
    '<text:hidden-text text:condition="" text:string-value="oculto" text:is-hidden="true"/>'
    '<text:bookmark text:name="b1"/><text:soft-page-break/></text:p>'
    '<text:hidden-paragraph text:condition="" text:is-hidden="true"/>'
    '<text:table-of-content text:name="Indice"><text:index-body>'
    "<text:p>Introducción ..... 1</text:p></text:index-body></text:table-of-content>"
    '<text:h text:outline-level="3">Tabla</text:h>'
    '<table:table table:name="T"><table:table-column table:number-columns-repeated="2"/>'
    "<table:table-header-rows><table:table-row>"
    "<table:table-cell><text:p>A</text:p></table:table-cell>"
    "<table:table-cell><text:p>B</text:p></table:table-cell>"
    "</table:table-row></table:table-header-rows>"
    "<table:table-row><table:table-cell><text:p>1</text:p></table:table-cell>"
    '<table:table-cell><text:p><text:span text:style-name="T1">2</text:span></text:p>'
    "</table:table-cell></table:table-row>"
    "</table:table>"
)
ODT_MERGED_BODY = (
    "<text:p>Antes. Marcador: fixture-odt-merged.</text:p>"
    "<table:table>"
    "<table:table-row>"
    '<table:table-cell table:number-columns-spanned="2"><text:p>Junta</text:p></table:table-cell>'
    "<table:covered-table-cell/>"
    "</table:table-row>"
    "<table:table-row><table:table-cell><text:p>a</text:p></table:table-cell>"
    "<table:table-cell><text:p>b</text:p></table:table-cell></table:table-row>"
    "</table:table>"
)
ODT_REVISIONS_BODY = (
    "<text:tracked-changes>"
    '<text:changed-region text:id="c1"><text:deletion><office:change-info>'
    "<dc:creator>Ana</dc:creator><dc:date>2026-10-25T10:00:00</dc:date></office:change-info>"
    "<text:p>borrado</text:p></text:deletion></text:changed-region>"
    "</text:tracked-changes>"
    '<text:p>Texto final<text:change text:change-id="c1"/>. Marcador: fixture-odt-revisions.'
    "<office:annotation><dc:creator>Luis</dc:creator><text:p>Un comentario</text:p>"
    "</office:annotation></text:p>"
)
ODT_UNKNOWN_BODY = (
    "<text:p>Antes. Marcador: fixture-odt-unknown.</text:p>"
    '<draw:custom-shape draw:name="Forma"><text:p>texto en forma</text:p></draw:custom-shape>'
    "<text:p><text:ruby><text:ruby-base>漢字</text:ruby-base></text:ruby> fin</text:p>"
)
ODT_IMAGES_BODY = (
    "<text:p>Marcador: fixture-odt-images.</text:p>"
    '<text:p><draw:frame draw:name="Imagen1" text:anchor-type="paragraph" svg:width="2cm" '
    'svg:height="2cm"><draw:image xlink:href="Pictures/map.png" xlink:type="simple"/>'
    "<svg:title>Mapa de la región</svg:title></draw:frame></text:p>"
    '<text:p><draw:frame draw:name="Imagen2"><draw:image xlink:href="Pictures/map.png"/>'
    "<svg:desc>Una descripción</svg:desc></draw:frame></text:p>"
    '<text:p><draw:frame draw:name="Logo"><draw:image xlink:href="Pictures/map.png"/>'
    "</draw:frame></text:p>"
)
MATHML_SUBSET = (
    '<math:math xmlns:math="http://www.w3.org/1998/Math/MathML" display="block"><math:semantics>'
    "<math:mrow><math:mfrac><math:mi>a</math:mi><math:mi>b</math:mi></math:mfrac>"
    "<math:mo>+</math:mo><math:msup><math:mi>x</math:mi><math:mn>2</math:mn></math:msup>"
    "<math:mo>+</math:mo><math:msqrt><math:mi>y</math:mi></math:msqrt>"
    "<math:mo>+</math:mo><math:mi>α</math:mi></math:mrow>"
    '<math:annotation encoding="StarMath 5.0">{a over b} + x^2 + sqrt{y} + %alpha</math:annotation>'
    "</math:semantics></math:math>"
)
MATHML_SUM = (
    '<math:math xmlns:math="http://www.w3.org/1998/Math/MathML"><math:semantics>'
    "<math:mrow><math:munderover><math:mo>∑</math:mo>"
    "<math:mrow><math:mi>i</math:mi><math:mo>=</math:mo><math:mn>1</math:mn></math:mrow>"
    "<math:mi>n</math:mi></math:munderover><math:mi>i</math:mi></math:mrow>"
    '<math:annotation encoding="StarMath 5.0">sum from{i=1} to{n} i</math:annotation>'
    "</math:semantics></math:math>"
)
MATHML_OUTSIDE = (
    '<math:math xmlns:math="http://www.w3.org/1998/Math/MathML"><math:semantics>'
    '<math:mrow><math:menclose notation="box"><math:mi>z</math:mi></math:menclose></math:mrow>'
    '<math:annotation encoding="StarMath 5.0">boxed z</math:annotation>'
    "</math:semantics></math:math>"
)
ODT_FORMULAS_BODY = (
    "<text:p>Marcador: fixture-odt-formulas.</text:p>"
    '<text:p><draw:frame draw:name="F1" text:anchor-type="as-char">'
    '<draw:object xlink:href="./Object 1" xlink:type="simple"/></draw:frame></text:p>'
    '<text:p>En línea <draw:frame draw:name="F2" text:anchor-type="as-char">'
    '<draw:object xlink:href="./Object 2"/></draw:frame> y fin.</text:p>'
    '<text:p>Fuera: <draw:frame draw:name="F3" text:anchor-type="as-char">'
    '<draw:object xlink:href="./Object 3"/></draw:frame>.</text:p>'
    '<text:p>Afuera: <draw:frame draw:name="F4" text:anchor-type="as-char">'
    '<draw:object xlink:href="../escape"/></draw:frame>.</text:p>'
)
