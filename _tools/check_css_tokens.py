"""Guard de integridad de Custom Properties (tokens CSS) — v9.34.61.

Complementa a los guards existentes, que NO miran tokens:
  - check_css_balance.py    -> llaves {} balanceadas
  - check_css_huerfano.py   -> clases .foo sin uso

Este cubre las dos direcciones del contrato de tokens:

1. `var(--x)` usado sin que `--x` este declarado. Un token inexistente no da error
   ni warning: la propiedad cae silenciosamente a su valor heredado/inicial. Asi
   un `color: var(--text)` con typo se ve en un gris cualquiera y nadie se entera
   hasta que se nota el texto "despintado" en un estado puntual.
   Bug real corregido con este guard: `.barrier-text` en dashboard-live.css:357
   usaba `var(--text)` (inexistente) en vez de `var(--text-secondary)`.

2. `--x` declarado y nunca usado: token muerto (mismo criterio que las clases
   huerfanas de AC-5, Lote 9).

Distingue Custom Properties reales de clases BEM: `.btn--premium:` NO es un
token `--premium`; exige que el `--nombre` no este pegado a un selector de clase.

Falla (exit 1) si hay tokens usados-sin-declarar o declarados-sin-usar.

Uso:
  python _tools/check_css_tokens.py           # modo CI (exit 1 si hay problemas)
  python _tools/check_css_tokens.py --list    # detalle por token
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = ROOT / "static" / "css"

# Custom Property: precedida por inicio de linea, espacio, {, o ; (NO por un
# selector de clase como .btn--premium) seguida de : y un valor.
DECLARE_RE = re.compile(
    r"(?:^|[\s{;])(--[a-z0-9]+(?:-[a-z0-9]+)*)\s*:\s*[^;{}]+", re.M
)
USE_RE = re.compile(r"var\(\s*(--[\w-]+)")
STRIP_COMMENTS = re.compile(r"/\*.*?\*/", re.S)


def _collect():
    files = sorted(CSS_DIR.rglob("*.css"))
    declared = set()
    used = Counter()
    used_in = {}

    for path in files:
        text = STRIP_COMMENTS.sub(" ", path.read_text(encoding="utf-8", errors="ignore"))
        for m in DECLARE_RE.finditer(text):
            declared.add(m.group(1))
        for m in USE_RE.finditer(text):
            token = m.group(1)
            used[token] += 1
            used_in.setdefault(token, set()).add(path.relative_to(ROOT).as_posix())

    return declared, used, used_in


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="detalle por token")
    args = ap.parse_args()

    declared, used, used_in = _collect()
    undef = sorted(set(used) - declared)
    unused = sorted(declared - set(used))

    if args.list:
        print("Declarados (%d):" % len(declared))
        for t in sorted(declared):
            print("  %-28s usos=%d" % (t, used.get(t, 0)))
        print("")
        for t in undef:
            print("SIN DECLARAR: %s  (usado en: %s)"
                  % (t, ", ".join(sorted(used_in[t]))))
        for t in unused:
            print("SIN USAR:     %s" % t)

    if not undef and not unused:
        print("OK: %d tokens, todos declarados y usados." % len(declared))
        return 0

    print("")
    print("Usados sin declarar: %d" % len(undef))
    for t in undef:
        print("  %s  <- en %s" % (t, ", ".join(sorted(used_in[t]))))
    print("Declarados sin usar: %d" % len(unused))
    for t in unused:
        print("  %s" % t)
    return 1


if __name__ == "__main__":
    sys.exit(main())
