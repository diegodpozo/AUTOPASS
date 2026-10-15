"""Convierte los contenedores de dialogo en dialogos accesibles (role=dialog).

Estado previo (v9.34.93): 28 contenedores con class modal / modal-premium /
onboarding-overlay-premium y NINGUNO con role="dialog", aria-modal ni nombre
accesible. Eso dejaba cuatro cosas sin resolver:

  1. NOMBRE. Sin role="dialog" el lector de pantalla no anuncia que se abrio un
     dialogo: sigue leyendo la pagina de atras. El nombre accesible sale del
     titulo visible (aria-labelledby) y, donde el dialogo no tiene titulo (los
     tickets de pase digital y de canje), de un aria-label explicito.
  2. AISLAMIENTO. aria-modal="true" es lo que le dice al lector que el fondo
     quedo inerte (el encierro real del foco con Tab lo hace ui.js).
  3. CIERRE TABULABLE Y CON NOMBRE. Los 5 <span class="close-btn" onclick> no se
     podian tabular ni activar con teclado: pasan a <button type="button">
     (type=button obligatorio: dentro de un <form>, un button sin type es submit)
     con aria-label="Cerrar". Los 2 que ya eran <button> pero solo tenian un icono
     adentro reciben type + aria-label: sin eso el lector de pantalla anuncia
     "boton" a secas (o el caracter del icono, que es basura).
  4. CONTROL DE CIERRE PARA ESCAPE. ui.js cierra el dialogo de arriba activando
     su control de cierre, asi corre la logica propia de cada uno (resolver la
     promesa de showConfirm/showChoice, sacar el blur del onboarding, frenar el
     reloj virtual). Los controles que no se pueden reconocer por clase
     (.close-btn / .modal-close-top) se marcan con data-modal-close.

Que NO hace (a proposito):
  - NO agrega titulos visibles: no cambia diseno. Donde no hay titulo, usa
    aria-label.
  - NO duplica marcado: los 18 dialogos que usan el macro modal_header ya lo
    tienen, asi que solo se le pasa title_id (parametro que el macro ya soporta).
  - NO enruta los call sites de JS por openModal: eso es codigo, no marcado.

Idempotente: si el contenedor ya tiene role="dialog", se saltea. Dry-run por
defecto.

Uso:
  python _tools/migrate_modal_a11y.py            # lista lo que haria
  python _tools/migrate_modal_a11y.py --apply    # escribe
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"

# (archivo, id del contenedor) -> (tipo de nombre accesible, valor).
# labelledby apunta al titulo VISIBLE del dialogo; label es texto propio, solo
# para los 2 dialogos que no tienen titulo (tickets imprimibles).
DIALOGOS = {
    ("templates/components/auth_modals.html", "loginModal"): ("labelledby", "login-title"),
    ("templates/components/auth_modals.html", "recoveryModal"): ("labelledby", "recovery-title"),
    ("templates/components/auth_modals.html", "registerModal"): ("labelledby", "register-title"),
    ("templates/components/auth_modals.html", "oauthSignupModal"): ("labelledby", "oauth-signup-title"),
    ("templates/components/modals_global.html", "modal-confirm"): ("labelledby", "confirm-title"),
    ("templates/components/modals_global.html", "modal-choice"): ("labelledby", "choice-title"),
    ("templates/components/virtual_time_banner.html", "vt-modal"): ("labelledby", "vt-modal-title"),
    ("templates/dashboard.html", "modal-log-detail"): ("labelledby", "log-detail-modal-title"),
    ("templates/dashboard.html", "modal-pending-exit"): ("labelledby", "pending-exit-modal-title"),
    ("templates/dashboard.html", "modal-res-detail"): ("labelledby", "res-detail-modal-title"),
    ("templates/dashboard/modals/admin_help_modal.html", "modal-admin-help"): ("labelledby", "admin-help-modal-title"),
    ("templates/dashboard/modals/branch_modals.html", "modal-branch-floors"): ("labelledby", "branch-floors-title"),
    ("templates/dashboard/modals/branch_modals.html", "modal-add-branch"): ("labelledby", "branch-modal-title"),
    ("templates/dashboard/modals/promotion_modal.html", "modal-create-promotion"): ("labelledby", "promo-modal-title"),
    ("templates/dashboard/modals/user_modals.html", "modal-create-user"): ("labelledby", "create-user-modal-title"),
    ("templates/dashboard/modals/user_modals.html", "modal-edit-user"): ("labelledby", "edit-user-modal-title"),
    ("templates/dashboard/modals/user_modals.html", "modal-change-password-admin"): ("labelledby", "change-password-modal-title"),
    ("templates/dashboard/tabs/admin_reservations.html", "modal-new-reservation"): ("labelledby", "new-res-modal-title"),
    ("templates/dashboard/tabs/admin_reservations.html", "modal-edit-resumo"): ("labelledby", "edit-resumo-modal-title"),
    ("templates/dashboard/tabs/settings/settings_system.html", "modal-add-floor"): ("labelledby", "floor-modal-title"),
    ("templates/dashboard/tabs/settings/settings_system.html", "modal-camera-config"): ("labelledby", "camera-modal-title"),
    ("templates/dashboard/tabs/tickets.html", "modal-ticket-answer"): ("labelledby", "ticket-modal-title"),
    ("templates/profile/modals/onboarding_modal.html", "reservation-onboarding-modal"): ("labelledby", "onboarding-modal-title"),
    ("templates/profile/modals.html", "support-ticket-modal"): ("labelledby", "modal-ticket-subject"),
    ("templates/profile/modals.html", "modal-pase-digital"): ("label", "Pase digital de la reserva"),
    ("templates/profile/modals.html", "modal-canje"): ("label", "Ticket de canje del cupon"),
    ("templates/profile/modals.html", "rechargeModal"): ("labelledby", "recharge-modal-title"),
    ("templates/profile/modals.html", "modal-legal-terms"): ("labelledby", "legal-modal-title"),
}

# (archivo, expresion del cierre del macro) -> id del <h3>.
# El macro modal_header ya soporta title_id; sin id no hay aria-labelledby.
TITLE_ID_MACRO = {
    ("templates/dashboard.html", "closeModal('modal-log-detail')"): "log-detail-modal-title",
    ("templates/dashboard.html", "closePendingExitPopup()"): "pending-exit-modal-title",
    ("templates/dashboard.html", "closeModal('modal-res-detail')"): "res-detail-modal-title",
    ("templates/dashboard/modals/admin_help_modal.html", "closeModal('modal-admin-help')"): "admin-help-modal-title",
    ("templates/dashboard/modals/user_modals.html", "closeModal('modal-create-user')"): "create-user-modal-title",
    ("templates/dashboard/modals/user_modals.html", "closeModal('modal-edit-user')"): "edit-user-modal-title",
    ("templates/dashboard/modals/user_modals.html", "closeModal('modal-change-password-admin')"): "change-password-modal-title",
    ("templates/dashboard/tabs/admin_reservations.html", "cancelEditResumo()"): "edit-resumo-modal-title",
    ("templates/profile/modals.html", "closeModal('rechargeModal')"): "recharge-modal-title",
}

# Titulos visibles que no tenian id (los que no pasan por el macro).
# (archivo, texto actual, texto con id)
TITULOS = [
    ("templates/components/auth_modals.html",
     "<h2>INICIÁ SESIÓN</h2>", '<h2 id="login-title">INICIÁ SESIÓN</h2>'),
    ("templates/components/auth_modals.html",
     "<h2>RECUPERÁ TU ACCESO</h2>", '<h2 id="recovery-title">RECUPERÁ TU ACCESO</h2>'),
    ("templates/components/auth_modals.html",
     "<h2>CREÁ TU CUENTA</h2>", '<h2 id="register-title">CREÁ TU CUENTA</h2>'),
    ("templates/components/auth_modals.html",
     "<h2>COMPLETÁ TU REGISTRO</h2>", '<h2 id="oauth-signup-title">COMPLETÁ TU REGISTRO</h2>'),
    ("templates/components/virtual_time_banner.html",
     '<h3 class="text-dorado">RELOJ VIRTUAL DEL SISTEMA</h3>',
     '<h3 class="text-dorado" id="vt-modal-title">RELOJ VIRTUAL DEL SISTEMA</h3>'),
    ("templates/profile/modals/onboarding_modal.html",
     "<h3>BIENVENIDO A AUTOPASS</h3>", '<h3 id="onboarding-modal-title">BIENVENIDO A AUTOPASS</h3>'),
]

# Controles de cierre que Escape tiene que activar y que no se reconocen por
# clase. (texto actual, texto con data-modal-close)
MARCAR_CIERRE = [
    ('<button id="confirm-btn-cancel" class="btn btn--outline">',
     '<button id="confirm-btn-cancel" class="btn btn--outline" data-modal-close>'),
    ('<button id="choice-btn-cancel" class="btn btn--outline">',
     '<button id="choice-btn-cancel" class="btn btn--outline" data-modal-close>'),
    ('<button class="btn btn--outline" onclick="skipReservationOnboarding()">Omitir</button>',
     '<button type="button" class="btn btn--outline" data-modal-close '
     'onclick="skipReservationOnboarding()">Omitir</button>'),
]

# Controles de cierre que ya eran <button> pero sin nombre accesible ni type: un
# boton con solo un icono adentro se anuncia como "boton" a secas (o con el
# caracter del icono, que es basura). (texto actual, texto corregido)
CIERRE_SIN_NOMBRE = [
    ('<button class="modal-close-top no-print" onclick="closeDigitalPass()">',
     '<button type="button" class="modal-close-top no-print" aria-label="Cerrar" '
     'onclick="closeDigitalPass()">'),
    ('<button class="modal-close-top no-print" onclick="closeCanjeModal()">',
     '<button type="button" class="modal-close-top no-print" aria-label="Cerrar" '
     'onclick="closeCanjeModal()">'),
]

# Dialogos que se centran con flex: la clase reemplaza el style inline que
# tenian showConfirm/showChoice (align-items/justify-content), asi ui.js sabe
# que display usar al abrirlos. Se agrega en la MISMA edicion que role/aria
# porque ambas tocan la etiqueta de apertura del contenedor.
CENTRADOS = {"modal-confirm", "modal-choice"}

SPAN_CIERRE_RE = re.compile(
    r'<span class="close-btn" onclick="([^"]+)"><i class="fas fa-xmark"></i></span>')
CALL_RE = re.compile(r"(?:\{\{|\{[-%])\s*(?:call\s+)?modal_header\s*\(")


def add_attr(tag: str, attr: str) -> str:
    """Inserta `attr` justo antes del cierre de la etiqueta de apertura."""
    if tag.endswith("/>"):
        return tag[:-2] + " " + attr + "/>"
    return tag[:-1] + " " + attr + ">"


def fin_de_llamada(text: str, desde: int) -> int:
    """Indice (exclusivo) del ')' que cierra la llamada al macro."""
    i, profundidad, comillas = desde, 1, None
    while i < len(text) and profundidad:
        c = text[i]
        if comillas:
            if c == comillas:
                comillas = None
        elif c in "\"'":
            comillas = c
        elif c == "(":
            profundidad += 1
        elif c == ")":
            profundidad -= 1
        i += 1
    return i


def plan_for(path: Path, text: str):
    """Devuelve (ediciones, avisos) para un template."""
    edits, warnings = [], []
    rel = str(path.relative_to(ROOT)).replace("\\", "/")

    # 1. Contenedores: role + aria-modal + nombre accesible.
    for (archivo, dialogo_id), (tipo, valor) in DIALOGOS.items():
        if archivo != rel:
            continue
        tag_re = re.compile(r'<div\b[^>]*\bid="%s"[^>]*>' % re.escape(dialogo_id))
        m = tag_re.search(text)
        if not m:
            warnings.append("%s: no encuentro el contenedor #%s" % (rel, dialogo_id))
            continue
        if 'role="dialog"' in m.group(0):
            continue
        attr = 'role="dialog" aria-modal="true" aria-%s="%s"' % (
            "labelledby" if tipo == "labelledby" else "label", valor)
        tag = m.group(0)
        if dialogo_id in CENTRADOS:
            tag = tag.replace('class="modal"', 'class="modal modal--centered"')
        edits.append((m.start(), m.end(), add_attr(tag, attr)))

    # 2. title_id en las llamadas al macro que no lo tenian.
    for (archivo, cierre), title_id in TITLE_ID_MACRO.items():
        if archivo != rel:
            continue
        encontrada = False
        for m in CALL_RE.finditer(text):
            fin = fin_de_llamada(text, m.end())
            cuerpo = text[m.start():fin]
            if cierre not in cuerpo:
                continue
            encontrada = True
            if "title_id" in cuerpo:
                break
            edits.append((fin - 1, fin - 1, ", title_id='%s'" % title_id))
            break
        if not encontrada:
            warnings.append("%s: no encuentro la llamada al macro con %s" % (rel, cierre))

    # 3. Titulos visibles sin id.
    for archivo, viejo, nuevo in TITULOS:
        if archivo != rel:
            continue
        if nuevo in text:
            continue
        if viejo not in text:
            warnings.append("%s: no encuentro el titulo %s" % (rel, viejo))
            continue
        i = text.index(viejo)
        edits.append((i, i + len(viejo), nuevo))

    # 4. <span class="close-btn"> -> <button type="button">.
    for m in SPAN_CIERRE_RE.finditer(text):
        edits.append((m.start(), m.end(),
                      '<button type="button" class="close-btn" data-modal-close '
                      'aria-label="Cerrar" onclick="%s"><i class="fas fa-xmark"></i></button>'
                      % m.group(1)))

    # 5. data-modal-close en los controles de cierre sin clase reconocible.
    for viejo, nuevo in MARCAR_CIERRE:
        if archivo_no_aplica(rel, viejo, nuevo):
            continue
        if nuevo in text:
            continue
        if viejo not in text:
            warnings.append("%s: no encuentro el control %s" % (rel, viejo[:48]))
            continue
        i = text.index(viejo)
        edits.append((i, i + len(viejo), nuevo))

    # 5b. Nombre accesible en los cierres que ya eran boton.
    for viejo, nuevo in CIERRE_SIN_NOMBRE:
        if rel != "templates/profile/modals.html":
            continue
        if nuevo in text:
            continue
        if viejo not in text:
            warnings.append("%s: no encuentro el cierre %s" % (rel, viejo[:48]))
            continue
        i = text.index(viejo)
        edits.append((i, i + len(viejo), nuevo))

    # 6. Clase modal--centered: va en la edicion del contenedor (ver CENTRADOS).

    return edits, warnings


# Los controles a marcar viven en archivos puntuales: se evita que un texto
# igual en otro template se edite por accidente.
ARCHIVO_MARCA = {
    "confirm-btn-cancel": "templates/components/modals_global.html",
    "choice-btn-cancel": "templates/components/modals_global.html",
    "skipReservationOnboarding()": "templates/profile/modals/onboarding_modal.html",
}


def archivo_no_aplica(rel: str, viejo: str, nuevo: str) -> bool:
    for clave, archivo in ARCHIVO_MARCA.items():
        if clave in viejo:
            return rel != archivo
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Dialogos accesibles (role=dialog + nombre).")
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
        print("%-58s ediciones: %d" % (rel, len(edits)))
        for start, end, replacement in sorted(edits, reverse=True):
            print("      %s" % replacement[:96])
        if args.apply:
            new_text = text
            for start, end, replacement in sorted(edits, reverse=True):
                new_text = new_text[:start] + replacement + new_text[end:]
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
        total += len(edits)

    print("\nTotal de ediciones: %d%s" % (total, "" if args.apply else "  (dry-run)"))
    for w in warnings:
        print("  AVISO: %s" % w)
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
