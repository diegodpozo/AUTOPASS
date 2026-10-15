"""Guard: las librerias de CDN se cargan POR PAGINA, no para todas.

Estado previo (hasta v9.34.95): base.html cargaba 5 librerias en TODAS las
vistas (Leaflet, Chart.js, Flatpickr, qrcodejs y html2canvas) aunque cada una
la use una minoria de paginas:

  - Leaflet:     index (mapa), perfil (mapa del portal), dashboard (pickers).
  - Chart.js:    dashboard (tabs metricas/finance), estadisticas-ocr.
  - Flatpickr:   perfil (form de reserva), dashboard (alta de reserva).
  - qrcodejs:    perfil (pase digital), dashboard (tour del admin).
  - html2canvas: perfil (compartir/imprimir el pase).
  - Font Awesome: SI es global (fas/far/fab en casi todas las vistas) y se
    queda en base.html.

El costo de tenerlas globales era concreto: /privacidad, /terminos, /contacto,
/monitoreo, /reset-password y /nuestra-red bajaban ~5 recursos de CDN (y sus
dependencias) sin usarlos.

Desde v9.34.96 el catalogo vive en un solo lugar (components/cdn_libs.html) con
dos macros, y cada vista declara lo suyo:

    {% from "components/cdn_libs.html" import cdn_head, cdn_scripts %}
    {% block extra_head %}{{ cdn_head(['leaflet']) }}{% endblock %}
    {% block extra_scripts %}{{ cdn_scripts(['leaflet']) }}{% endblock %}

Este guard no abre un navegador: verifica el invariante en el marcado.

Uso:
  python _tools/check_cdn_per_page.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"
MACRO = TPL / "components/cdn_libs.html"
BASE = TPL / "base.html"

# Una URL de cada libreria (lo suficiente para reconocerla en cualquier tag).
LIB_URLS = {
    "leaflet": r"unpkg\.com/leaflet@",
    "chart": r"jsdelivr\.net/npm/chart\.js",
    "flatpickr": r"flatpickr",
    "qrcode": r"qrcodejs/",
    "capture": r"html2canvas/",
}
FONT_AWESOME = r"font-awesome/"

# Que declara cada vista, y por que (el consumidor real en JS):
#   index.html        -> static/js/modules/landing-map*.js         (L.map)
#   perfil.html       -> landing-map*.js, reservas-form.js, profile.js, reservas-pass.js, tour.js
#   dashboard.html    -> dashboard-{admin-branches-crud,promotions,finance,informes,reservations}.js, admin-tour.js
#   estadisticas_ocr  -> static/js/modules/estadisticas-ocr.js (+ chart-window.js)
ESPERADO = {
    "index.html": {"leaflet"},
    "perfil.html": {"leaflet", "flatpickr", "qrcode", "capture"},
    "dashboard.html": {"leaflet", "chart", "flatpickr", "qrcode"},
    "estadisticas_ocr.html": {"chart"},
}

# Paginas que extienden base.html declaradas en el diccionario del macro.
# Cualquier otra pagina que extienda base.html no debe declarar NINGUNA.
# instalar.html es la excepcion documentada: es una pagina suelta (no extiende
# base.html) que trae su propio qrcodejs para el QR de instalacion.
EXCEPCIONES = {"instalar.html": {"qrcode"}}

URL_RE = re.compile(r"https?://[^\s\"'>]+")
ENTRADA_RE = re.compile(r"'(\w+)':\s*\{(.*?)\}", re.S)
LISTA_RE = re.compile(r"'(\w+)':\s*\[(.*?)\]", re.S)
NOMBRES_RE = re.compile(r"'([^']+)'|\"([^\"]+)\"")
LLAMADA_RE = re.compile(r"\bcdn_(head|scripts)\s*\(\s*\[(.*?)\]\s*\)", re.S)
BLOQUE_RE = re.compile(r"\{%-?\s*block\s+(extra_head|extra_scripts)\s*-?%\}(.*?)\{%-?\s*endblock",
                       re.S)
EXTENDS_RE = re.compile(r"\{%\s*extends\s*\"([^\"]+)\"")
IMPORT_RE = re.compile(r"\{%-?\s*from\s*\"components/cdn_libs\.html\"\s*import\s*([^%]+)%\}")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def catalogo():
    """El diccionario lib -> (css, js) del macro (fuente unica de verdad)."""
    texto = MACRO.read_text(encoding="utf-8")
    libs = {}
    for m in ENTRADA_RE.finditer(texto):
        nombre, cuerpo = m.group(1), m.group(2)
        css = LISTA_RE.search(cuerpo)
        # El 'css' aparece primero; para 'js' se busca la segunda lista.
        listas = LISTA_RE.findall(cuerpo)
        valores = {}
        for clave, contenido in listas:
            valores[clave] = [a or b for a, b in NOMBRES_RE.findall(contenido)]
        libs[nombre] = (valores.get("css", []), valores.get("js", []))
        if css is None:
            pass
    return libs


def lib_de_url(url: str):
    for nombre, pat in LIB_URLS.items():
        if re.search(pat, url):
            return nombre
    return None


def bloque_en(texto: str, pos: int):
    """En que block de Jinja cae esta posicion (para exigir head vs scripts)."""
    for m in BLOQUE_RE.finditer(texto):
        if m.start(2) <= pos < m.end(2):
            return m.group(1)
    return None


def declarado(texto: str):
    """(head, scripts, ubicaciones) declarados con los macros."""
    head, scripts, ubicaciones, errores = set(), set(), [], []
    for m in LLAMADA_RE.finditer(texto):
        cual, contenido = m.group(1), m.group(2)
        nombres = {a or b for a, b in NOMBRES_RE.findall(contenido)}
        if not nombres:
            errores.append("cdn_%s([]) vacio" % cual)
        ubicaciones.append((cual, nombres, bloque_en(texto, m.start())))
    for cual, nombres, bloque in ubicaciones:
        if cual == "head":
            head |= nombres
        else:
            scripts |= nombres
        esperado = "extra_head" if cual == "head" else "extra_scripts"
        if bloque != esperado:
            errores.append("cdn_%s(...) esta en %s: tiene que ir en %s"
                           % (cual, bloque or "ningun block", esperado))
    return head, scripts, errores


def main() -> int:
    errors = []
    libs = catalogo()

    # 1) El macro define las 5 librerias y todas tienen al menos un JS.
    faltan = set(LIB_URLS) - set(libs)
    if faltan:
        errors.append("components/cdn_libs.html: faltan librerias del catalogo: %s"
                      % ", ".join(sorted(faltan)))
    for nombre, (css, js) in sorted(libs.items()):
        if not js:
            errors.append("components/cdn_libs.html: '%s' no tiene ningun JS" % nombre)

    # 2) Ninguna URL de libreria fuera del macro (salvo la excepcion de instalar).
    for path in sorted(TPL.rglob("*.html")):
        if path == MACRO:
            continue
        texto = path.read_text(encoding="utf-8")
        permitidas = EXCEPCIONES.get(path.name, set()) if path.parent == TPL else set()
        for url in URL_RE.findall(texto):
            lib = lib_de_url(url)
            if lib and lib not in permitidas:
                linea = texto[:texto.find(url)].count("\n") + 1
                errors.append("%s:%d tiene la URL de '%s' a mano: usar el macro "
                              "cdn_head/cdn_scripts de components/cdn_libs.html"
                              % (rel(path), linea, lib))

    # 3) base.html solo globaliza Font Awesome.
    base = BASE.read_text(encoding="utf-8")
    if not re.search(FONT_AWESOME, base):
        errors.append("base.html: se perdio Font Awesome (es la unica libreria "
                      "global: los iconos fas/far/fab se usan en casi todas las vistas)")
    for url in URL_RE.findall(base):
        lib = lib_de_url(url)
        if lib:
            errors.append("base.html: volvio a cargar '%s' para todas las paginas; "
                          "declararla en la vista que la usa" % lib)

    # 4) Cada pagina declara exactamente lo suyo, en el block correcto.
    paginas = [p for p in sorted(TPL.rglob("*.html"))
               if EXTENDS_RE.search(p.read_text(encoding="utf-8"))]
    for path in paginas:
        texto = path.read_text(encoding="utf-8")
        head, scripts, propios = declarado(texto)
        errors.extend("%s: %s" % (rel(path), e) for e in propios)
        esperado = ESPERADO.get(path.name, set())
        con_css = {n for n in esperado if libs.get(n, ([], []))[0]}
        if scripts != esperado:
            errors.append("%s: declara %s; deberia declarar %s en cdn_scripts"
                          % (rel(path), sorted(scripts) or "ninguna libreria",
                             sorted(esperado) or "ninguna"))
        if head != con_css:
            errors.append("%s: cdn_head declara %s; deberia declarar %s (las que "
                          "tienen CSS)" % (rel(path), sorted(head) or "nada",
                                           sorted(con_css) or "nada"))
        for nombre in scripts | head:
            if nombre not in libs:
                errors.append("%s: declara '%s', que no existe en el catalogo del macro"
                              % (rel(path), nombre))
        importado = IMPORT_RE.search(texto)
        necesita_import = bool(esperado)
        if necesita_import and not importado:
            errors.append("%s: usa los macros cdn_head/cdn_scripts sin importarlos "
                          "desde components/cdn_libs.html" % rel(path))
        if importado:
            nombres_import = {n.strip() for n in importado.group(1).split(",") if n.strip()}
            faltan_macros = {"cdn_head", "cdn_scripts"} - nombres_import
            if faltan_macros:
                errors.append("%s: el import de cdn_libs.html no trae %s"
                              % (rel(path), ", ".join(sorted(faltan_macros))))
        if not necesita_import and (head or scripts):
            errors.append("%s: declara librerias que no deberia necesitar" % rel(path))

    if errors:
        for e in errors:
            print("  ERROR: %s" % e)
        print("\nFALLO: %d problema(s) en el reparto de CDN por pagina." % len(errors))
        return 1

    print("  OK: el catalogo vive solo en components/cdn_libs.html (%d librerias: %s)."
          % (len(libs), ", ".join(sorted(libs))))
    print("  OK: base.html solo globaliza Font Awesome.")
    for nombre, esperado in sorted(ESPERADO.items()):
        print("  OK: %-24s -> %s" % (nombre, ", ".join(sorted(esperado))))
    print("  OK: las otras %d paginas no bajan ninguna libreria de CDN."
          % (len(paginas) - len([p for p in paginas if p.name in ESPERADO])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
