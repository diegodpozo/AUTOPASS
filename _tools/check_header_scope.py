"""Guard: el header del portal no puede ser un selector descendiente.

El header de /perfil y /dashboard se estiliza con
`.main-content-scroll header`. Ese selector matchea CUALQUIER <header> que
este debajo de <main class="main-content-scroll">, no solo el hijo directo.

Con v9.34.71 el macro del saludo paso a emitir <header class="saludo">. El
saludo vive dentro de .main-content-scroll, asi que matcheaba la regla del
header del portal y heredaba position:sticky, top:0, z-index:1000, background
opaco y backdrop-filter:blur(25px). Como va despues en el DOM a igual z-index
tapaba el dropdown de notificaciones, en escritorio y en movil.

Dos defensas:
  1. el saludo emite <div>, no <header> (no es landmark: el section contenedor
     es un <div>, y el <h1> de adentro ya da el encabezado);
  2. las reglas usan `.main-content-scroll > header`, hijo directo, asi ningun
     <header> anidado futuro las dispara.

Este guard verifica las dos.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Selectores que estilizan el header del portal. Deben ser de hijo directo.
HEADER_RULES = [
    ("static/css/layout/header.css", r"\.main-content-scroll\s*>\s*header"),
    ("static/css/layout/standalone.css", r"\.main-content-scroll\s*>\s*header"),
]

DESCENDANT = re.compile(r"\.main-content-scroll\s+header(?![-\w])")
HEADER_TAG = re.compile(r"<header\b")
TABS = ["inicio", "vehiculos", "reservas", "puntos",
        "notificaciones", "cuenta", "ayuda"]


def main() -> int:
    errors = []

    for rel, expected in HEADER_RULES:
        p = ROOT / rel
        if not p.exists():
            errors.append("no existe %s" % rel)
            continue
        text = p.read_text(encoding="utf-8")
        for m in DESCENDANT.finditer(text):
            line = text[:m.start()].count("\n") + 1
            errors.append(
                "%s:%d usa el selector descendente '.main-content-scroll header'"
                "; debe ser '.main-content-scroll > header'" % (rel, line))
        if not re.search(expected, text):
            errors.append("%s perdio la regla '.main-content-scroll > header'" % rel)

    # Ningun tab del portal debe emitir un <header>: matchearia el header.
    for tab in TABS:
        p = ROOT / "templates" / "profile" / "tabs" / ("%s.html" % tab)
        if not p.exists():
            errors.append("falta %s" % p.relative_to(ROOT))
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if HEADER_TAG.search(line):
                errors.append(
                    "templates/profile/tabs/%s.html:%d emite <header>; el header "
                    "del portal se selecciona por etiqueta y lo terminaria "
                    "heredando. Usar <div>." % (tab, i))

    # El header real del portal tiene que seguir siendo <header> hijo directo.
    perfil = (ROOT / "templates" / "perfil.html").read_text(encoding="utf-8")
    if not re.search(r'<main class="main-content-scroll">\s*<header>', perfil):
        errors.append("perfil.html: el header real ya no es hijo directo de "
                      "main-content-scroll, la regla > header dejaria de "
                      "aplicar")

    if errors:
        for e in errors:
            print("  ERROR: %s" % e)
        print("\nFALLO: %d problema(s) con el header del portal." % len(errors))
        return 1

    print("  OK: el header del portal se selecciona como hijo directo y ningun "
          "tab emite <header>.")
    print("  Verificado en header.css, standalone.css y los 7 tabs de /perfil.")
    return 0


if __name__ == "__main__":
    sys.exit(main())