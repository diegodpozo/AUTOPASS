"""Asocia cada <label> con el control de formulario que rotula (for= / id=).

Estado previo (v9.34.92): en templates/ habia 179 <label> y solo 8 con for=.
Consecuencia concreta: clickear el rotulo no enfocaba el campo, y un lector de
pantalla anunciaba "edit text" / "combobox" sin decir cual, porque el nombre
accesible no existe si el label no esta asociado (ni por for= ni envolviendo al
control).

Que hace:
  - al <label> que esta AL LADO de un control le agrega for="<id>";
  - si el control no tenia id, se lo agrega (mapa MISSING_ID, explicito: la clave
    es el texto del control, asi no se rompe si cambian los numeros de linea).

Que NO hace (a proposito, para no inventar asociaciones):
  - label que ENVUELVE al control: la asociacion implicita ya funciona;
  - label sobre un valor de display (no hay control que rotular);
  - label de grupo (aparece otro <label> antes del control);
  - el control debe estar antes del </form> de su propio formulario, para no
    emparejar un label con un campo del formulario siguiente.

Idempotente: si el label ya tiene for=, se saltea. Dry-run por defecto.

Uso:
  python _tools/migrate_label_association.py            # lista lo que haria
  python _tools/migrate_label_association.py --apply    # escribe
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"

LABEL_RE = re.compile(r"<label\b[^>]*>", re.I)
CLOSE_RE = re.compile(r"</label\s*>", re.I)
CONTROL_RE = re.compile(r"<(input|select|textarea)\b[^>]*>", re.I)
FORM_END_RE = re.compile(r"</form\s*>", re.I)
HAS_ID_RE = re.compile(r'\bid="', re.I)
HAS_FOR_RE = re.compile(r"\bfor=", re.I)
ID_RE = re.compile(r'\bid="([^"]+)"', re.I)

# Controles que no tenian id. Clave: (ruta relativa con /, texto exacto del
# control). El id se elige con prefijo por formulario para no chocar dentro del
# mismo DOM (perfil.html incluye inicio.html y vehiculos.html a la vez, y las
# dos traen el form "NUEVO VEHICULO").
MISSING_ID = {
    ("templates/contacto.html",
     '<input type="text" placeholder="Ej: Juan Pérez" required>'): "contact-nombre",
    ("templates/contacto.html",
     '<input type="email" placeholder="juan@ejemplo.com" required>'): "contact-email",
    ("templates/contacto.html",
     "<select required>"): "contact-motivo",
    ("templates/contacto.html",
     '<textarea rows="5" placeholder="Escribí tu mensaje aquí..." required>'): "contact-mensaje",

    ("templates/profile/tabs/inicio.html",
     '<select name="tipo" class="input-premium-sm fg-pad-left" '
     'onchange="updateVehicleTypeIcon(this.value, \'quick-\', this.form)">'): "quick-veh-tipo",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" name="patente" placeholder="ABC 123" required '
     'class="input-premium-sm uppercase fg-sm">'): "quick-veh-patente",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" name="marca_modelo" placeholder="Ej: VW Gol" required '
     'class="input-premium-sm fg-sm">'): "quick-veh-marca",

    ("templates/profile/tabs/inicio.html",
     '<select class="res-vehicle fg-select" required>'): "res-vehicle",
    ("templates/profile/tabs/inicio.html",
     '<select class="res-sucursal fg-select" required>'): "res-sucursal",
    ("templates/profile/tabs/inicio.html",
     '<select class="res-type fg-select" required>'): "res-type",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-date-only input-premium" placeholder="Fecha...">'): "res-date-only",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-day-only input-premium" placeholder="Seleccioná día...">'): "res-day-only",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-week-start input-premium" placeholder="Fecha inicio...">'): "res-week-start",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-week-end input-premium-readonly" readonly>'): "res-week-end",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-fortnight-start input-premium" placeholder="Fecha inicio...">'): "res-fortnight-start",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-fortnight-end input-premium-readonly" readonly>'): "res-fortnight-end",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-month-start input-premium" placeholder="Fecha inicio...">'): "res-month-start",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-month-end input-premium-readonly" readonly>'): "res-month-end",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-start input-premium" placeholder="Fecha y hora...">'): "res-start",
    ("templates/profile/tabs/inicio.html",
     '<input type="text" class="res-end input-premium" placeholder="Fecha y hora...">'): "res-end",

    ("templates/profile/tabs/vehiculos.html",
     '<select name="tipo" class="input-premium-sm fg-pad-left" '
     'onchange="updateVehicleTypeIcon(this.value, \'\', this.form)">'): "add-veh-tipo",
    ("templates/profile/tabs/vehiculos.html",
     '<input type="text" name="patente" placeholder="ABC 123" required '
     'class="input-premium-sm uppercase">'): "add-veh-patente",
    ("templates/profile/tabs/vehiculos.html",
     '<input type="text" name="marca_modelo" placeholder="Ej: VW Gol" required '
     'class="input-premium-sm">'): "add-veh-marca",
}


def add_attr(tag: str, attr: str) -> str:
    """Inserta `attr` justo antes del cierre de la etiqueta de apertura."""
    if tag.endswith("/>"):
        return tag[:-2] + " " + attr + "/>"
    return tag[:-1] + " " + attr + ">"


def plan_for(path: Path, text: str):
    """Devuelve (ediciones, avisos) para un template."""
    edits, warnings = [], []
    rel = str(path.relative_to(ROOT)).replace("\\", "/")

    for m in LABEL_RE.finditer(text):
        if HAS_FOR_RE.search(m.group(0)):
            continue
        form_end = FORM_END_RE.search(text, m.end())
        limit = form_end.start() if form_end else len(text)

        control = CONTROL_RE.search(text, m.end(), limit)
        next_label = LABEL_RE.search(text, m.end(), limit)
        if next_label and (control is None or next_label.start() < control.start()):
            continue  # label de grupo: otro label aparece antes del control
        if control is None:
            continue  # label sobre valor de display

        close = CLOSE_RE.search(text, m.end())
        if close and close.start() > control.start():
            continue  # envuelve al control: asociacion implicita

        control_tag = control.group(0)
        id_match = ID_RE.search(control_tag)
        if id_match:
            control_id = id_match.group(1)
        else:
            control_id = MISSING_ID.get((rel, control_tag))
            if not control_id:
                warnings.append(
                    "%s:%d control sin id y sin entrada en MISSING_ID: %s"
                    % (rel, text[:control.start()].count("\n") + 1, control_tag[:70]))
                continue
            edits.append((control.start(), control.end(),
                          add_attr(control_tag, 'id="%s"' % control_id)))

        edits.append((m.start(), m.end(), add_attr(m.group(0), 'for="%s"' % control_id)))

    return edits, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Asocia <label> con su control (for=/id=).")
    ap.add_argument("--apply", action="store_true", help="Escribe los cambios.")
    args = ap.parse_args()

    total = 0
    warnings = []
    for path in sorted(TPL.rglob("*.html")):
        with open(path, encoding="utf-8", newline="") as fh:
            text = fh.read()
        edits, warns = plan_for(path, text)
        warnings.extend(warns)
        if not edits:
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        labels = sum(1 for e in edits if text[e[0]:e[1]].lstrip().lower().startswith("<label"))
        ids = len(edits) - labels
        print("%-58s labels: %3d   id nuevos: %3d" % (rel, labels, ids))

        if args.apply:
            new_text = text
            for start, end, replacement in sorted(edits, reverse=True):
                new_text = new_text[:start] + replacement + new_text[end:]
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
        total += len(edits)

    print("\nTotal de atributos a escribir: %d%s" % (total, "" if args.apply else "  (dry-run)"))
    for w in warnings:
        print("  AVISO: %s" % w)
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
