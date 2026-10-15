"""Guard: accesibilidad de formularios y de la retroalimentacion.

Cuatro formas concretas en que la app perdia accesibilidad, medidas en v9.34.92:

  1. ASOCIACION <label> -> CONTROL. Habia 179 <label> y solo 8 con for=. Un
     label sin asociar no da nombre accesible al campo: el lector de pantalla
     anuncia "edit text"/"combobox" sin decir cual, y clickear el rotulo no
     enfoca el campo. Los casos validos son dos: for="<id>" (o envolver al
     control, que es la asociacion implicita).
  2. for= QUE APUNTA A OTRO CAMPO. Un for= huerfano (id que no existe, o que
     quedo apuntando al campo de al lado despues de reordenar el formulario)
     falla en silencio: el label se ve bien y no asocia nada.
  3. TOGGLE DE CONTRASENA. Era un <i onclick>, o sea: no se podia tabular, no
     tenia nombre ni estado. Tiene que ser <button type="button"> (type=button
     es obligatorio: dentro de un <form> un button sin type es submit y clickear
     el ojo enviaria el formulario) con aria-label y aria-pressed.
  4. FEEDBACK QUE NO LLEGA. showToast tiene 206 llamadas y #toast-container no
     era live region: quien usa lector de pantalla no se enteraba de un exito ni
     de un error.

Mismo chequeo de marcado para los cuatro: se corre en segundos y sin navegador.

Uso:
  python _tools/check_a11y_forms.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"

LABEL_RE = re.compile(r"<label\b[^>]*>", re.I)
CLOSE_RE = re.compile(r"</label\s*>", re.I)
CONTROL_RE = re.compile(r"<(input|select|textarea)\b[^>]*>", re.I)
FORM_END_RE = re.compile(r"</form\s*>", re.I)
HAS_FOR_RE = re.compile(r"\bfor=", re.I)
FOR_RE = re.compile(r'\bfor="([^"]*)"', re.I)
ID_RE = re.compile(r'\bid="([^"]+)"', re.I)

# El toggle de contrasena es un <i> (mal) o un <button> (bien).
TOGGLE_I_RE = re.compile(r"<i\b[^>]*class=\"[^\"]*\btoggle-password\b", re.I)
TOGGLE_BTN_RE = re.compile(r"<button\b[^>]*class=\"[^\"]*\btoggle-password\b[^>]*>", re.I)

TOASTS = "templates/components/modals_global.html"
TOAST_RE = re.compile(r'<div\b[^>]*id="toast-container"[^>]*>', re.I)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def control_after(text: str, start: int):
    """El control que este label rotula, o None si es un label de valor/grupo."""
    form_end = FORM_END_RE.search(text, start)
    limit = form_end.start() if form_end else len(text)
    control = CONTROL_RE.search(text, start, limit)
    nxt = LABEL_RE.search(text, start, limit)
    if nxt and (control is None or nxt.start() < control.start()):
        return None  # otro label antes: es label de grupo
    return control


def check_template(path: Path, errors: list):
    text = path.read_text(encoding="utf-8")
    name = rel(path)

    for m in LABEL_RE.finditer(text):
        line = text[:m.start()].count("\n") + 1
        for_match = HAS_FOR_RE.search(m.group(0))
        control = control_after(text, m.end())

        if control is None:
            continue  # label sobre un valor de display: no aplica

        close = CLOSE_RE.search(text, m.end())
        if close and close.start() > control.start():
            continue  # envuelve al control: asociacion implicita

        control_tag = control.group(0)
        control_id = ID_RE.search(control_tag)

        if for_match:
            valor = FOR_RE.search(m.group(0)).group(1).strip()
            if not valor:
                errors.append("%s:%d tiene for= vacio" % (name, line))
            elif not control_id:
                errors.append("%s:%d declara for=\"%s\" pero el control siguiente "
                              "no tiene id=" % (name, line, valor))
            elif control_id.group(1) != valor:
                errors.append("%s:%d tiene for=\"%s\" pero el control siguiente es "
                              "id=\"%s\" (for= huerfano: no asocia nada)"
                              % (name, line, valor, control_id.group(1)))
        else:
            errors.append("%s:%d el <label> no asocia su campo (agregar for= o "
                          "envolver el control)" % (name, line))

    for m in TOGGLE_I_RE.finditer(text):
        line = text[:m.start()].count("\n") + 1
        errors.append("%s:%d el toggle de contrasena es un <i>: no se puede "
                      "tabular ni anunciar. Usar <button type=\"button\" ...>"
                      % (name, line))

    for m in TOGGLE_BTN_RE.finditer(text):
        line = text[:m.start()].count("\n") + 1
        tag = m.group(0)
        if not re.search(r'\btype="button"', tag, re.I):
            errors.append("%s:%d toggle de contrasena sin type=\"button\" "
                          "(dentro del form enviaria el formulario al clickearlo)"
                          % (name, line))
        for attr in ("aria-label", "aria-pressed"):
            if not re.search(r"\b%s=" % attr, tag, re.I):
                errors.append("%s:%d toggle de contrasena sin %s=" % (name, line, attr))


def check_toast(errors: list):
    path = ROOT / TOASTS
    if not path.exists():
        errors.append("falta %s" % TOASTS)
        return
    m = TOAST_RE.search(path.read_text(encoding="utf-8"))
    if not m:
        errors.append("%s: no encuentro #toast-container" % TOASTS)
        return
    tag = m.group(0)
    for attr in ("role=", "aria-live="):
        if not re.search(r"\b%s" % attr, tag, re.I):
            errors.append("%s: #toast-container sin %s: los toasts no se anuncian"
                          % (TOASTS, attr.rstrip("=")))


def main() -> int:
    errors = []
    for path in sorted(TPL.rglob("*.html")):
        check_template(path, errors)
    check_toast(errors)

    if errors:
        for e in errors:
            print("  ERROR: %s" % e)
        print("\nFALLO: %d problema(s) de accesibilidad de formularios." % len(errors))
        return 1

    print("  OK: cada <label> asocia su campo (for= o envolviendolo) y ningun for= "
          "apunta a otro id.")
    print("  OK: el toggle de contrasena es <button type=\"button\"> con aria-label "
          "y aria-pressed.")
    print("  OK: #toast-container sigue siendo live region (role + aria-live).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
