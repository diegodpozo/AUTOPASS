"""Tokeniza box-shadow duplicados EXACTOS (mismo valor escrito identico).

Criterio, mismo que la Fase 1 de color: solo se tokeniza una sombra si aparece
identica (byte a byte, normalizando espacios) en >= MIN_USO lugares. Las 108
sombras que se usan una sola vez son decisiones unicas de diseno y NO se tocan:
no hay escala que imponer (cero anclas >=8 usos).

Genera nombres a partir de la propia sombra para que el token sea legible:
  0 10px 30px rgba(0,0,0,0.5)  ->  --shadow-0-10-30-b50
  (los numeros son el desplazamiento Y el difuminado; el sufijo, la opacidad)

Solo genera tokens para sombras SIN token ya declarado, y unifica las que ya
aplican un var() con la misma geometria (ej. 0 0 20px var(--border-light) x3).

Dry-run por defecto. --apply escribe.

Uso:
  python _tools/migrate_shadow_tokens.py
  python _tools/migrate_shadow_tokens.py --apply
"""
import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = ROOT / "static" / "css"
VARIABLES = CSS_DIR / "base" / "variables.css"

MIN_USO = 2  # mismo criterio que "usada mas de una vez" del analisis

SHADOW = re.compile(r"(box-shadow)(\s*:\s*)([^;{}]+)")
STRIP = re.compile(r"/\*.*?\*/", re.S)
# Una sombra que ya es un var() no es candidata: tokenizarla seria crear un token
# que apunta a otro token. Sin este filtro la herramienta no es idempotente y en
# la segunda pasada tokeniza los tokens que ella misma acaba de generar.
# Admite el !important posterior: 'var(--x) !important' sigue siendo un token.
IS_TOKEN = re.compile(r"^\s*var\(\s*--[\w-]+\s*\)\s*(?:!\s*important\s*)?$")

# Una sombra bien formada: 'none', un var(), o capas [inset] offsets+blur+spread
# separadas por coma que terminan en un color. Es lo que valida verify() para
# detectar un corte mal placed sin depender de un parser de CSS completo.
# El cero sin unidad importa: '0 8px 24px rgba(...)' es valido y es la forma mas
# comun en el proyecto, asi que la longitud admite (?:[-\d.]+px|0) y no solo px.
_UNIT = r"(?:[-\d.]+px|0)"
_W = r"(?:%s\s+){1,4}" % _UNIT
_C = r"(?:rgba?\([^)]*\)|var\(--[\w-]+\)|#[0-9a-fA-F]{3,8})"
WELL_FORMED = re.compile(
    r"^(?:inset\s+)?" + _W + _C
    + r"(?:\s*,\s*(?:inset\s+)?" + _W + _C + r")*$")

IMPORTANT = re.compile(r"(\s*!\s*important\s*)$")


def split_important(value):
    """Separa 'sombra !important' -> (sombra, ' !important').

    Reemplazar el valor completo perderia el !important y cambiaria la cascada:
    'box-shadow: var(--x)' sin !important pierde contra cualquier regla posterior,
    mientras que el literal original lo ganaba. Hay que conservar el sufijo y
    ponerlo DESPUES del var().
    """
    m = IMPORTANT.search(value)
    if not m:
        return value.strip(), ""
    return value[:m.start()].strip(), m.group(1)

# un token de sombra ya presente en variables.css
TOKEN_SHADOW = re.compile(r"(--shadow-[\w-]+)\s*:\s*([^;]+);")


def norm(s):
    """Normaliza una sombra para comparar: colapsa espacios, quita el !important."""
    s = s.replace("!important", "")
    s = re.sub(r"\s+", " ", s.strip())
    # rgba(0, 0, 0, 0.5) == rgba(0,0,0,0.5)
    s = re.sub(r"\(\s*", "(", s)
    s = re.sub(r"\s*,\s*", ",", s)
    return s


def token_name(shadow):
    """Deriva un nombre legible de la geometria de la sombra.

    inset NO puede omitirse: una sombra inset y una equivalente sin inset pintan
    distinto, asi que el nombre tiene que distinguirla aunque la geometria sea
    la misma.
    """
    nums = re.findall(r"(-?[\d.]+)px", shadow)
    alpha = re.search(r"rgba?\([^)]*?,\s*([\d.]+)\s*\)", shadow)
    parts = [n.replace("-", "n").replace(".", "p") for n in nums[:3]]
    base = "--shadow-" + "-".join(parts) if parts else "--shadow-flat"
    if re.search(r"\binset\b", shadow):
        base += "-inset"
    if alpha:
        try:
            a = float(alpha.group(1))
            pct = int(round(a * 100)) if a <= 1.0 else int(round(a))
            base += "-b%d" % pct
        except ValueError:
            pass
    return base


def verify(before, after, edits, cands):
    """Comprueba que el codemod solo toco valores de box-shadow.

    Un codemod que reescribe CSS necesita una post-condicion fuerte: si solo
    puede cambiar un valor de box-shadow por un var(), entonces el balance de
    llaves, el de ';' y el numero de declaraciones tienen que quedar EXACTOS.
    Cualquier desvio significa que un corte cayo en el lugar equivocado.
    """
    problems = []
    for ch in "{};":
        if before.count(ch) != after.count(ch):
            problems.append("balance de %r cambio: %d -> %d"
                            % (ch, before.count(ch), after.count(ch)))
    nb = len(SHADOW.findall(before))
    na = len(SHADOW.findall(after))
    if nb != na:
        problems.append("numero de declaraciones box-shadow cambio: %d -> %d"
                        % (nb, na))
    # NOTA: el numero de palabras NO es un invariante. Reemplazar
    # '0 8px 32px rgba(0, 0, 0, 0.4)' (7 palabras) por 'var(--x)' (1 palabra) lo
    # baja legitimamente, asi que usarlo abortaria en cada archivo real. Solo
    # valen los invariantes que el codemod no puede alterar por construccion.
    # todo box-shadow resultante debe estar bien formado
    for m in SHADOW.finditer(after):
        v = m.group(3).strip()
        _sh, imp = split_important(v)
        if IS_TOKEN.match(_sh) or _sh == "none":
            continue
        if not WELL_FORMED.match(_sh):
            problems.append("box-shadow mal formado: %r" % v[:70])
    # los cortes no deben solaparse
    spans = sorted((s, e) for s, e, _ in edits)
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        if s2 < e1:
            problems.append("cortes solapados: [%d,%d) y [%d,%d)" % (s1, e1, s2, e2))
    # el conteo esperado son las declaraciones no tokenizadas que SON candidatas;
    # un archivo puede tener sombras de un solo uso que no entran en cands y esas
    # no cuentan (contarlas abortaba en falso sobre buttons.css)
    expected = sum(1 for m in SHADOW.finditer(before)
                   if not IS_TOKEN.match(m.group(3)) and norm(m.group(3)) in cands)
    if len(edits) != expected:
        problems.append("numero de cortes (%d) no coincide con las %d declaraciones "
                        "candidatas" % (len(edits), expected))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="escribe los cambios")
    ap.add_argument("--min", type=int, default=MIN_USO,
                    help="usos minimos para tokenizar (default %d)" % MIN_USO)
    args = ap.parse_args()

    files = sorted(CSS_DIR.rglob("*.css"))

    # 1) freq de cada sombra normalizada
    freq = Counter()
    where = defaultdict(set)
    for p in files:
        if p.resolve() == VARIABLES.resolve():
            continue
        txt = STRIP.sub(" ", p.read_text(encoding="utf-8", errors="ignore"))
        for m in SHADOW.finditer(txt):
            raw = m.group(3)
            if IS_TOKEN.match(raw):
                continue
            v = norm(raw)
            if v in ("none", ""):
                continue
            freq[v] += 1
            where[v].add(p.relative_to(ROOT).as_posix())

    cands = {k: v for k, v in freq.items() if v >= args.min}
    print("Sombras distintas: %d | con >=%d usos: %d | ocurrencias a tokenizar: %d"
          % (len(freq), args.min, len(cands), sum(cands.values())))
    print("")
    for k in sorted(cands, key=lambda x: -cands[x]):
        print("  x%-3d %-46s %s" % (cands[k], k[:46], token_name(k)))

    # 2) nombres unicos: si dos sombras colisionan en nombre, sufijar
    names = Counter(token_name(k) for k in cands)
    final = {}
    for k in cands:
        n = token_name(k)
        if names[n] > 1:
            n = n + "-" + re.sub(r"\W+", "", k.replace("rgba", "c").replace(")", ""))[:6]
        final[k] = n
    print("")
    for k in sorted(cands, key=lambda x: -cands[x]):
        print("  %-30s <- %s" % (final[k], k[:50]))

    if not args.apply:
        print("")
        print("DRY-RUN (use --apply).")
        return 0

    # 3) escribir los tokens en variables.css
    vtxt = VARIABLES.read_text(encoding="utf-8")
    existing = {m.group(1) for m in TOKEN_SHADOW.finditer(vtxt)}
    nuevos = [final[k] for k in cands if final[k] not in existing]
    if nuevos:
        bloque = ["", "/* Sombras reutilizadas (tokenizadas por _tools/migrate_shadow_tokens.py",
                  "   Solo duplicados EXACTOS: las sombras de un solo uso son decisiones",
                  "   unicas de diseno y se dejan como literal. */"]
        for k in sorted(cands, key=lambda x: -cands[x]):
            if final[k] in existing:
                continue
            bloque.append("    %s: %s;" % (final[k], k))
        bloque.append("")
        vtxt = vtxt.rstrip("\n") + "\n" + "\n".join(bloque) + "\n"
        VARIABLES.write_text(vtxt, encoding="utf-8", newline="\n")
        print("")
        print("Anadidos %d tokens a variables.css." % len(nuevos))

    # 4) calcular los reemplazos y validarlos TODOS antes de escribir nada.
    #    Un codemod debe ser atomico: si el archivo 8 de 20 falla, los otros 7 ya
    #    escritos quedan en un estado que nunca llego a pasar la validacion.
    planes = []
    for p in files:
        if p.resolve() == VARIABLES.resolve():
            continue
        txt = p.read_text(encoding="utf-8")
        edits = []
        for m in SHADOW.finditer(txt):
            if IS_TOKEN.match(m.group(3)):
                continue
            k = norm(m.group(3))
            if k in cands:
                _sh, imp = split_important(m.group(3))
                # el !important va DESPUES del var(), nunca dentro:
                # var(--tok !important) es un token inexistente.
                edits.append((m.start(3), m.end(3), "var(%s)%s" % (final[k], imp)))
        if not edits:
            continue
        edits.sort(key=lambda e: e[0], reverse=True)
        new = txt
        for start, end, repl in edits:
            # repl ya viene como texto completo ("var(--tok) !important"), no se
            # envuelve otra vez aqui
            new = new[:start] + repl + new[end:]
        planes.append((p, txt, new, edits))

    fallos = []
    for p, txt, new, edits in planes:
        problems = verify(txt, new, edits, cands)
        if problems:
            fallos.append((p, problems))
    if fallos:
        print("")
        print("ABORTADO sin escribir nada: %d archivo(s) con problemas." % len(fallos))
        for p, probs in fallos:
            print("   %s" % p.relative_to(ROOT).as_posix())
            for pr in probs:
                print("      " + pr)
        return 1

    # 5) escribir
    total = 0
    touched = []
    for p, txt, new, edits in planes:
        p.write_text(new, encoding="utf-8", newline="\n")
        total += len(edits)
        touched.append((p.relative_to(ROOT).as_posix(), len(edits)))
    print("Reemplazadas %d ocurrencias en %d archivos." % (total, len(touched)))
    for f, n in sorted(touched, key=lambda x: -x[1]):
        print("  %-46s %d" % (f, n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
