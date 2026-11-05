"""HTML pages for article mode (feature 004)."""

from pathlib import Path

HTML_DIR = Path(__file__).parent.parent / "html"
_ARTICLE_PARAGRAPHS = [
    "La cuenca del río Magdalena recibe cada año más lluvias de las que sus bosques pueden "
    "retener, "
    "y los municipios ribereños llevan una década midiendo el cambio con estaciones comunitarias.",
    "Las estaciones registran precipitación, caudal y temperatura del agua; los datos se publican "
    "cada semana y cualquier persona puede descargarlos sin registrarse.",
    "Según el informe de este año, los picos de caudal llegan en promedio once días antes que hace "
    "veinte años, lo que adelanta también la temporada de siembra en las veredas cercanas.",
]
NEWS_HTML = (
    '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
    "<title>Estaciones comunitarias en el Magdalena | Diario de Prueba</title>"
    '<script>trackVisitor("fixture")</script></head><body>'
    '<nav class="menu"><a href="/">Inicio</a> <a href="/deportes">Deportes</a> '
    '<a href="/opinion">Opinión</a> MENU-FIXTURE</nav>'
    '<div class="cookies">Usamos cookies para mejorar tu experiencia. COOKIES-FIXTURE '
    "<button>Aceptar</button></div>"
    "<main><article>"
    "<h1>Estaciones comunitarias miden el cambio en el Magdalena</h1>"
    f"<p>{_ARTICLE_PARAGRAPHS[0]} Marcador: fixture-html-article.</p>"
    "<h2>Qué miden</h2>"
    f"<p>{_ARTICLE_PARAGRAPHS[1]} Los datos tienen <strong>licencia abierta</strong> y "
    '<em>formato CSV</em>; el código está en <a href="https://example.org/estaciones">el '
    "repositorio del proyecto</a>.</p>"
    "<ul><li>Precipitación diaria</li><li>Caudal del río<ul><li>en metros cúbicos por segundo</li>"
    "</ul></li><li>Temperatura del agua</li></ul>"
    "<ol><li>Instalar la estación</li><li>Calibrarla</li><li>Publicar los datos</li></ol>"
    '<figure><img src="https://cdn.example.org/estacion.jpg" alt="Una estación junto al río">'
    "<figcaption>Una estación en Honda.</figcaption></figure>"
    "<h2>Lo que dicen los datos</h2>"
    f"<p>{_ARTICLE_PARAGRAPHS[2]}</p>"
    "<blockquote><p>Ahora sabemos cuándo sembrar antes de que llegue el agua.</p></blockquote>"
    "<table><tr><th>Año</th><th>Días de adelanto</th></tr>"
    "<tr><td>2016</td><td>4</td></tr><tr><td>2026</td><td>11</td></tr></table>"
    "<pre><code>python analizar.py --estacion honda</code></pre>"
    "<p>El próximo informe se publica en marzo, con las estaciones nuevas de la cuenca alta y "
    "una comparación con los registros oficiales de los últimos treinta años.</p>"
    "</article>"
    '<aside class="related">Te puede interesar: ASIDE-FIXTURE <a href="/x">otra nota</a></aside>'
    "</main>"
    "<footer>Diario de Prueba © 2026 · Términos · Privacidad FOOTER-FIXTURE</footer>"
    "</body></html>"
)
NO_ARTICLE_HTML = (
    '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ingreso</title></head><body>'
    '<form><label>Usuario <input name="u"></label> <button>Entrar</button></form>'
    '<p><a href="/a">A</a> · <a href="/b">B</a></p> Marcador: fixture-html-no-article.'
    "</body></html>"
)
HOSTILE_HTML = (
    '<!DOCTYPE html><html><head><meta charset="utf-8">'
    "<title>Hostil &lt;img src=x&gt;</title></head>"
    "<body><article><h1>Un artículo hostil</h1>"
    "<p>Texto con &lt;img src=x onerror=alert(1)&gt; y ![x](http://evil.example/b.png) y "
    "[t](javascript:alert(1)) escritos como texto, suficiente para que haya un artículo que "
    "extraer y medir con cuidado. Marcador: fixture-html-hostile.</p>"
    '<p>Un <a href="javascript:alert(1)">enlace con script</a>, otro con '
    '<a href="javascript&#58;alert(1)">entidad</a> y uno '
    '<a href="//evil.example/x">sin esquema</a>, '
    "en un párrafo bastante largo para que el extractor lo considere parte del contenido.</p>"
    "<p># no es un título<br>- ni una lista<br>&gt; ni una cita<br>=== ni un subrayado, y "
    "aún más texto para que este párrafo cuente como contenido del artículo principal.</p>"
    '<script>steal()</script><iframe src="https://evil.example/frame"></iframe>'
    '<img src="https://evil.example/beacon.png" alt="baliza">'
    "</article></body></html>"
)


def build_html(destination: Path) -> dict[str, Path]:
    """Write the HTML pages of feature 004 and return them."""
    files = {
        "news.html": NEWS_HTML,
        "no_article.html": NO_ARTICLE_HTML,
        "hostile.html": HOSTILE_HTML,
    }
    written = {}
    for name, text in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written[name] = path
    return written
