"""Migra literales de color a Custom Properties cuando el RGBA es IDENTICO.

Cero cambio visual garantizado: solo reemplaza un literal si su RGBA normalizado
coincide exactamente con el de un token ya declarado. Si no coincide, no toca.

Excluye del reemplazo (para no romper nada):
  - el archivo variables.css (es la fuente de los tokens)
  - literales dentro de var(--x, #fallback): el fallback debe seguir siendo un
    literal valido aunque el token no exista (decisión de robustez)
  - literales dentro de content: (iconos de FontAwesome van ahi)

Dry-run por defecto. --apply escribe.

Uso:
  python _tools/migrate_color_tokens.py
  python _tools/migrate_color_tokens.py --apply
"""
import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path.cwd()
CSS_DIR = ROOT / "static" / "css"
VARIABLES = CSS_DIR / "base" / "variables.css"

if not VARIABLES.exists():
    raise SystemExit("No encuentro %s — corré el script desde la raíz del repo." % VARIABLES)

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB = re.compile(
    r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)"
)
PROTECT = re.compile(r"var\(\s*--[\w-]+\s*,[^()]*\)|content\s*:[^;}]+")

# Tokens semanticos preferidos cuando varios comparten el mismo RGBA.
PREFERRED = (
    "--text-primary", "--text-secondary", "--text-muted",
    "--bg-main", "--bg-sidebar", "--bg-card", "--bg-input",
    "--border", "--border-card", "--border-light",
    "--dorado", "--dorado-hover", "--dorado-dark", "--dorado-glow",
    "--success", "--danger", "--warning", "--info",
    "--violet-brand", "--violet-glow",
)

# Tokens GENERICOS: --blanco/--negro son colores fijos, no decisiones de diseño.
# Reemplazar "#fff" por "var(--blanco)" no aporta coherencia (el resultado es
# identico por definicion) y multiplica por 13 la indireccion: hoy --blanco tiene
# 12 usos y pasaria a 157. Se dejan fuera por defecto; --include-generic los
# agrega si se quiere consistencia mecanica total.
GENERIC = ("--blanco", "--negro")


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


def build_token_map():
    """RGBA normalizado -> tokens, leyendo solo variables.css."""
    text = VARIABLES.read_text(encoding="utf-8")
    by_rgba = defaultdict(list)
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", text):
        name, val = m.group(1), m.group(2).strip()
        hv = HEX.search(val)
        rgba = hex_to_rgba(hv.group(0)) if hv else None
        if rgba is None:
            rv = RGB.search(val)
            rgba = rgb_to_rgba(*rv.groups()) if rv else None
        if rgba:
            by_rgba[tuple(rgba)].append(name)
    return by_rgba


def pick_token(names):
    names = set(names)
    for pref in PREFERRED:
        if pref in names:
            return pref
    return sorted(names)[0]


def protected_spans(text):
    return [(m.start(), m.end()) for m in PROTECT.finditer(text)]


def in_spans(pos, spans):
    for s, e in spans:
        if s <= pos < e:
            return True
        if pos < s:
            break
    return False


def plan(text, by_rgba, skip_generic=True):
    """Devuelve (nuevo_texto, stats) sin escribir."""
    spans = protected_spans(text)
    edits = []  # (start, end, replacement, token)

    def resolve(rgba):
        if rgba is None or rgba not in by_rgba:
            return None
        tok = pick_token(by_rgba[rgba])
        if skip_generic and tok in GENERIC:
            return None
        return tok

    for m in HEX.finditer(text):
        if in_spans(m.start(), spans):
            continue
        tok = resolve(hex_to_rgba(m.group(0)))
        if tok:
            edits.append((m.start(), m.end(), "var(%s)" % tok, tok))

    for m in RGB.finditer(text):
        if in_spans(m.start(), spans):
            continue
        tok = resolve(rgb_to_rgba(*m.groups()))
        if tok:
            edits.append((m.start(), m.end(), "var(%s)" % tok, tok))

    if not edits:
        return text, Counter()

    edits.sort()
    out = []
    stats = Counter()
    cursor = 0
    for s, e, repl, tok in edits:
        out.append(text[cursor:s])
        out.append(repl)
        stats[tok] += 1
        cursor = e
    out.append(text[cursor:])
    return "".join(out), stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="escribe los cambios")
    ap.add_argument("--include-generic", action="store_true",
                    help="incluye #fff->var(--blanco) y #000->var(--negro)")
    args = ap.parse_args()

    skip_generic = not args.include_generic
    by_rgba = build_token_map()
    print("Tokens de color en variables.css: %d (RGBA distintos: %d)"
          % (sum(len(v) for v in by_rgba.values()), len(by_rgba)))
    print("Tokens genericos %s" % ("INCLUIDOS" if not skip_generic else
                                   "EXCLUIDOS (#fff/#000 se dejan como literal)"))

    per_file = {}
    by_token = Counter()
    for p in sorted(CSS_DIR.rglob("*.css")):
        if p.resolve() == VARIABLES.resolve():
            continue
        new, stats = plan(p.read_text(encoding="utf-8"), by_rgba, skip_generic)
        if stats:
            per_file[p] = (new, stats)
            by_token.update(stats)

    total = sum(by_token.values())
    mode = "APLICADO" if args.apply else "DRY-RUN (use --apply)"
    print("")
    print("%s: %d literales en %d archivos" % (mode, total, len(per_file)))
    for p in sorted(per_file, key=lambda x: -sum(per_file[x][1].values()))[:12]:
        print("  %-40s %3d" % (p.relative_to(ROOT).as_posix(), sum(per_file[p][1].values())))

    print("")
    print("Por token:")
    for tok, n in by_token.most_common():
        print("  %-22s %3d" % (tok, n))

    if args.apply:
        for p, (new, _stats) in per_file.items():
            p.write_text(new, encoding="utf-8", newline="\n")
        print("")
        print("Escritos %d archivos." % len(per_file))


if __name__ == "__main__":
    main()
