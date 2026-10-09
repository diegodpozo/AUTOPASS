"""AC-5 (CSS muerto, duplicación y DRY — ver Info proyecto/AUDITORIAS.md). Guard de clases CSS huerfanas.

Extrae los nombres de clase definidos en static/css/**/*.css y busca su uso real
en templates/**/*.html, static/js/**/*.js y *.py. Una clase es HUERFANA si no
aparece en ninguno de esos tres con coincidencia por token delimitado (evita
falsos positivos por subcadena, p.ej. "p-10" dentro de "gap-10").

Falla (exit 1) si la cantidad de huerfanas supera el umbral del baseline.

Uso:
  python _tools/check_css_huerfano.py            # modo CI (exit 1 si supera el umbral)
  python _tools/check_css_huerfano.py --list     # imprime el detalle huerfan por archivo
  python _tools/check_css_huerfano.py --update   # regenera el baseline tras la purga
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = ROOT / "static" / "css"
SCAN_DIRS = [ROOT / "templates", ROOT / "static" / "js"]
BASELINE_PATH = Path(__file__).resolve().parent / "css_huerfano_baseline.json"

# Clases de terceros: no son nuestras, las define la libreria en runtime.
THIRD_PARTY_PREFIXES = ("flatpickr-", "leaflet-", "numInput", "arrowUp", "arrowDown")

# Clases vivas solo por concatenacion en runtime, p.ej. dashboard.html
# "document.body.classList.add('role-' + rol)", reservations-admin-list.js
# "badge-${estado.toLowerCase()}" y dashboard-informes.js
# "hm-leg--t${tramos.length}" (leyenda del grafico de barras). Se validan a mano
# contra el emisor.
RUNTIME_BUILT_PREFIXES = ("badge-", "role-", "hm-leg--t")

SELECTOR_CLASS_RE = re.compile(r"\.(-?[_a-zA-Z][\w-]*)")


def _strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


def defined_classes() -> dict:
    """Devuelve {clase: [archivos css donde se define]}."""
    found: dict = {}
    for path in sorted(CSS_DIR.rglob("*.css")):
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        for name in SELECTOR_CLASS_RE.findall(_strip_comments(path.read_text(encoding="utf-8"))):
            found.setdefault(name, [])
            if rel not in found[name]:
                found[name].append(rel)
    return found


PY_DIRS = [ROOT / "routes", ROOT / "core", ROOT / "services", ROOT / "models", ROOT / "tests", ROOT / "utils"]
SKIP_DIRS = {".venv", "node_modules", ".git", "__pycache__", "alembic", "Info proyecto"}


def _read(path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _usage_blob() -> str:
    chunks = []
    for base in SCAN_DIRS:
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in {".html", ".js"} and not (SKIP_DIRS & set(path.parts)):
                chunks.append(_read(path))
    for base in PY_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if not (SKIP_DIRS & set(path.parts)):
                chunks.append(_read(path))
    return "\n".join(chunks)


def find_orphans(classes: dict, blob: str) -> dict:
    orphans = {}
    for name, files in classes.items():
        if name.startswith(THIRD_PARTY_PREFIXES):
            continue
        if name in blob:
            continue
        # Prefijos generados en runtime: se consideran vivas (se validan aparte).
        if any(name.startswith(p) for p in RUNTIME_BUILT_PREFIXES):
            continue
        orphans[name] = files
    return orphans


def load_baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Guard de clases CSS huerfanas (AC-5).")
    parser.add_argument("--list", action="store_true", help="Detalle de huerfanas por archivo CSS.")
    parser.add_argument("--update", action="store_true", help="Regenera el baseline con el conteo actual.")
    args = parser.parse_args()

    classes = defined_classes()
    orphans = find_orphans(classes, _usage_blob())

    by_file: dict = {}
    for name, files in orphans.items():
        for css in files:
            by_file.setdefault(css, []).append(name)

    if args.update:
        baseline = {"orphan_count": len(orphans), "files": {k: sorted(v) for k, v in by_file.items()}}
        BASELINE_PATH.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Baseline actualizado: {len(orphans)} huerfanas -> {BASELINE_PATH.name}")
        return 0

    if args.list:
        for css in sorted(by_file, key=lambda c: -len(by_file[c])):
            print(f"{css} ({len(by_file[css])})")
            for name in sorted(by_file[css]):
                print(f"    .{name}")
        print(f"\nTotal huerfanas: {len(orphans)}")
        return 0

    threshold = load_baseline().get("orphan_count", len(orphans))
    print(f"Clases definidas: {len(classes)}")
    print(f"Clases huerfanas: {len(orphans)}  (baseline: {threshold})")
    if len(orphans) > threshold:
        print(f"\nERROR: {len(orphans)} huerfanas > baseline {threshold} (regresion de CSS muerto)")
        return 1
    print("OK: sin regresion de CSS muerto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
