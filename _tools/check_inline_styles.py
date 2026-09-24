"""P3 AUDITORIA_COMPONENTES - Guard de estilos inline en templates.

Falla si:
  * un template existente SUPERA el conteo registrado en el baseline (regresión);
  * un template NUEVO (no registrado) supera THRESHOLD_NEW (25) estilos inline.

Emails (templates/emails) se descartan por diseño.

Uso:
  python _tools/check_inline_styles.py          # modo CI (exit 1 si falla)
  python _tools/check_inline_styles.py --update # regenera el baseline tras limpiezas
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates"
BASELINE_PATH = Path(__file__).resolve().parent / "inline_styles_baseline.json"
THRESHOLD_NEW = 25
EXCLUDED_DIRS = {"emails"}

STYLE_RE = re.compile(r"style\s*=\s*[\"']")


def count_styles(path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(STYLE_RE.findall(text))


def scan() -> dict:
    counts = {}
    for path in sorted(TEMPLATES_DIR.rglob("*.html")):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(TEMPLATES_DIR).parts):
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        counts[rel] = count_styles(path)
    return counts


def load_baseline():
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Guard de estilos inline en templates.")
    parser.add_argument("--update", action="store_true", help="Regenera el baseline con los conteos actuales.")
    args = parser.parse_args()

    counts = scan()

    if args.update:
        baseline = {"threshold_new": THRESHOLD_NEW, "files": counts}
        BASELINE_PATH.write_text(
            json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"Baseline actualizado: {len(counts)} templates -> {BASELINE_PATH.name}")
        return 0

    baseline = load_baseline()
    prev = baseline.get("files", {})
    failures = []

    rows = []
    for rel, current in counts.items():
        rows.append((rel, current, prev.get(rel)))
    for rel in sorted(set(prev) - set(counts)):
        rows.append((rel, None, prev[rel]))

    for rel, current, old in sorted(rows, key=lambda r: r[1] if r[1] is not None else -1, reverse=True):
        if current is None:
            print(f"  DEL    {rel} (era {old})")
            continue
        if old is None:
            status = "NUEVO"
            if current > (threshold := baseline.get("threshold_new", THRESHOLD_NEW)):
                failures.append(f"{rel}: {current} inline > umbral {threshold} (archivo nuevo)")
                status = "FALLA"
        elif current > old:
            status = "REGRESIÓN"
            failures.append(f"{rel}: {current} inline > baseline {old}")
        else:
            status = "ok"
            if current < old:
                status = f"mejorado ({old}->{current})"
        print(f"  {status:>14}  {rel}  ({current})")

    print(f"\nTotal templates analizados: {len(counts)}")
    if failures:
        print("\nERRORES (estilos inline fuera de control):")
        for f in failures:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())