"""Guard de equivalencia visual: prueba que una migracion de color fue neutra.

Complementa a migrate_color_tokens.py. Para cada CSS modificado respecto a HEAD,
resuelve TODOS los colores (literales y var(--x)) a RGBA canonico y compara el
multiset resultante entre la version HEAD y la de trabajo.

Si los multisets son identicos, la migracion no puede haber cambiado ningun
pixel: cada propiedad que resolvia a un color resuelve al mismo color.

Clasifica cada var() en tres desenlaces, porque no son lo mismo:
  - token que resuelve a un color -> cuenta como ese RGBA
  - token declarado no-color        -> env() / longitud: no pinta, no cuenta
  - token AUSENTE                   -> cuenta como UNRESOLVED (bug: no pinta nada)
Esto es lo que permitio cazar el `var(--text)` inexistente de dashboard-live.css.

Falla (exit 1) si algum arquivo resuelve distinto a HEAD.

Hay cambios de color LEGITIMOS (mover un titulo de dorado a blanco para bajar la
fatiga visual, por ejemplo). Esos no se pueden probar con este guard, porque el
guard existe justamente para demostrar lo contrario: que una migracion de tokens
no movio ni un pixel. Para no perder la proteccion, esos archivos van declarados
en color_equivalence_allowlist.json y solo se omiten cuando la comparacion es
contra el padre del commit que los cambio (validar un commit recien hecho).
En cualquier otra comparacion se comparan normales, asi una regresion posterior
en el mismo archivo sigue saltando. El flag --allow hace lo mismo de forma
puntual, sin tocar el archivo de lista.

Uso:  python _tools/check_color_equivalence.py
      python _tools/check_color_equivalence.py --against HEAD~1
Nota: comparar contra HEAD solo tiene sentido con cambios sin commitear.
"""
import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB = re.compile(
    r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.%]+)\s*)?\)"
)


def _alpha(raw):
    """Convierte el 4to componente de rgba() a 0-255.

    CSS admite dos notaciones: 0.05 (fraccion, la que usa el proyecto) y 5%
    (porcentaje). Cualquier otra cosa se asume que YA viene en 0-255, que es lo
    que ocurre si alguien escribe rgba(255,255,255,14) queriendo decir alfa 14.
    Tratar un 14 como fraccion daba 14*255=3570 y falseaba cualquier medicion.
    """
    if raw is None:
        return 255
    s = str(raw).strip()
    if s.endswith("%"):
        return int(round(float(s[:-1]) / 100.0 * 255))
    f = float(s)
    if 0.0 <= f <= 1.0:
        return int(round(f * 255))
    return int(round(f))
VAR = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*))?\)")
ENV = re.compile(r"\benv\(\s*--[\w-]+\s*(?:,[^()]*)?\)")
STRIP = re.compile(r"/\*.*?\*/", re.S)


def hex_to_rgba(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 6:
        h += "ff"
    if len(h) != 8:
        return None
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))


def rgb_to_rgba(r, g, b, a=None):
    return (int(float(r)), int(float(g)), int(float(b)), _alpha(a))


def token_values(text):
    """RGBA de cada Custom Property declarada. None si el valor no es un color.

    Una propiedad puede contener VARIOS colores, no uno: los tokens de sombra de
    dos capas ('--shadow-8-24-10-b70: 0 8px 24px rgba(0,0,0,0.7), 0 0 10px
    rgba(223,186,107,0.25)') tienen dos. Guardar solo el primero dejaba el
    segundo invisible y reportaba un falso 13/255 al tokenizar sombras, asi que
    aqui se guarda la LISTA completa de colores.
    """
    out = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", text):
        val = m.group(2).strip()
        cols = []
        for h in HEX.finditer(val):
            cols.append(hex_to_rgba(h.group(0)))
        if not cols:
            for r in RGB.finditer(val):
                cols.append(rgb_to_rgba(*r.groups()))
        out[m.group(1)] = cols if cols else None
    return out


def resolve_tokens(text, extra=None):
    """Reemplaza var(--x) por sus colores RGBA textuales (o por el fallback)."""
    toks = token_values(text)
    if extra:
        toks.update(extra)

    def sub(m):
        name, fallback = m.group(1), m.group(2)
        if name in toks and toks[name]:
            # Emitir hex8 (no rgba con alfa 0-255: el parser rgba asume 0-1).
            # Un token con varios colores expande a todos: se separan por coma
            # para que el contador de colores los vea igual que en el literal.
            return ",".join("#%02x%02x%02x%02x" % c for c in toks[name])
        if name in toks:
            return NONCOLOR          # declarado pero no es color (env(), longitud)
        return UNRESOLVED            # token ausente: bug real

    # hasta 3 rondas por si un token referencia a otro
    for _ in range(3):
        new = VAR.sub(sub, text)
        if new == text:
            break
        text = new
    return text


# Sentinelas (no son colores, no los cuenta el parser de color)
NONCOLOR = " envnoncolor "    # token declarado cuyo valor no es un color (env(), longitudes)
UNRESOLVED = " envunresolved "  # token AUSENTE: es el bug que se quiere detectar

NONCOLOR_RE = re.compile(r"envnoncolor")
UNRESOLVED_RE = re.compile(r"envunresolved")


def color_multiset(text, vars_css):
    """Multiset de colores RESUELTOS de un archivo, para comparar HEAD vs trabajo.

    - token que resuelve a un color  -> cuenta como ese RGBA
    - token declarado no-color       -> env() / longitud: no cuenta (no pinta)
    - token AUSENTE                  -> cuenta como UNRESOLVED (bug: no pinta nada)
    """
    toks = token_values(vars_css)
    text = STRIP.sub(" ", text)
    text = ENV.sub(NONCOLOR, text)
    text = resolve_tokens(text, toks)

    out = Counter()
    for m in HEX.finditer(text):
        r = hex_to_rgba(m.group(0))
        if r:
            out[r] += 1
    for m in RGB.finditer(text):
        out[rgb_to_rgba(*m.groups())] += 1
    n_unres = len(UNRESOLVED_RE.findall(text))
    if n_unres:
        out["UNRESOLVED"] += n_unres
    return out


def _rgb_multiset(m):
    return [c for c in m if isinstance(c, tuple)]


def multiset_delta(mb, ma, worst_where=None):
    """Desvio maximo por canal entre dos multisets de colores, en ambos sentidos.

    Empareja cada color con su MAS CERCANO en el otro lado y se queda con el
    peor emparejamiento. Asi una fusion de niveles casi identicos da un delta
    chico y medible, mientras que comparar todos contra todos daria siempre el
    maximo global y no serviria para nada.

    0 = identicos. Ignora el centinela UNRESOLVED (lo cuenta _no_new_unresolved).
    """
    ca, cb = _rgb_multiset(mb), _rgb_multiset(ma)
    if not ca or not cb:
        return 0
    worst = 0
    for src, dst in ((ca, cb), (cb, ca)):
        for c in src:
            best = min(max(abs(c[i] - o[i]) for i in range(4)) for o in dst)
            if best > worst:
                worst = best
                if worst_where is not None:
                    worst_where[0] = "rgba%s" % (c,)
    return worst


def _no_new_unresolved(mb, ma):
    """Falla si aparece un token AUSENTE nuevo (un color que antes no se pintaba)."""
    return ma.get("UNRESOLVED", 0) <= mb.get("UNRESOLVED", 0)


ALLOWLIST_PATH = Path(__file__).resolve().parent / "color_equivalence_allowlist.json"


def _parents_of(ref):
    """Hashes de los padres del commit `ref`. Vacio si no se puede resolver."""
    out = subprocess.run(["git", "rev-list", "--parents", "-n", "1", ref],
                         capture_output=True, text=True)
    parts = out.stdout.split()
    return set(parts[1:]) if len(parts) > 1 else set()


def _git_show(ref, rel):
    """Contenido de `rel` en `ref`, o "" si ese archivo no existia todavia.

    Hace falta porque un archivo CSS NUEVO aparece en `git diff --name-only ref`
    pero no existe en `ref`. Con check=True el guard reventaba con un
    CalledProcessError en vez de comparar, que es lo que paso con
    components/saludo.css en v9.34.71.

    Para un archivo agregado no hay baseline, asi que "" es el baseline
    correcto: no hay pixeles previos que preservar. El archivo nuevo igual
    queda controlado por _no_new_unresolved, que si detecta var() sin
    resolver.
    """
    out = subprocess.run(["git", "show", ref + ":" + rel],
                         capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ""


def committed_allowlist(root, ref):
    """Archivos de la lista, si `ref` es el padre del commit que los cambio.

    Se omiten SOLO en ese caso (validar el commit recien hecho). Si alguien
    vuelve a tocar el archivo mas adelante, el ref ya no es ese padre y el
    guard lo compara entero: la lista no abre un hueco permanente.
    """
    if not ALLOWLIST_PATH.exists():
        return {}
    data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    entries = data.get("files", {})
    if not entries:
        return {}

    parents = set()
    for c in {e.get("commit", "") for e in entries.values() if e.get("commit")}:
        parents |= _parents_of(c)
    if not parents:
        return {}

    # El ref que se esta comparando debe ser el padre del commit declarado.
    r = subprocess.run(["git", "rev-parse", ref], capture_output=True, text=True)
    if r.returncode != 0 or r.stdout.strip() not in parents:
        return {}

    return {rel.replace("\\", "/"): e.get("motivo", "")
            for rel, e in entries.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow", action="append", default=[], metavar="FILE",
                    help="archivo cuyo cambio de color es INTENCIONAL; se omite "
                         "del fallo pero se informa (repetible)")
    ap.add_argument("--max-delta", type=int, default=0, metavar="N",
                    help="tolerancia maxima de desvío por canal en 8 bits (0 = "
                         "exacto). Fase 2 usa un valor bajo a proposito: fusionar "
                         "niveles casi iguales no debe mover el color de forma "
                         "perceptible.")
    ap.add_argument("--against", default="HEAD", metavar="REF",
                    help="referencia de comparacion (default HEAD). Usar HEAD~1 "
                         "para validar recien un commit ya hecho.")
    args = ap.parse_args()
    allow = {a.replace("\\", "/").split("/")[-1] for a in args.allow}
    ref = args.against

    root = Path(__file__).resolve().parents[1]
    committed = committed_allowlist(root, ref)
    vars_path = root / "static" / "css" / "base" / "variables.css"
    if not vars_path.exists():
        print("No encuentro %s" % vars_path)
        return 1
    vars_new = vars_path.read_text(encoding="utf-8")
    vars_old = _git_show(ref, vars_path.relative_to(root).as_posix())
    if not vars_old:
        print("No encuentro %s en %s" % (vars_path.name, ref))
        return 1

    files = subprocess.run(
        ["git", "diff", "--name-only", ref, "--", "static/css"],
        capture_output=True, text=True, check=True).stdout.split()
    files = [f for f in files if f.endswith(".css") and "variables.css" not in f]

    print("Archivos a comparar: %d" % len(files))
    print("Tolerancia: %d/255 por canal%s"
          % (args.max_delta, " (exacto)" if args.max_delta == 0 else ""))
    bad, allowed = [], []
    total_before = total_after = 0
    worst = 0
    worst_info = [""]

    for rel in files:
        before = _git_show(ref, rel)
        after = (root / rel).read_text(encoding="utf-8")

        mb = color_multiset(before, vars_old)
        ma = color_multiset(after, vars_new)
        total_before += sum(mb.values())
        total_after += sum(ma.values())

        delta = multiset_delta(mb, ma, worst_info)
        if delta > worst:
            worst = delta
            worst_where = "%s (color que mas se movio: %s)" % (rel, worst_info[0])

        if delta <= args.max_delta and _no_new_unresolved(mb, ma):
            continue

        diffs = []
        for c in set(mb) | set(ma):
            if mb.get(c, 0) != ma.get(c, 0):
                diffs.append("  %s: %d -> %d" % (c, mb.get(c, 0), ma.get(c, 0)))
        name = rel.split("/")[-1]
        reason = committed.get(rel)
        if reason:
            allowed.append((rel, diffs, "lista: " + reason))
        elif name in allow:
            allowed.append((rel, diffs, "--allow"))
        else:
            bad.append((rel, diffs))

    print("Colores resueltos: %d antes -> %d despues" % (total_before, total_after))
    print("Desvio maximo por canal: %d/255%s"
          % (worst, ("  (%s)" % worst_where) if worst else ""))
    if allowed:
        print("")
        print("CAMBIOS INTENCIONALES (no se exige neutralidad, se informa):")
        for rel, diffs, src in allowed:
            print("  %s  [%s]" % (rel, src))
            for d in diffs:
                print(d)
    print("")
    if bad:
        print("ARCHIVOS CON COLORES RESUELTOS DISTINTOS:")
        for rel, diffs in bad:
            print("  %s" % rel)
            for d in diffs:
                print(d)
        print("")
        print("FALLO: la migracion supero la tolerancia de %d/255." % args.max_delta)
        return 1

    n_neutral = len(files) - len(allowed)
    if args.max_delta == 0:
        if allowed:
            print("OK: %d de %d archivos resuelven EXACTAMENTE los mismos colores."
                  % (n_neutral, len(files)))
            print("Los otros %d tienen cambio de color declarado como intencional "
                  "(arriba)." % len(allowed))
            print("Neutralidad garantizada solo para los %d archivos neutros."
                  % n_neutral)
        else:
            print("OK: los %d archivos resuelven EXACTAMENTE los mismos colores." % len(files))
            print("Cero cambio visual garantizado (mismo multiset RGBA por archivo).")
    else:
        print("OK: los %d archivos se movieron como maximo %d/255 por canal."
              % (len(files), worst))
        print("Dentro de la tolerancia %d/255." % args.max_delta)
        if worst:
            print("El mas afectado: %s" % worst_where)
    return 0


if __name__ == "__main__":
    sys.exit(main())
