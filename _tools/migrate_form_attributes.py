"""Completa los atributos de usabilidad movil y de gestores de contrasena.

Dos huecos medidos en v9.34.92 sobre templates/:
  - autocomplete= aparecia 6 veces en todo el sitio: login, registro, recuperacion
    y cambio de contrasena quedaban sin pistas, asi que los gestores de contrasena
    no rellenaban ni ofrecian guardar, y el teclado movil no arrancaba en el
    campo correcto;
  - inputmode= aparecia 2 veces: DNI y telefono abrian teclado QWERTY.

Los formularios del dashboard cargan datos de OTRA persona (un admin crea o
edita usuarios), asi que ahi va autocomplete="off" a nivel de <form>: rellenar
con los datos del admin seria un error silencioso.

Idempotente: si el campo ya tiene el atributo, se saltea. Dry-run por defecto.

Uso:
  python _tools/migrate_form_attributes.py
  python _tools/migrate_form_attributes.py --apply
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# id del campo -> atributos a agregar
FIELD_ATTRS = {
    # login / recuperacion
    "login-email": 'autocomplete="username"',
    "login-password": 'autocomplete="current-password"',
    "recovery-email": 'autocomplete="email"',
    # registro
    "reg-nombre": 'autocomplete="given-name"',
    "reg-apellido": 'autocomplete="family-name"',
    "reg-dni": 'inputmode="numeric" autocomplete="off"',
    "reg-tel": 'inputmode="tel" autocomplete="tel"',
    "reg-email": 'autocomplete="email"',
    "reg-password": 'autocomplete="new-password"',
    "reg-password-confirm": 'autocomplete="new-password"',
    # alta por OAuth (los readonly ya vienen precargados: solo teclado)
    "oauth-signup-dni": 'inputmode="numeric"',
    "oauth-signup-tel": 'inputmode="tel"',
    # reset de contrasena
    "reset-password": 'autocomplete="new-password"',
    "reset-password-confirm": 'autocomplete="new-password"',
    # perfil > cuenta
    "input-nombre": 'autocomplete="given-name"',
    "input-apellido": 'autocomplete="family-name"',
    "input-dni": 'inputmode="numeric" autocomplete="off"',
    "input-email": 'autocomplete="email"',
    "input-telefono": 'inputmode="tel" autocomplete="tel"',
    "current-password": 'autocomplete="current-password"',
    "new-password": 'autocomplete="new-password"',
    "confirm-new-password": 'autocomplete="new-password"',
    # dashboard > usuarios (datos de terceros: solo teclado)
    "admin-user-dni": 'inputmode="numeric"',
    "edit-user-dni": 'inputmode="numeric"',
    "edit-user-tel": 'inputmode="tel"',
    # patente: el teclado debe arrancar en mayusculas y sin corrector
    "quick-veh-patente": 'autocapitalize="characters" spellcheck="false"',
    "add-veh-patente": 'autocapitalize="characters" spellcheck="false"',
}

# archivo -> etiquetas <form ...> exactas que reciben autocomplete="off"
FORM_ATTRS = {
    "templates/dashboard/modals/user_modals.html": [
        '<form class="modal-body" onsubmit="handleAdminCreateUser(event)">',
        '<form class="modal-body" onsubmit="handleAdminEditUser(event)">',
        '<form onsubmit="handleAdminChangePassword(event)">',
    ],
}

TAG_RE = r"<(?:input|select|textarea)\b[^>]*\bid=\"%s\"[^>]*>"


def add_attr(tag: str, attrs: str) -> str:
    """Inserta los atributos antes del cierre de la etiqueta de apertura."""
    if tag.endswith("/>"):
        return tag[:-2] + " " + attrs + "/>"
    return tag[:-1] + " " + attrs + ">"


def apply_attrs(text: str, tag: str, attrs: str, where: str, edits: list):
    """Agrega `attrs` a `tag` si todavia no estan."""
    missing = [
        a for a in attrs.split()
        if not re.search(r"\b%s=" % re.escape(a.split("=")[0]), tag)
    ]
    if not missing:
        return
    start = text.find(tag)
    if start < 0:
        print("  AVISO: no encuentro en %s: %s" % (where, tag[:70]))
        return
    edits.append((start, start + len(tag), add_attr(tag, " ".join(missing))))


def main() -> int:
    ap = argparse.ArgumentParser(description="Atributos de usabilidad movil y autofill.")
    ap.add_argument("--apply", action="store_true", help="Escribe los cambios.")
    args = ap.parse_args()

    # Agrupar por archivo para una sola lectura/escritura por template.
    by_field = {}
    for path in sorted((ROOT / "templates").rglob("*.html")):
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        with open(path, encoding="utf-8", newline="") as fh:
            text = fh.read()
        edits = []

        for fid, attrs in FIELD_ATTRS.items():
            m = re.search(TAG_RE % re.escape(fid), text, re.I)
            if m:
                apply_attrs(text, m.group(0), attrs, rel, edits)
        for form_tag in FORM_ATTRS.get(rel, []):
            apply_attrs(text, form_tag, 'autocomplete="off"', rel, edits)

        if not edits:
            continue
        print("%-58s campos: %d" % (rel, len(edits)))
        by_field[rel] = len(edits)
        if args.apply:
            new_text = text
            for start, end, replacement in sorted(edits, reverse=True):
                new_text = new_text[:start] + replacement + new_text[end:]
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)

    print("\nTotal de campos a tocar: %d%s"
          % (sum(by_field.values()), "" if args.apply else "  (dry-run)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
