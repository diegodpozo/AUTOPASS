"""
Motor de capturas de pantalla para los manuales de usuario de AUTOPASS.

Lee `manual/capturas/manifiesto.json`, se loguea con la cuenta indicada para cada
captura, ejecuta los pasos declarados (clics, esperas, scroll) y guarda el
resultado en `manual/assets/img/`.

Uso:
    python manual/tools/capturar.py                 # todas las capturas
    python manual/tools/capturar.py finance metricas   # solo los ids indicados
    python manual/tools/capturar.py --manual admin-sucursal
    python manual/tools/capturar.py --base http://127.0.0.1:8000
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_POR_DEFECTO = "http://127.0.0.1:8000"

RAIZ_MANUAL = Path(__file__).resolve().parents[1]
RAIZ_PROYECTO = RAIZ_MANUAL.parent
RUTA_MANIFIESTO = RAIZ_MANUAL / "capturas" / "manifiesto.json"
RUTA_IMG = RAIZ_MANUAL / "assets" / "img"

CARPETAS_VIGILADAS = (
    RAIZ_PROYECTO / "templates",
    RAIZ_PROYECTO / "static" / "css",
    RAIZ_PROYECTO / "static" / "js",
)

CUENTAS = {
    "local_admin": {"email": "admcastelar@autopass.com", "password": "admin123"},
    "admin": {"email": "admin@autopass.com", "password": "admin123"},
    # No hay usuario "staff" en el seed: crealo antes de capturarlo.
    "staff": None,
    # Cliente real con historial de reservas y 2 vehiculos.
    "cliente": {
        "email": "diegodpozo@hotmail.com",
        "password": "Adridie2332@",
    },
    "anonimo": None,
}

SELECTORES_CIERRE = (
    "#tour-overlay .tour-close",
    ".tour-close",
    "#onboarding-overlay .close",
    "[data-bs-dismiss='modal']",
    ".modal.show .btn-close",
)


def log(mensaje):
    print(mensaje, flush=True)


def login(base, rol):
    """Devuelve el payload de sesion (token, rol, nombre, apellido) del rol pedido."""
    cuenta = CUENTAS[rol]
    if cuenta is None:
        return None
    peticion = urllib.request.Request(
        f"{base}/v1/auth/login",
        data=json.dumps(cuenta).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"[ERROR] Login fallo para {rol}: {error.code} {detalle}") from error


def inyectar_sesion(payload):
    """Script que corre antes de cada carga de pagina para dejar la sesion lista."""
    return """
        localStorage.setItem('token', %s);
        localStorage.setItem('rol', %s);
        localStorage.setItem('nombre', %s);
        localStorage.setItem('apellido', %s);
    """ % (
        json.dumps(payload["access_token"]),
        json.dumps(payload.get("rol", "")),
        json.dumps(payload.get("nombre", "")),
        json.dumps(payload.get("apellido", "")),
    )


def cerrar_overlays(page):
    """Cierra tours de primera visita y modales que tapen la pantalla."""
    for _ in range(4):
        cerrado = False
        for selector in SELECTORES_CIERRE:
            try:
                elemento = page.locator(selector).first
                if elemento.is_visible(timeout=400):
                    elemento.click(timeout=2000)
                    cerrado = True
                    page.wait_for_timeout(400)
            except Exception:
                continue
        if not cerrado:
            break
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
    except Exception:
        pass


def aplicar_pasos(page, pasos):
    for paso in pasos or []:
        if "clic" in paso:
            objetivo = page.locator(paso["clic"]).first
            objetivo.wait_for(state="visible", timeout=15000)
            objetivo.click(timeout=10000)
        elif "clic_texto" in paso:
            page.locator(f"text={paso['clic_texto']}").first.click(timeout=10000)
        elif "espera" in paso:
            page.wait_for_timeout(paso["espera"])
        elif "scroll" in paso:
            page.evaluate(paso["scroll"])
            page.wait_for_timeout(600)
        elif "js" in paso:
            page.evaluate(paso["js"])
            page.wait_for_timeout(600)
        page.wait_for_timeout(paso.get("pausa", 400))


def capturar(base, solamente_ids=None, solamente_manual=None):
    if not RUTA_MANIFIESTO.exists():
        raise SystemExit(f"[ERROR] No existe el manifiesto: {RUTA_MANIFIESTO}")

    manifiesto = json.loads(RUTA_MANIFIESTO.read_text(encoding="utf-8"))
    capturas = manifiesto["capturas"]

    if solamente_manual:
        capturas = [c for c in capturas if c.get("manual") == solamente_manual]
    if solamente_ids:
        capturas = [c for c in capturas if c["id"] in solamente_ids]

    if not capturas:
        raise SystemExit("[ERROR] Ninguna captura coincide con el filtro.")

    RUTA_IMG.mkdir(parents=True, exist_ok=True)

    roles = sorted({c["rol"] for c in capturas})
    sesiones = {}
    for rol in roles:
        if CUENTAS[rol] is None:
            log(f"-> {rol}: sin sesion (captura publica)")
            sesiones[rol] = None
        else:
            log(f"-> Login {rol} ({CUENTAS[rol]['email']})")
            sesiones[rol] = login(base, rol)

    hechas, falladas = 0, 0

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        contextos = {}

        for rol, payload in sesiones.items():
            ctx = navegador.new_context(
                viewport={"width": 1600, "height": 1000},
                device_scale_factor=2,
                locale="es-AR",
                reduced_motion="reduce",
            )
            if payload:
                ctx.add_init_script(inyectar_sesion(payload))
            contextos[rol] = ctx

        for captura in capturas:
            id_captura = captura["id"]
            destino = RUTA_IMG / captura["archivo"]
            ctx = contextos[captura["rol"]]
            pagina = ctx.new_page()

            try:
                pagina.goto(f"{base}{captura.get('url', '/dashboard')}",
                             wait_until="domcontentloaded", timeout=45000)
                pagina.wait_for_timeout(2500)
                cerrar_overlays(pagina)
                aplicar_pasos(pagina, captura.get("pasos"))
                pagina.wait_for_timeout(captura.get("espera_ms", 1500))

                if captura.get("elemento"):
                    pagina.locator(captura["elemento"]).first.screenshot(
                        path=str(destino), timeout=15000)
                else:
                    pagina.screenshot(path=str(destino), full_page=True)

                log(f"[OK]   {id_captura} -> {destino.name}")
                hechas += 1
            except Exception as error:
                log(f"[FALLA] {id_captura}: {type(error).__name__}: {error}")
                falladas += 1
            finally:
                pagina.close()

        for ctx in contextos.values():
            ctx.close()
        navegador.close()

    log("")
    log(f"Capturas generadas: {hechas} | fallidas: {falladas}")
    return 0 if falladas == 0 else 1


def firma_de_archivos():
    """Huella de los archivos que afectan a la interfaz. Si cambia, hay que recapturar."""
    partes = []
    watched = [p for carpeta in CARPETAS_VIGILADAS if carpeta.exists() for p in carpeta.rglob("*")]
    watched.append(RUTA_MANIFIESTO)
    for archivo in watched:
        if archivo.is_file():
            partes.append((str(archivo), archivo.stat().st_mtime))
    return tuple(sorted(partes))


def vigilar(base, solamente_ids=None, solamente_manual=None, intervalo=3):
    """Recaptura automaticamente cada vez que cambia un template, un CSS o un JS."""
    log("=" * 66)
    log("MODO VIGILANDO: las capturas se regeneran solas al cambiar la interfaz.")
    log(f"Revisando cada {intervalo}s. Dejar abierto mientras trabajas. Ctrl+C para salir.")
    log("=" * 66)

    anterior = firma_de_archivos()
    log(f"Estado inicial: {len(anterior)} archivos vigilados. Capturas al dia.")

    try:
        while True:
            time.sleep(intervalo)
            actual = firma_de_archivos()
            if actual == anterior:
                continue

            cambiados = [ruta for (ruta, m), (_, m2)
                         in zip(anterior, actual) if m != m2]
            if len(actual) != len(anterior):
                cambiados.append("(archivos agregados o eliminados)")

            anterior = actual
            log("")
            log("-" * 66)
            log("CAMBIO DETECTADO, regenerando capturas:")
            for ruta in dict.fromkeys(cambiados):
                log(f"  * {ruta.replace(str(RAIZ_PROYECTO) + chr(92), '')}")
            try:
                capturar(base, solamente_ids, solamente_manual)
            except SystemExit as error:
                log(f"El ciclo fallo: {error}")
            log("-" * 66)
    except KeyboardInterrupt:
        log("")
        log("Vigilancia detenida.")


def main():
    parser = argparse.ArgumentParser(description="Genera las capturas de los manuales AUTOPASS.")
    parser.add_argument("ids", nargs="*", help="ids de captura puntuales")
    parser.add_argument("--base", default=BASE_POR_DEFECTO, help="URL base del servidor")
    parser.add_argument("--manual", help="filtra por manual (admin-sucursal, admin-general, cliente)")
    parser.add_argument("--vigilar", action="store_true",
                        help="recaptura automaticamente cuando cambia la interfaz")
    parser.add_argument("--intervalo", type=int, default=3, help="segundos entre chequeos (modo vigilar)")
    argumentos = parser.parse_args()

    if argumentos.vigilar:
        vigilar(argumentos.base, argumentos.ids or None, argumentos.manual, argumentos.intervalo)
        return

    sys.exit(capturar(argumentos.base, argumentos.ids or None, argumentos.manual))


if __name__ == "__main__":
    main()