"""Enlaza menciones de archivos y funciones dentro de 'EXPLICACION DE CODIGO/pregunta_*.html'.

Reglas:
  - Span 'cd-l-file' con texto 'ruta.ext:linea' -> enlace a archivos/ruta.ext.html.
  - Span 'pg-ref' con texto de archivo -> mismo criterio.
  - <code>EXPR</code> cuyo EXPR es un simbolo conocido -> enlace a la tarjeta del
    simbolo (archivos/<ruta>.html#sym-<slug>).
  - Span 'pg-ref' cuyo texto es un simbolo (p.ej. 'Clase.metodo') -> igual criterio.

Desambiguacion por contexto: los archivos declarados en el mismo paso (cd-l-file)
tienen prioridad; si no, se exige coincidencia unica global.

Idempotente: antes de enlazar desenvuelve los <a class="cd-link" ...>...</a> previos.

Uso:
    .\\venv\\Scripts\\python.exe _tools\\crosslink_preguntas.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "EXPLICACION DE CODIGO"
ARCHIVOS = DOCS / "archivos"

RE_ANCLA = re.compile(
    r'<div id="(sym-[^"]+)" class="cd-sym[^"]*">\s*<div class="cd-sym-head">\s*'
    r'<span class="cd-badge[^"]*">[^<]*</span>\s*<span class="cd-sym-name">(.*?)</span>\s*</div>',
    re.S,
)
RE_TAG = re.compile(r"<[^>]*>")
RE_DESENVOLVER = re.compile(r'<a class="cd-link" href="[^"]*">(.*?)</a>', re.S)

GENERICOS = {
    "add", "commit", "refresh", "flush", "rollback", "close", "get", "post", "put",
    "patch", "delete", "first", "all", "now", "filter", "filter_by", "join", "query",
    "read", "write", "open", "load", "save", "update", "create", "init", "main",
}

Informe: list[str] = []


def ruta_origen(ruta_archivo_html: Path) -> str:
    return ruta_archivo_html.relative_to(ARCHIVOS).as_posix()[:-5]


def construir_indice() -> tuple[dict[str, list[tuple[str, str]]], set[str]]:
    indices: dict[str, list[tuple[str, str]]] = {}
    rutas_validas: set[str] = set()
    for archivo in ARCHIVOS.rglob("*.html"):
        ruta = ruta_origen(archivo)
        rutas_validas.add(ruta)
        for m in RE_ANCLA.finditer(archivo.read_text(encoding="utf-8")):
            nombre = RE_TAG.sub("", m.group(2)).strip().split(".")[-1].strip()
            if not nombre:
                continue
            lista = indices.setdefault(nombre, [])
            if (ruta, m.group(1)) not in lista:
                lista.append((ruta, m.group(1)))
    return indices, rutas_validas


def elegir(nombre: str, ctx: set[str], indices) -> tuple[str, str] | None:
    entradas = indices.get(nombre)
    if not entradas:
        return None
    if ctx:
        en_ctx = [e for e in entradas if e[0] in ctx]
        if en_ctx:
            return en_ctx[0]
    return entradas[0] if len(entradas) == 1 else None


def candidato_simbolo(expr: str) -> str | None:
    expr = expr.strip()
    expr = re.sub(r"\(.*\)$", "", expr, flags=re.S).strip().strip("` ")
    if not re.fullmatch(r"[A-Za-z_][\w.]*", expr):
        return None
    segmentos = expr.split(".")
    completo = segmentos[-1]
    if len(segmentos) > 1 and segmentos[-2][:1].islower() and completo in GENERICOS:
        return None
    if completo.lower() in ("self", "cls", "true", "false", "none"):
        return None
    return completo


def envolver(inner: str, ruta: str, ancla: str | None) -> str:
    href = f"archivos/{ruta}.html" + (f"#{ancla}" if ancla else "")
    return f'<a class="cd-link" href="{href}">{inner}</a>'


class Pagina:
    def __init__(self, texto: str, indices, rutas_validas):
        self.indices = indices
        self.rutas_validas = rutas_validas
        self.secciones = []
        for m in re.finditer(r'<section class="cd-l-step">', texto):
            fin = texto.find("</section>", m.end())
            fin = fin if fin != -1 else len(texto)
            self.secciones.append((m.start(), fin, texto[m.start():fin]))

    def ctx(self, pos: int) -> set[str]:
        for ini, fin, trozo in self.secciones:
            if ini <= pos < fin:
                rutas = {
                    r.split(":")[0].strip()
                    for r in re.findall(r'<span class="cd-l-file">([^<]+)</span>', trozo)
                }
                return {p for p in rutas if p in self.rutas_validas}
        return set()


def enlazar_archivo_span(texto: str, rutas_validas) -> str:
    def rep_file(m: re.Match) -> str:
        bruto = m.group(1)
        ruta = bruto.split(":")[0].strip()
        if ruta in rutas_validas:
            return envolver(f'<span class="cd-l-file">{bruto}</span>', ruta, None)
        Informe.append(f"[SIN RUTA] {bruto}")
        return m.group(0)

    def rep_ref(m: re.Match) -> str:
        bruto = m.group(1)
        ruta = bruto.split(":")[0].strip()
        if re.search(r"\.(py|js|css|html)($|:)", ruta) and ruta in rutas_validas:
            return envolver(f'<span class="pg-ref">{bruto}</span>', ruta, None)
        return m.group(0)

    texto = re.sub(r'<span class="cd-l-file">([^<]+)</span>', rep_file, texto)
    return re.sub(r'<span class="pg-ref">([^<]+)</span>', rep_ref, texto)


def enlazar_codigo(texto: str, indices, rutas_validas) -> str:
    pagina = Pagina(texto, indices, rutas_validas)

    def rep_code(m: re.Match) -> str:
        cand = candidato_simbolo(m.group(1))
        if not cand:
            return m.group(0)
        elegido = elegir(cand, pagina.ctx(m.start()), indices)
        if not elegido:
            return m.group(0)
        return envolver(f"<code>{m.group(1)}</code>", elegido[0], elegido[1])

    def rep_ref(m: re.Match) -> str:
        bruto = m.group(1)
        cand = candidato_simbolo(bruto)
        if not cand:
            return m.group(0)
        elegido = elegir(cand, pagina.ctx(m.start()), indices)
        if not elegido:
            return m.group(0)
        return envolver(f'<span class="pg-ref">{bruto}</span>', elegido[0], elegido[1])

    texto = re.sub(r"<code>(.*?)</code>", rep_code, texto, flags=re.S)
    pagina = Pagina(texto, indices, rutas_validas)
    return re.sub(r'<span class="pg-ref">([^<]+)</span>', rep_ref, texto)


def procesar(archivo: Path, indices, rutas_validas) -> None:
    texto = archivo.read_text(encoding="utf-8")
    texto = RE_DESENVOLVER.sub(r"\1", texto)
    texto = enlazar_archivo_span(texto, rutas_validas)
    texto = enlazar_codigo(texto, indices, rutas_validas)
    archivo.write_text(texto, encoding="utf-8")


def main() -> None:
    indices, rutas_validas = construir_indice()
    preguntas = sorted(DOCS.glob("pregunta_*.html"))
    for archivo in preguntas:
        procesar(archivo, indices, rutas_validas)
    print(f"Simbolos: {len(indices)} | Rutas: {len(rutas_validas)} | Preguntas: {len(preguntas)}")
    print(f"Avisos: {len(Informe)}")
    for linea in Informe[:80]:
        print("  " + linea)


if __name__ == "__main__":
    main()
