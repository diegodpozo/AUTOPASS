"""
Verificacion del PDF de los manuales: detecta paginas en blanco, cortes
desafortunados y secciones que no arrancan en pagina nueva.

No reemplaza mirar el PDF a ojo, pero avisa de los problemas mecanicos mas
comunes de un paginado automatico.
"""

import re
import sys
from pathlib import Path

from pypdf import PdfReader

RAIZ_MANUAL = Path(__file__).resolve().parents[1]
RUTA_PDF = RAIZ_MANUAL / "pdf"

UMBRAL_PAGINA_VACIA = 60
UMBRAL_PAGINA_ESCASA = 320


RUZOS = re.compile(r"(Pagina\s*\d+\s*de\s*\d+|Documento de uso interno|AUTOPASS)")

PATRON_TITULO = re.compile(r"^\s*\d+\.\s+\S|^\s*(Vehiculos|Movimientos|Reservas|Usuarios|Metricas|Promociones|Tickets|Configuracion|Ayuda|Problemas|Tarifario|Plazas|Monitoreo|Sistema|Barreras|Ingreso|Reporte|Soporte)\b")


def lineas_de_contenido(pagina):
    texto = pagina.extract_text() or ""
    lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]
    return [linea for linea in lineas if not RUZOS.search(linea)]


def titulo_al_pie(linea):
    """True si la ultima linea de la pagina parece un titulo suelto."""
    # Los contadores CSS de las listas numeradas quedan pegados al texto como
    # "Guardá.6": hay que quitar SOLO el numero del contador, no el punto final.
    linea = re.sub(r"\d+$", "", linea.strip()).strip()
    if not linea:
        return False
    if len(linea) > 90 or linea.endswith((".", ":", ",", ";")):
        # Un titulo es corto y no termina en puntuacion. Los pies de imagen y
        # los parrafos arrancan con la palabra del titulo ("Ayuda y Soporte.
        # ...") pero son varias lineas y terminan en punto.
        return False
    if PATRON_TITULO.match(linea):
        return True
    if len(linea) < 60 and not linea.endswith((".", ":", ",", ";")) and not linea[0].isdigit():
        return True
    return False


def imagenes_de(pagina):
    try:
        recursos = pagina.get("/Resources", {})
        xobjects = recursos.get("/XObject", {})
        return sum(1 for _ in xobjects.get_object().values())
    except Exception:
        return 0


def texto_util(texto):
    """Saca encabezado, pie y numeros de pagina para medir el contenido real."""
    limpio = re.sub(r"Pagina\s*\d+\s*de\s*\d+", "", texto or "")
    limpio = re.sub(r"AUTOPASS", "", limpio)
    limpio = re.sub(r"Documento de uso interno", "", limpio)
    limpio = re.sub(r"Manual del \w+[\w\s]*", "", limpio, count=1)
    return re.sub(r"\s+", " ", limpio).strip()


def normalizar(texto):
    return re.sub(r"[^a-z0-9]", "", (texto or "").lower())


def verificar_indice(lector, problemas):
    """El indice debe tener entradas con numero de pagina y links internos."""
    if len(lector.pages) < 2:
        return

    pagina_indice = lector.pages[1]
    texto = normalizar(pagina_indice.extract_text() or "")

    if "indice" not in texto:
        problemas.append("no se encontro el indice en la pagina 2")
        return

    # Cada entrada del indice es un link con su numero de pagina al lado,
    # asi que el conteo de links es el conteo de entradas reales.
    links = 0
    for anotacion in pagina_indice.get("/Annots", []) or []:
        try:
            objeto = anotacion.get_object()
            if objeto.get("/Subtype") == "/Link" and (
                    objeto.get("/Dest") is not None or objeto.get("/A") is not None):
                links += 1
        except Exception:
            continue

    print(f"Indice: {links} entradas con link interno")
    if links == 0:
        problemas.append("el indice no tiene links internos navegables")
    if not re.search(r"\d", texto):
        problemas.append("el indice no muestra numeros de pagina")
    return links


def contar_nodos(nodo):
    """Cuenta el outline entero, hijos y hermanos, porque van anidados."""
    total = 0
    actual = nodo.get_object().get("/First")
    while actual is not None:
        objeto = actual.get_object()
        total += 1
        if "/First" in objeto:
            total += contar_nodos(objeto)
        siguiente = objeto.get("/Next")
        actual = siguiente.get_object() if siguiente is not None else None
    return total


def verificar_marcadores(lector, problemas):
    """Los marcadores (outline) son el panel lateral del lector de PDF."""
    try:
        esquema = lector.trailer["/Root"]
        if "/Outlines" not in esquema:
            problemas.append("el PDF no tiene marcadores (outline)")
            return 0
        conteo = contar_nodos(esquema["/Outlines"])
        print(f"Marcadores (outline): {conteo} entradas")
        if conteo < 10:
            problemas.append("el outline tiene pocas entradas")
        return conteo
    except Exception as error:
        problemas.append(f"no se pudo leer el outline: {error}")
        return 0


def empieza_seccion(texto):
    """True si la pagina arranca con un titulo de seccion numerado ("6. Tickets")."""
    for linea in texto.splitlines():
        limpia = linea.strip()
        if not limpia:
            continue
        return bool(re.match(r"^\d{1,2}\.\s+\S", limpia))
    return False


def verificar(archivo):
    lector = PdfReader(str(archivo))
    total = len(lector.pages)
    problemas = []
    notas = []
    print(f"{archivo.name}: {total} paginas, "
          f"{archivo.stat().st_size / 1024 / 1024:.1f} MB\n")

    print(f"{'pag':>4} {'caracteres':>11} {'imagenes':>9}  estado")
    print("-" * 62)

    # Textos de todas las paginas: hace falta ver la siguiente para saber si
    # una pagina escasa es el cierre de una seccion (normal) o un hueco real.
    textos = [texto_util(p.extract_text() or "") for p in lector.pages]

    # El indice (siempre la pagina 2, ver verificar_indice) repite todos los
    # titulos uno tras otro: es normal que su ultima linea sea un titulo, asi
    # que no se controla como pagina con titulo huerfano.
    paginas_indice = {1} if len(lector.pages) > 1 else set()

    for indice, pagina in enumerate(lector.pages, start=1):
        texto = textos[indice - 1]
        imagenes = imagenes_de(pagina)
        largo = len(texto)

        estado = "OK"
        detalle = ""
        if largo == 0 and imagenes == 0:
            estado = "VACIA"
            problemas.append(f"pagina {indice} en blanco")
        elif largo < UMBRAL_PAGINA_VACIA:
            estado = "casi vacia"
            problemas.append(f"pagina {indice} con apenas {largo} caracteres")
        elif largo < UMBRAL_PAGINA_ESCASA and imagenes == 0:
            # Si la pagina siguiente arranca una seccion nueva, esta es solo la
            # cola de la anterior: cada seccion empieza en pagina propia. La
            # ultima pagina del documento es corta por definicion.
            cierra_seccion = (indice < total
                              and empieza_seccion(textos[indice]))
            ultima = indice == total
            if cierra_seccion or ultima:
                estado = "cierre"
                motivo = "cola de seccion" if cierra_seccion else "ultima pagina"
                detalle = f"  ({motivo})"
                notas.append(f"pagina {indice} {motivo} con {largo} car.")
            else:
                estado = "escasa"
                problemas.append(
                    f"pagina {indice} con poco contenido y sin imagen ({largo} car.)")

        lineas = lineas_de_contenido(pagina)
        if (lineas and titulo_al_pie(lineas[-1])
                and indice != total and (indice - 1) not in paginas_indice):
            detalle = f"  <- titulo al pie: '{lineas[-1][:44]}'"
            problemas.append(f"pagina {indice} termina en un titulo: '{lineas[-1][:44]}'")

        print(f"{indice:>4} {largo:>11} {imagenes:>9}  {estado}{detalle}")

    print()
    for nota in notas:
        print(f"Nota: {nota}")
    if notas:
        print()
    verificar_indice(lector, problemas)
    verificar_marcadores(lector, problemas)

    if problemas:
        print(f"Problemas ({len(problemas)}):")
        for problema in problemas:
            print(f"  - {problema}")
    else:
        print("Sin problemas mecanicos: sin paginas vacias, sin cortes sospechosos")
        print("y sin titulos huerfanos al pie de pagina.")
    return problemas


def main():
    archivos = sorted(RUTA_PDF.glob("*.pdf")) if len(sys.argv) < 2 else [
        RUTA_PDF / f"{sys.argv[1]}.pdf"]
    if not archivos or not archivos[0].exists():
        print("No hay PDF generados. Corré: python manual/tools/generar-pdf.py")
        return 1

    for archivo in archivos:
        verificar(archivo)
        print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())