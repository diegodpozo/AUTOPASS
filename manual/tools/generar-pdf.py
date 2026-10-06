"""
Genera la version PDF de los manuales AUTOPASS usando el motor de Chromium
(Playwright), que es el mismo que dibuja el HTML: por eso el PDF conserva
exactamente la estetica del manual en pantalla.

Lo que agrega respecto de una impresion normal del HTML:
  - portada propia
  - indice con numero de pagina REAL, en dos pasadas
  - cada entrada del indice es un link que salta a su pagina
  - marcadores (bookmarks) navegables en el panel del lector de PDF
  - PDF etiquetado (accesibilidad)
  - paginado sin cortes: la portada sola, cada seccion en pagina nueva, los
    temas (<h3> + contenido) nunca partidos, imagenes y tablas intactas
  - encabezado con el nombre del manual y pie con "Pagina X de Y"

Como se consigue el numero de pagina real:
  pasada 1 -> se imprime con marcadores de posicion y se lee en que pagina
              cayo cada titulo
  pasada 2 -> se imprime de nuevo con los numeros definitivos. El alto del
              indice no cambia, asi que la paginacion es identica.

Uso:
    python manual/tools/generar-pdf.py
    python manual/tools/generar-pdf.py admin-sucursal
    python manual/tools/generar-pdf.py --todos
"""

import argparse
import html
import re
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader
from playwright.sync_api import sync_playwright

RAIZ_MANUAL = Path(__file__).resolve().parents[1]
RUTA_PDF = RAIZ_MANUAL / "pdf"

MANUALES = {
    "admin-sucursal": "Manual del Administrador de Sucursal",
    "admin-general": "Manual del Administrador General",
    "cliente": "Manual del Cliente",
}

MARCA_INDICE = "INDICE-GENERADO-POR-SCRIPT"


# --------------------------------------------------------------------------
# Preparacion del DOM: ids estables + bloque de indice
# --------------------------------------------------------------------------

AGREGAR_INDICE = """
(marca) => {
  const Normalizar = (texto) => texto.toLowerCase()
    .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  const usados = new Set();
  const slug = (texto) => {
    let base = Normalizar(texto) || 'sec';
    let candidato = base, i = 2;
    while (usados.has(candidato)) { candidato = base + '-' + i; i++; }
    usados.add(candidato);
    return candidato;
  };

  const entradas = [];

  // Un <h2> por seccion y un <h3> por tema. El indice los recorre en orden.
for (const seccion of document.querySelectorAll('.seccion')) {
      for (const titulo of seccion.querySelectorAll('h2, h3')) {
        // El <h2> arma el titulo como "1." + "Antes de empezar": en el indice
        // hay que devolverle el espacio que el CSS pone al imprimir.
        const texto = titulo.textContent.trim().replace(/^(\\d+\\.)\\s*/, '$1 ');
        const id = titulo.id || slug(texto);
        titulo.id = id;
        entradas.push({ id: id, titulo: texto, nivel: titulo.tagName === 'H2' ? 1 : 2 });
      }
    }

  // Armando el HTML del indice con puntos guia y link a cada tema.
  const filas = entradas.map((e) => {
    const clase = 'indice-fila nivel-' + e.nivel;
    const pagina = e.__pagina !== undefined ? e.__pagina : '--';
    return '<div class="' + clase + '">'
      + '<a href="#' + e.id + '">'
      + '<span class="idx-titulo">' + e.titulo + '</span>'
      + '<span class="idx-puntos"></span>'
      + '<span class="idx-pag" data-pagina="' + e.id + '">' + pagina + '</span>'
      + '</a></div>';
  }).join('');

  const bloque = document.createElement('section');
  bloque.className = 'indice-pdf solo-pdf';
  bloque.innerHTML =
    '<header><div class="marca">AUTOPASS</div><h2>Indice</h2></header>'
    + filas
    + '<p class="pie-indice">Los titulos del indice son links: hacé clic para ir '
    + 'directo a esa pagina.</p>'
    + '<span class="marca-indice" style="display:none">' + marca + '</span>';

  // El indice va entre la portada y la primera seccion.
  const portada = document.querySelector('.portada');
  if (portada && portada.nextSibling) {
    portada.parentNode.insertBefore(bloque, portada.nextSibling);
  } else {
    document.body.insertBefore(bloque, document.body.firstChild);
  }

  return entradas;
}
"""


# --------------------------------------------------------------------------
# Agrupacion de temas para que no se partan al imprimirse
# --------------------------------------------------------------------------

AGRUPAR_TEMAS = """
() => {
  // Cada <h3> se agrupa con su contenido en un div.tema. El parrafo de
  // entrada de la seccion se suma al PRIMER tema; si no, el titulo y la
  // introduccion quedan solos en una pagina.
  const secciones = document.querySelectorAll('.seccion');
  let creadas = 0;

  for (const seccion of secciones) {
    let grupo = null;

    for (const hijo of Array.from(seccion.children)) {
      if (hijo.tagName === 'H2') { grupo = null; continue; }
      if (hijo.tagName === 'H3' && grupo && grupo.querySelector('h3')) { grupo = null; }

      if (!grupo) {
        grupo = document.createElement('div');
        grupo.className = 'tema';
        seccion.insertBefore(grupo, hijo);
        creadas++;
      }
      grupo.appendChild(hijo);
    }
  }
  return creadas;
}
"""


def normalizar(texto):
    """Compacta el texto para comparar el HTML con lo extraido del PDF.

    El HTML de los <h2> arma el titulo como "1." + "Antes de empezar", sin
    espacio entre medio, pero el PDF lo imprime con espacio. Por eso se
    comparan solo letras y numeros, en minuscula y sin espacios.
    """
    descompuesto = unicodedata.normalize("NFD", texto or "")
    ascii_ = descompuesto.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]", "", ascii_)


def esperar_carga(page):
    page.wait_for_load_state("networkidle", timeout=60000)
    page.evaluate("async () => { await document.fonts.ready; }")
    page.evaluate("""
        async () => {
          const imagenes = Array.from(document.images).filter(i => !i.complete);
          await Promise.all(imagenes.map(i => new Promise(res => {
            i.addEventListener('load', res, {once: true});
            i.addEventListener('error', res, {once: true});
          })));
        }
    """)
    page.wait_for_timeout(1200)


def aplicar_paginas(page):
    """Aplica el numero de pagina real a cada entrada del indice."""
    def poner(numero):
        page.evaluate(
            "(n) => { for (const el of document.querySelectorAll('[data-pagina]'))"
            " el.textContent = n[el.dataset.pagina]; }",
            numero,
        )

    return poner


def mover_si_puede(origen, destino):
    """Reemplaza el destino moviendo el archivo.

    Acrobat y los visores de PDF de Windows mantienen el archivo abierto, asi
    que no se puede sobrescribir. En vez de romper con un error, se escribe al
    lado y se avisa.
    """
    import os
    try:
        os.replace(origen, destino)
        return destino
    except PermissionError:
        alternativo = destino.with_name(destino.stem + "-nuevo" + destino.suffix)
        os.replace(origen, alternativo)
        return alternativo


def imprimir_pdf(page, destino, titulo):
    cabecera = f"""
      <div style="font-size:7.5pt; font-family:Segoe UI,sans-serif; color:#767f95;
                  width:100%; padding:0 14mm; display:flex; justify-content:space-between;">
        <span>{html.escape(titulo)}</span>
        <span>AUTOPASS</span>
      </div>
    """
    pie = """
      <div style="font-size:7.5pt; font-family:Segoe UI,sans-serif; color:#767f95;
                  width:100%; padding:0 14mm; display:flex; justify-content:space-between;
                  align-items:center;">
        <span>Documento de uso interno</span>
        <span>Pagina <span class="pageNumber"></span> de <span class="totalPages"></span></span>
      </div>
    """
    page.emulate_media(media="print")
    temporal = destino.with_name(destino.stem + ".tmp" + destino.suffix)
    page.pdf(
        path=str(temporal),
        format="A4",
        print_background=True,
        display_header_footer=True,
        header_template=cabecera,
        footer_template=pie,
        margin={"top": "13mm", "bottom": "12mm", "left": "0mm", "right": "0mm"},
        outline=True,
        tagged=True,
    )
    return mover_si_puede(temporal, destino)


def paginas_de_titulos(destino, entradas):
    """Lee el PDF de la pasada 1 y deduce en que pagina cae cada titulo."""
    lector = PdfReader(str(destino))
    textos = [normalizar(pagina.extract_text() or "") for pagina in lector.pages]
    titulos = [normalizar(e["titulo"]) for e in entradas if e["titulo"]]

    # Las paginas del indice repiten TODOS los titulos. Se detectan porque
    # concentran muchos de golpe: si una pagina trae mas de la mitad de los
    # titulos, es indice y no contenido.
    umbral = max(3, int(len(titulos) * 0.6))
    paginas_indice = set()
    for i, texto in enumerate(textos):
        cuantos = sum(1 for t in titulos if t and t in texto)
        if cuantos >= umbral:
            paginas_indice.add(i)

    numeros = {}
    cursor = 0
    for entrada in entradas:
        objetivo = normalizar(entrada["titulo"])
        if not objetivo:
            continue

        encontrado = None
        # Barrido en orden: cada titulo esta despues del anterior.
        for i in range(cursor, len(textos)):
            if i in paginas_indice:
                continue
            if objetivo in textos[i]:
                encontrado = i + 1
                cursor = i
                break

        if encontrado is None:
            for i in range(len(textos)):
                if i not in paginas_indice and objetivo in textos[i]:
                    encontrado = i + 1
                    break

        numeros[entrada["id"]] = encontrado if encontrado else ""

    return numeros, len(lector.pages), sorted(paginas_indice)


def titulos_huerfanos(destino, entradas, indices_indice):
    """Ids de los titulos que quedaron solos al pie de una pagina.

    Chromium no siempre respeta "break-after: avoid": si despues del titulo
    hay un bloque largo, lo deja pegado al final de la pagina y el texto se
    va a la siguiente. Es el unico defecto de paginacion que no se puede
    resolver solo con CSS, asi que se detecta desde el PDF y se corrige
    forzando un salto antes del titulo.
    """
    lector = PdfReader(str(destino))
    indice = set(indices_indice)
    total = len(lector.pages)
    por_titulo = {normalizar(e["titulo"]): e["id"] for e in entradas if e["titulo"]}

    huerfanos = []
    for i, pagina in enumerate(lector.pages):
        if i in indice or i == total - 1:
            continue
        lineas = [l.strip() for l in (pagina.extract_text() or "").splitlines() if l.strip()]
        # Se descartan el encabezado y el pie que agrega el visor.
        while lineas and ("AUTOPASS" in lineas[-1] or "Pagina" in lineas[-1]):
            lineas.pop()
        if not lineas:
            continue
        clave = normalizar(lineas[-1])
        # Solo cuenta si la ultima linea ES un titulo del manual: asi los
        # pies de imagen o parrafos que empiezan con una palabra suelta
        # ("Ayuda y Soporte. ...") no se confunden con un titulo.
        if clave and clave in por_titulo:
            huerfanos.append(por_titulo[clave])

    return huerfanos


def forzar_saltos(page, ids):
    """Marca los titulos huerfanos para que el tema arranque en pagina nueva."""
    page.evaluate(
        """(ids) => {
            for (const id of ids) {
              const el = document.getElementById(id);
              if (el) {
                el.classList.add('salto');
                const tema = el.closest('.tema');
                if (tema) tema.classList.add('salto');
              }
            }
        }""",
        ids,
    )
    page.wait_for_timeout(400)


def generar(nombre_manual, pagina, contexto, titulo):
    origen = RAIZ_MANUAL / f"{nombre_manual}.html"
    if not origen.exists():
        return None, f"no existe {origen.name}"

    destino = RUTA_PDF / f"{nombre_manual}.pdf"
    pagina.goto(origen.as_uri(), wait_until="domcontentloaded", timeout=60000)
    esperar_carga(pagina)

    temas = pagina.evaluate(AGRUPAR_TEMAS)
    entradas = pagina.evaluate(AGREGAR_INDICE, MARCA_INDICE)
    pagina.wait_for_timeout(600)

# --- Pasada 1: se imprime en una carpeta temporal para descubrir la paginacion ---
    import tempfile
    with tempfile.TemporaryDirectory() as temporal:
        borrador = Path(temporal) / f"{nombre_manual}.pdf"
        imprimir_pdf(pagina, borrador, titulo)
        numeros, total, indices = paginas_de_titulos(borrador, entradas)
        huerfanos = titulos_huerfanos(borrador, entradas, indices)

    faltantes = [e["titulo"] for e in entradas if not numeros.get(e["id"])]

    # --- Titulos que quedaron solos al pie: se fuerzan a pagina nueva ---
    if huerfanos:
        forzar_saltos(pagina, huerfanos)
        print(f"     [OK] {len(huerfanos)} titulo(s) huerfano(s) a pagina nueva")

    # --- Pasada 2: con los numeros definitivos, al destino real ---
    if faltantes:
        print(f"     aviso: {len(faltantes)} titulo(s) sin pagina detectada")
    aplicar_paginas(pagina)(numeros)
    pagina.wait_for_timeout(500)
    final = imprimir_pdf(pagina, destino, titulo)

    if final.name != destino.name:
        print(f"     AVISO: {destino.name} estaba abierto en un visor.")
        print(f"            El PDF nuevo quedo en {final.name}")
        print("            Cerra el PDF abierto y volve a correr el comando.")

    detalle = (f"{temas} temas, {len(entradas)} entradas de indice, "
               f"{total} paginas, indice en {[i + 1 for i in indices]}, "
               f"{final.stat().st_size / 1024 / 1024:.1f} MB")
    return final, detalle


def main():
    parser = argparse.ArgumentParser(description="Genera los PDF de los manuales AUTOPASS.")
    parser.add_argument("manual", nargs="?", help="nombre del manual (sin .html)")
    parser.add_argument("--todos", action="store_true", help="genera todos los que existan")
    argumentos = parser.parse_args()

    RUTA_PDF.mkdir(parents=True, exist_ok=True)

    if argumentos.manual:
        objetivos = [argumentos.manual]
    elif argumentos.todos:
        objetivos = list(MANUALES)
    else:
        objetivos = [n for n in MANUALES if (RAIZ_MANUAL / f"{n}.html").exists()]

    if not objetivos:
        print("No hay manuales para convertir.")
        return 1

    print(f"Generando PDF de: {', '.join(objetivos)}\n")

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        contexto = navegador.new_context(viewport={"width": 1280, "height": 900},
                                         locale="es-AR")

        for nombre in objetivos:
            if nombre not in MANUALES:
                print(f"[SKIP] {nombre}: nombre desconocido.")
                continue

            pagina = contexto.new_page()
            titulo = MANUALES[nombre]
            destino, detalle = generar(nombre, pagina, contexto, titulo)
            pagina.close()

            if destino is None:
                print(f"[SKIP] {nombre}: {detalle}")
            else:
                print(f"[OK]   {destino.name}  ({detalle})")

        contexto.close()
        navegador.close()

    print(f"\nPDF en: {RUTA_PDF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())