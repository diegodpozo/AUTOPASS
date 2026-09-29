"""Guard de llaves CSS balanceadas (AC-5 / bug tarifario dashboard).

Una llave "{" sin cerrar deja todo el resto del archivo anidado dentro del
bloque abierto. Si ese bloque es un @media, las reglas siguientes SOLO aplican
en ese breakpoint y el resto de la pagina se ve roto en escritorio sin aviso
ninguno en consola. Sintoma historico: en dashboard-settings.css el
@media (max-width: 768px) no cerraba, por lo que las reglas que ocultan las
sub-secciones de Configuracion (#set-section-system, #set-section-floors,
#set-section-monitoring y #rate-group-motos/camionetas) quedaban restringidas a
movil y en desktop se veian los 3 tarifarios apilados mas Plazas y Sistema.

Falla (exit 1) si algun archivo tiene llaves desbalanceadas, Comments y strings
se ignoran para no contar llaves de contenido.

Uso:
  python _tools/check_css_balance.py           # modo CI (exit 1 si hay desbalance)
  python _tools/check_css_balance.py --list    # detalle por archivo
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = ROOT / "static" / "css"


def _strip_noise(text: str) -> str:
    """Quita comentarios y contenido entre comillas para contar solo llaves de bloque."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"\\.", " ", text)  # escapes de CSS
    text = re.sub(r'"[^"\n]*"', '""', text)
    text = re.sub(r"'[^'\n]*'", "''", text)
    return text


def analyze(path: Path) -> dict:
    """Devuelve el desbalance final y la primera linea anomala.

    delta > 0: quedan llaves "{" sin cerrar, asi que todo lo que sigue queda
                anidado dentro del bloque abierto (tipicamente un @media).
    delta < 0: hay una "}" de mas; el parser la ignora, pero desordena el archivo.
    """
    openers: list = []          # lineas de las "{" abiertas y aun no cerradas
    extra_close_line = None

    for lineno, line in enumerate(_strip_comments_lines(path), start=1):
        for ch in line:
            if ch == "{":
                openers.append(lineno)
            elif ch == "}":
                if openers:
                    openers.pop()
                elif extra_close_line is None:
                    extra_close_line = lineno

    delta = len(openers) - (1 if extra_close_line is not None else 0)
    if openers:
        # Llave sin cerrar: se reporta la mas externa que quedo abierta.
        return {"delta": delta, "first_bad_line": openers[0]}
    return {"delta": delta, "first_bad_line": extra_close_line}


def _strip_comments_lines(path: Path):
    """Itera lineas sin comentarios y sin llaves dentro de strings."""
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        yield _strip_noise(raw)


def find_unbalanced() -> dict:
    """Devuelve {archivo_relativo: delta} para los CSS no balanceados."""
    bad = {}
    for path in sorted(CSS_DIR.rglob("*.css")):
        info = analyze(path)
        if info["delta"] != 0:
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            bad[rel] = info
    return bad


def main():
    parser = argparse.ArgumentParser(description="Guard de llaves CSS balanceadas (AC-5).")
    parser.add_argument("--list", action="store_true", help="Detalle de desbalance por archivo.")
    args = parser.parse_args()

    bad = find_unbalanced()

    if args.list:
        for css, info in bad.items():
            print(f"{css}: delta={info['delta']:+d} (primera anomalia linea {info['first_bad_line']})")
        print(f"\nTotal archivos desbalanceados: {len(bad)}")
        return 0

    total = len(list(CSS_DIR.rglob("*.css")))
    print(f"Archivos CSS revisados: {total}")
    print(f"Archivos desbalanceados: {len(bad)}")
    if bad:
        print("\nERROR: llaves CSS desbalanceadas (reglas anidadas por error dentro de un @media):")
        for css, info in bad.items():
            print(f"  - {css}: delta={info['delta']:+d} (primera anomalia linea {info['first_bad_line']})")
        return 1
    print("OK: todas las llaves CSS balanceadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
