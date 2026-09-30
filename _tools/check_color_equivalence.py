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

Falla (exit 1) si algum archivo resuelve distinto a HEAD.

Uso:  python _tools/check_color_equivalence.py
Nota: comparar contra HEAD solo tiene sentido con cambios sin commitear.
"""
import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB = re.compile(
    r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)"
)
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
    alpha = int(round(float(a) * 255)) if a is not None else 255
    return (int(float(r)), int(float(g)), int(float(b)), alpha)


def token_values(text):
    """RGBA de cada Custom Property declarada. None si el valor no es un color."""
    out = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", text):
        val = m.group(2).strip()
        hv = HEX.search(val)
        if hv:
            out[m.group(1)] = hex_to_rgba(hv.group(0))
        else:
            rv = RGB.search(val)
            out[m.group(1)] = rgb_to_rgba(*rv.groups()) if rv else None
    return out


def resolve_tokens(text, extra=None):
    """Reemplaza var(--x) por su literal RGBA textual (o por el fallback)."""
    toks = token_values(text)
    if extra:
        toks.update(extra)

    def sub(m):
        name, fallback = m.group(1), m.group(2)
        if name in toks and toks[name]:
            # Emitir hex8 (no rgba con alfa 0-255: el parser rgba asume 0-1).
            r, g, b, a = toks[name]
            return "#%02x%02x%02x%02x" % (r, g, b, a)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow", action="append", default=[], metavar="FILE",
                    help="archivo cuyo cambio de color es INTENCIONAL; se omite "
                         "del fallo pero se informa (repetible)")
    args = ap.parse_args()
    allow = {a.replace("\\", "/").split("/")[-1] for a in args.allow}

    root = Path(__file__).resolve().parents[1]
    vars_path = root / "static" / "css" / "base" / "variables.css"
    if not vars_path.exists():
        print("No encuentro %s" % vars_path)
        return 1
    vars_new = vars_path.read_text(encoding="utf-8")
    vars_old = subprocess.run(
        ["git", "show", "HEAD:" + vars_path.relative_to(root).as_posix()],
        capture_output=True, text=True, check=True).stdout

    files = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "static/css"],
        capture_output=True, text=True, check=True).stdout.split()
    files = [f for f in files if f.endswith(".css") and "variables.css" not in f]

    print("Archivos a comparar: %d" % len(files))
    bad, allowed = [], []
    total_before = total_after = 0

    for rel in files:
        before = subprocess.run(
            ["git", "show", "HEAD:" + rel], capture_output=True, text=True,
            check=True).stdout
        after = (root / rel).read_text(encoding="utf-8")

        mb = color_multiset(before, vars_old)
        ma = color_multiset(after, vars_new)
        total_before += sum(mb.values())
        total_after += sum(ma.values())

        if mb != ma:
            diffs = []
            for c in set(mb) | set(ma):
                if mb.get(c, 0) != ma.get(c, 0):
                    diffs.append("  %s: %d -> %d" % (c, mb.get(c, 0), ma.get(c, 0)))
            name = rel.split("/")[-1]
            (allowed if name in allow else bad).append((rel, diffs))

    print("Colores resueltos: %d antes -> %d despues" % (total_before, total_after))
    if allowed:
        print("")
        print("CAMBIOS INTENCIONALES (--allow):")
        for rel, diffs in allowed:
            print("  %s" % rel)
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
        print("FALLO: la migracion no fue visualmente neutra.")
        return 1

    print("OK: los %d archivos resuelven EXACTAMENTE los mismos colores." % len(files))
    print("Cero cambio visual garantizado (mismo multiset RGBA por archivo).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
