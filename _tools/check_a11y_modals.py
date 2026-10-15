"""Guard: los contenedores de dialogo son dialogos accesibles de verdad.

Estado previo (v9.34.93): 28 contenedores con class modal / modal-premium /
onboarding-overlay-premium y NINGUNO con role="dialog", aria-modal ni nombre
accesible. Cuatro formas concretas en que eso se perdia:

  1. SIN ROLE. Un <div class="modal"> no es un dialogo para el lector de
     pantalla: no lo anuncia al abrirse y sigue leyendo la pagina de atras.
  2. SIN NOMBRE. aria-labelledby tiene que apuntar a un id que EXISTA. En este
     repo el id del titulo lo emite el macro modal_header (parametro title_id),
     asi que un aria-labelledby cuyo id no este ni en el archivo ni como
     title_id de una llamada al macro queda apuntando al vacio: el dialogo se
     anuncia como "dialogo" a secas. Si el dialogo no tiene titulo visible, el
     nombre tiene que venir en aria-label.
  3. CIERRE NO TABULABLE / SIN NOMBRE. Un <span class="close-btn" onclick> no se
     puede tabular ni activar con teclado: tiene que ser <button> o <a>. Y un
     <button> que solo lleva un icono adentro se anuncia como \"boton\" a secas:
     necesita aria-label (o texto visible) y type=\"button\" (dentro de un <form>
     un button sin type es submit).
  4. CIERRE QUE ESCAPE NO ENCUENTRA. ui.js cierra con Escape ACTIVANDO el
     control de cierre del dialogo de arriba (asi corre la logica propia:
     resolver la promesa de showConfirm/showChoice, sacar el blur del
     onboarding, frenar el reloj virtual). Si el dialogo no tiene ningun
     control reconocible, Escape solo puede ocultar el contenedor a mano y esa
     logica no corre.

Mismo chequeo de marcado para los cuatro: se corre en segundos y sin navegador.

Uso:
  python _tools/check_a11y_modals.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"

# Clases que convierten a un <div> en dialogo (las mismas que usa ui.js).
CLASES_DIALOGO = {"modal", "modal-premium", "onboarding-overlay-premium"}

DIV = re.compile(r"<div\b[^>]*>", re.I)
DIV_OPEN = re.compile(r"<div\b", re.I)
DIV_CLOSE = re.compile(r"</div\s*>", re.I)
CLASE_RE = re.compile(r'\bclass="([^"]*)"')
ID_RE = re.compile(r'\bid="([^"]+)"')
LABELLEDBY_RE = re.compile(r'\baria-labelledby="([^"]+)"')
TITLE_ID_RE = re.compile(r"\btitle_id\s*=\s*['\"]([^'\"]+)['\"]")
ROLE_RE = re.compile(r'\brole="dialog"', re.I)
ARIA_MODAL_RE = re.compile(r'\baria-modal="true"', re.I)

# Control de cierre que ui.js sabe activar con Escape.
CIERRE_RE = re.compile(r'<(\w+)\b[^>]*class="[^"]*\b(?:close-btn|modal-close-top)\b', re.I)
DATA_CIERRE_RE = re.compile(r"\bdata-modal-close\b")
ARIA_LABEL_RE = re.compile(r'\baria-label="[^"]+"')

# Los 18 dialogos de contenido usan el macro modal_header, que emite el boton de
# cierre en su propio archivo: el id no esta en el template que arma el dialogo,
# asi que la regla 4 valida el macro en vez de pedirle el boton a cada archivo.
MACRO_HDR = TPL / "components/modal_header.html"
MACRO_CALL_RE = re.compile(r"\bmodal_header\s*\(")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def bloque(text: str, inicio: int) -> str:
    """Desde el '<div' de apertura hasta el '</div>' que lo cierra."""
    profundidad = 0
    i = inicio
    while i < len(text):
        abre = DIV_OPEN.search(text, i)
        cierra = DIV_CLOSE.search(text, i)
        if cierra is None:
            break
        if abre is not None and abre.start() < cierra.start():
            profundidad += 1
            i = abre.end()
        else:
            profundidad -= 1
            i = cierra.end()
            if profundidad == 0:
                return text[inicio:i]
    return text[inicio:]


def macro_emite_cierre() -> bool:
    """El macro modal_header emite un cierre que ui.js puede activar con Escape
    y que ademas tiene nombre accesible."""
    texto = MACRO_HDR.read_text(encoding="utf-8")
    for m in CIERRE_RE.finditer(texto):
        if m.group(1).lower() != "button":
            continue
        fin = texto.find(">", m.start())
        tag = texto[m.start():fin + 1]
        if DATA_CIERRE_RE.search(tag) and ARIA_LABEL_RE.search(tag):
            return True
    return False


def check_template(path: Path, errors: list, macro_ok: bool):
    text = path.read_text(encoding="utf-8")
    name = rel(path)

    for m in DIV.finditer(text):
        tag = m.group(0)
        clase = CLASE_RE.search(tag)
        if not clase:
            continue
        if not (CLASES_DIALOGO & set(clase.group(1).split())):
            continue

        linea = text[:m.start()].count("\n") + 1
        id_dialogo = ID_RE.search(tag)
        id_dialogo = id_dialogo.group(1) if id_dialogo else "(sin id)"

        # Regla 1: es un dialogo.
        if not ROLE_RE.search(tag):
            errors.append("%s:%d #%s no declara role=\"dialog\"" % (name, linea, id_dialogo))
        if not ARIA_MODAL_RE.search(tag):
            errors.append("%s:%d #%s no declara aria-modal=\"true\""
                          % (name, linea, id_dialogo))

        # Regla 2: tiene nombre accesible.
        labelledby = LABELLEDBY_RE.search(tag)
        if labelledby:
            ref = labelledby.group(1)
            existe = re.search(r'\bid="%s"' % re.escape(ref), text)
            emitido = re.search(r"\btitle_id\s*=\s*['\"]%s['\"]" % re.escape(ref), text)
            if not (existe or emitido):
                errors.append("%s:%d #%s tiene aria-labelledby=\"%s\" pero ese id no "
                              "existe en el archivo ni lo emite el macro modal_header "
                              "(title_id): el dialogo queda sin nombre"
                              % (name, linea, id_dialogo, ref))
        elif not re.search(r'\baria-label="[^"]+"', tag):
            errors.append("%s:%d #%s no tiene nombre accesible (aria-labelledby o "
                          "aria-label)" % (name, linea, id_dialogo))

        # Reglas 3 y 4: cierre tabulable y reconocible, dentro del dialogo.
        cuerpo = bloque(text, m.start())
        tiene_cierre = bool(DATA_CIERRE_RE.search(cuerpo) or CIERRE_RE.search(cuerpo))
        if not tiene_cierre and macro_ok and MACRO_CALL_RE.search(cuerpo):
            tiene_cierre = True  # lo emite el macro modal_header
        if not tiene_cierre:
            errors.append("%s:%d #%s no tiene control de cierre reconocible "
                          "(data-modal-close, .close-btn o .modal-close-top): con "
                          "Escape no se puede activar su logica de cierre"
                          % (name, linea, id_dialogo))
        for cierre in CIERRE_RE.finditer(cuerpo):
            etiqueta = cierre.group(1).lower()
            fin = cuerpo.find(">", cierre.start())
            tag = cuerpo[cierre.start():fin + 1]
            linea_cierre = text[:m.start() + cierre.start()].count("\n") + 1
            if etiqueta not in ("button", "a"):
                errors.append("%s:%d el cierre de #%s es un <%s>: no se puede tabular ni "
                              "activar con teclado. Usar <button type=\"button\">"
                              % (name, linea_cierre, id_dialogo, etiqueta))
                continue
            # Nombre accesible: aria-label, o texto visible adentro del boton. Un
            # boton que solo lleva un <i> de icono se anuncia como "boton" a secas.
            cierre_fin = cuerpo.find("</%s>" % etiqueta, fin)
            interior = cuerpo[fin + 1:cierre_fin] if cierre_fin > 0 else ""
            texto = re.sub(r"<[^>]*>", "", interior).strip()
            if not ARIA_LABEL_RE.search(tag) and not texto:
                errors.append("%s:%d el cierre de #%s no tiene nombre accesible "
                              "(aria-label o texto visible): un lector de pantalla lo "
                              "anuncia como \"boton\" a secas"
                              % (name, linea_cierre, id_dialogo))
            if etiqueta == "button" and 'type="button"' not in tag:
                errors.append("%s:%d el cierre de #%s es un <button> sin type=\"button\": "
                              "dentro de un <form> seria submit"
                              % (name, linea_cierre, id_dialogo))


def main() -> int:
    errors = []
    dialogos = 0
    macro_ok = macro_emite_cierre()
    if not macro_ok:
        errors.append("templates/components/modal_header.html: el macro modal_header ya "
                      "no emite un cierre reconocible y con nombre (button + "
                      "data-modal-close + aria-label): los 18 dialogos de contenido se "
                      "quedarian sin cierre para Escape")
    for path in sorted(TPL.rglob("*.html")):
        check_template(path, errors, macro_ok)
        text = path.read_text(encoding="utf-8")
        for m in DIV.finditer(text):
            clase = CLASE_RE.search(m.group(0))
            if clase and (CLASES_DIALOGO & set(clase.group(1).split())):
                dialogos += 1

    if errors:
        for e in errors:
            print("  ERROR: %s" % e)
        print("\nFALLO: %d problema(s) en %d dialogos." % (len(errors), dialogos))
        return 1

    print("  OK: los %d dialogos declaran role=\"dialog\" + aria-modal=\"true\"." % dialogos)
    print("  OK: todos tienen nombre accesible (aria-labelledby con id real o aria-label).")
    print("  OK: el control de cierre es <button>/<a>, con nombre accesible y "
          "type=\"button\": Escape lo puede encontrar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
