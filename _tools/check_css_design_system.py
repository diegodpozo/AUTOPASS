"""Guard de design system: fija un baseline medible de las metricas visuales.

Complementa a los guards ya existentes:
  - check_css_balance.py   -> llaves {} balanceadas
  - check_css_huerfano.py  -> clases .foo sin uso
  - check_css_tokens.py    -> tokens declarados/usados
  - check_color_equivalence.py -> prueba de que una migracion fue neutra

Este NO corrige nada: mide y compara contra un baseline en JSON, para que
cualquier unificacion futura (escala de espaciado, sombras, transiciones,
color) sea una regresion medible y no una operacion a ciegas.

Metricas:
  color      : literales de color, valores RGBA distintos, y cuantos son
               equivalentes exactos a un token existente (migrables sin cambio)
  spacing    : declaraciones px en padding/margin/gap/inset fuera de multiplos de 4
  shadow     : box-shadow distintas
  transition : duraciones y curvas distintas

Uso:
  python _tools/check_css_design_system.py            # falla si empeora (exit 1)
  python _tools/check_css_design_system.py --report   # detalle completo
  python _tools/check_css_design_system.py --update   # acepta el estado actual
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = ROOT / "static" / "css"
VARIABLES = CSS_DIR / "base" / "variables.css"
BASELINE = Path(__file__).resolve().parent / "css_design_system_baseline.json"

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB = re.compile(
    r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)"
)
STRIP = re.compile(r"/\*.*?\*/", re.S)

# px en propiedades de caja/espaciado
SPACING = re.compile(
    r"(?:padding|margin|gap|top|right|bottom|left|inset)[a-z-]*:\s*(-?[\d.]+)px")
SHADOW = re.compile(r"box-shadow:\s*([^;]+)")
TRANSITION = re.compile(r"transition:\s*([^;]+)")

# #fff y #000 NO se consideran literales "a unificar": son colores fijos y
# convertirlos a var(--blanco)/var(--negro) no aporta coherencia.
GENERIC_HEX = {"#fff", "#ffffff", "#000", "#000000"}


def hex_to_rgba(h):
    h = h.lstrip("#").lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 6:
        h += "ff"
    if len(h) != 8:
        return None
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))


def rgb_to_rgba(m):
    r, g, b = (int(float(x)) for x in m.group(1, 2, 3))
    a = m.group(4)
    return (r, g, b, int(round(float(a) * 255)) if a is not None else 255)


def iter_css():
    for p in sorted(CSS_DIR.rglob("*.css")):
        yield p, STRIP.sub(" ", p.read_text(encoding="utf-8", errors="ignore"))


def token_rgba_map():
    out = {}
    text = VARIABLES.read_text(encoding="utf-8")
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", text):
        val = m.group(2).strip()
        hv = HEX.search(val)
        if hv:
            out[m.group(1)] = hex_to_rgba(hv.group(0))
        else:
            rv = RGB.search(val)
            if rv:
                out[m.group(1)] = rgb_to_rgba(rv)
    by_rgba = {}
    for name, rgba in out.items():
        if rgba:
            by_rgba.setdefault(tuple(rgba), []).append(name)
    return by_rgba


def measure():
    by_rgba = token_rgba_map()
    color_lit = Counter()
    color_equiv = 0
    off_grid = Counter()
    off_grid_total = 0
    shadows = Counter()
    durations = Counter()
    curves = Counter()

    for _p, txt in iter_css():
        for m in HEX.finditer(txt):
            raw = m.group(0).lower()
            if raw in GENERIC_HEX:
                continue
            rgba = hex_to_rgba(raw)
            if rgba:
                color_lit[rgba] += 1
                if rgba in by_rgba:
                    color_equiv += 1
        for m in RGB.finditer(txt):
            rgba = rgb_to_rgba(m)
            color_lit[rgba] += 1
            if rgba in by_rgba:
                color_equiv += 1
        for v in SPACING.findall(txt):
            f = float(v)
            if f != 0 and f % 4 != 0:
                off_grid[f] += 1
                off_grid_total += 1
        for s in SHADOW.findall(txt):
            if s.strip() != "none":
                shadows[re.sub(r"\s+", " ", s.strip())] += 1
        for decl in TRANSITION.findall(txt):
            for d in re.findall(r"(?<![\d.])(\d*\.?\d+)m?s\b", decl):
                durations[d] += 1
            for c in re.findall(
                    r"cubic-bezier\([^)]*\)|\bease-in-out\b|\bease-out\b|"
                    r"\bease-in\b|\bease\b|\blinear\b", decl):
                curves[c] += 1

    return {
        "color": {
            "literales_no_genericos": sum(color_lit.values()),
            "valores_rgba_distintos": len(color_lit),
            "equivalentes_a_token": color_equiv,
        },
        "spacing": {
            "off_grid_ocurrencias": off_grid_total,
            "off_grid_valores_distintos": len(off_grid),
        },
        "shadow": {"distintas": len(shadows)},
        "transition": {
            "duraciones_distintas": len(durations),
            "curvas_distintas": len(curves),
        },
    }, {
        "off_grid_top": off_grid.most_common(10),
        "color_top": [(str(c), n) for c, n in color_lit.most_common(10)],
        "curvas_top": curves.most_common(8),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--update", action="store_true", help="acepta el estado actual")
    args = ap.parse_args()

    metrics, detail = measure()

    if args.update:
        BASELINE.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print("Baseline actualizado en %s" % BASELINE.name)
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0

    if not BASELINE.exists():
        print("No hay baseline. Generalo con: python %s --update" % Path(__file__).name)
        return 1

    base = json.loads(BASELINE.read_text(encoding="utf-8"))

    if args.report:
        print(json.dumps(metrics, indent=2, sort_keys=True))
        print("")
        print("off-grid px (top 10): %s" % detail["off_grid_top"])
        print("colores literales (top 10): %s" % detail["color_top"])
        print("curvas de transicion: %s" % detail["curvas_top"])
        return 0

    worse = []
    for section, vals in metrics.items():
        for key, val in vals.items():
            old = base.get(section, {}).get(key)
            if old is None:
                worse.append("%s.%s: NUEVO (sin baseline)" % (section, key))
            elif val > old:
                worse.append("%s.%s: %d -> %d (empeora)" % (section, key, old, val))
            elif val < old:
                print("mejora  %s.%s: %d -> %d" % (section, key, old, val))

    if worse:
        print("REGRESIONES de design system:")
        for w in worse:
            print("  %s" % w)
        return 1

    print("OK: sin regresiones de design system.")
    print("  color      %d literales no genericos (%d equivalentes a token), "
          "%d RGBA distintos" % (
              metrics["color"]["literales_no_genericos"],
              metrics["color"]["equivalentes_a_token"],
              metrics["color"]["valores_rgba_distintos"]))
    print("  spacing    %d ocurrencias off-grid en %d valores" % (
        metrics["spacing"]["off_grid_ocurrencias"],
        metrics["spacing"]["off_grid_valores_distintos"]))
    print("  shadow     %d box-shadow distintas" % metrics["shadow"]["distintas"])
    print("  transition %d duraciones, %d curvas" % (
        metrics["transition"]["duraciones_distintas"],
        metrics["transition"]["curvas_distintas"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
