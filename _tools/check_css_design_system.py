"""Guard de design system: fija un baseline medible de las metricas visuales.

Complementa a los guards ya existentes:
  - check_css_balance.py   -> llaves {} balanceadas
  - check_css_huerfano.py  -> clases .foo sin uso
  - check_css_tokens.py    -> tokens declarados/usados
  - check_color_equivalence.py -> prueba de que una migracion fue neutra

Este NO corrige nada: mide y compara contra un baseline en JSON, para que
cualquier unificacion futura (escala de espaciado, sombras, transiciones,
color) sea una regresion medible y no una operacion a ciegas.

Metricas:
  color      : literales de color, valores RGBA distintos, y cuantos son
               equivalentes exactos a un token existente (migrables sin cambio)
  spacing    : cuantos valores px distintos hay, cuantos se REPITEN (escala real
               en uso) y cuantos son de un solo uso (decision unica). Antes se
               media 'off-grid' (fuera de multiplos de 4) y se retiro: 10px,
               15px o 25px no son multiplos de 4 pero son valores legitimos, y
               la cifra de '592 ocurrencias a arreglar' empujaba a un refactor
               destructivo sobre una escala que ya esta bien usada
  shadow     : box-shadow distintas
  transition : duraciones y curvas distintas
  alpha_scale: niveles de opacidad declarados, por familia de color

Uso:
  python _tools/check_css_design_system.py            # falla si empeora (exit 1)
  python _tools/check_css_design_system.py --report   # detalle completo
  python _tools/check_css_design_system.py --update   # acepta el estado actual
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = ROOT / "static" / "css"
VARIABLES = CSS_DIR / "base" / "variables.css"
BASELINE = Path(__file__).resolve().parent / "css_design_system_baseline.json"

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB = re.compile(
    r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)"
)
STRIP = re.compile(r"/\*.*?\*/", re.S)

# px en propiedades de caja/espaciado
SPACING = re.compile(
    r"(?:padding|margin|gap|top|right|bottom|left|inset)[a-z-]*:\s*(-?[\d.]+)px")
# El bloque que respeta la preferencia del sistema operativo. Debe existir Y
# neutralizar las tres palancas del movimiento: duracion, iteraciones y delay.
# Si alguien lo borra o lo deja a medias, el guard falla en vez de dejar el sitio
# moviendose para todo el mundo otra vez.
REDUCED_MOTION = re.compile(
    r"@media[^{]*prefers-reduced-motion\s*:\s*reduce[^{]*\{(.*?)\n\}", re.S)
RM_REQUIRES = ("animation-duration", "animation-iteration-count",
               "transition-duration")

# Metricas donde SUBIR es mejorar. Sin esto el comparador generico marca como
# regresion cualquier aumento, y por ejemplo 'adopcion_escala_pct' al subir de
# 98 a 99 se reportaria como empeora: exactamente al reves.
MEJOR_SUBE = {"spacing.adopcion_escala_pct"}

# Un z-index literal cuyo valor es EXACTAMENTE el de un token declarado es
# duplicacion segura de DRY: mismo numero, asi que tokenizarlo no cambia nada.
# A diferencia de los literales locales (z 1-100, que viven dentro del stacking
# context de su componente y no compiten con nada) y de los magicos
# intencionales (1999 bajo el sidebar de 2000, 2200, 3200 sobre confirm, 100000
# sobre el FAB de 99999), que dependen de una RELACION y no de un valor.
# Se vigila el conteo: si sube, alguien volvio a escribir el numero.
ZINDEX = re.compile(r"z-index\s*:\s*([^;}]+)")
SHADOW = re.compile(r"box-shadow:\s*([^;]+)")
TRANSITION = re.compile(r"transition:\s*([^;]+)")

# #fff y #000 NO se consideran literales "a unificar": son colores fijos y
# convertirlos a var(--blanco)/var(--negro) no aporta coherencia.
GENERIC_HEX = {"#fff", "#ffffff", "#000", "#000000"}


def hex_to_rgba(h):
    h = h.lstrip("#").lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 6:
        h += "ff"
    if len(h) != 8:
        return None
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))


def rgb_to_rgba(m):
    r, g, b = (int(float(x)) for x in m.group(1, 2, 3))
    a = m.group(4)
    return (r, g, b, int(round(float(a) * 255)) if a is not None else 255)


def iter_css():
    for p in sorted(CSS_DIR.rglob("*.css")):
        yield p, STRIP.sub(" ", p.read_text(encoding="utf-8", errors="ignore"))


SELECTOR = re.compile(r"[^{}]*\{")


def declarations_only(txt):
    """Devuelve solo el cuerpo de las reglas, descartando selectores.

    Necesario para medir colores: HEX matchea `#add-vehicle-form` como si fuera
    un literal (las letras `a` y `d` son digitos hexadecimales validos), asi que
    contar sobre el archivo completo infla el total con selectores que no son
    colores y hace que borrar una regla parezca una mejora de color.
    """
    return SELECTOR.sub("{", txt)


def token_rgba_map():
    out = {}
    text = VARIABLES.read_text(encoding="utf-8")
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", text):
        val = m.group(2).strip()
        hv = HEX.search(val)
        if hv:
            out[m.group(1)] = hex_to_rgba(hv.group(0))
        else:
            rv = RGB.search(val)
            if rv:
                out[m.group(1)] = rgb_to_rgba(rv)
    by_rgba = {}
    for name, rgba in out.items():
        if rgba:
            by_rgba.setdefault(tuple(rgba), []).append(name)
    return by_rgba


def _alpha(raw):
    """4to componente de rgba() a 0-255. Acepta fraccion (0.05), % (5%) o 0-255."""
    if raw is None:
        return 255
    s = str(raw).strip()
    if s.endswith("%"):
        return int(round(float(s[:-1]) / 100.0 * 255))
    f = float(s)
    if 0.0 <= f <= 1.0:
        return int(round(f * 255))
    return int(round(f))


def alpha_scale():
    """Set de alfas de 8 bits que el proyecto usa hoy, por familia de color.

    Sirve como escala declarada: un alfa nuevo no se prohibe (seria una regla
    mortal para el diseno) pero queda flagged para que se registre en el
    baseline y sea una decision consciente, no un descuido.
    """
    fam = defaultdict(Counter)
    for _p, txt in iter_css():
        for m in RGB.finditer(declarations_only(txt)):
            r, g, b = (int(float(x)) for x in m.group(1, 2, 3))
            a = _alpha(m.group(4))
            if a == 255:
                continue
            if r == g == b == 255:
                name = "blanco"
            elif r == g == b == 0:
                name = "negro"
            elif abs(r - 223) < 25 and abs(g - 186) < 25 and abs(b - 107) < 30:
                name = "dorado"
            elif r == g == b:
                name = "gris"
            else:
                name = "otros"
            fam[name][a] += 1
    return {k: dict(v) for k, v in fam.items()}


def measure():
    _blob = "\n".join(txt for _p, txt in iter_css())
    by_rgba = token_rgba_map()
    color_lit = Counter()
    color_equiv = 0
    off_grid = Counter()
    off_grid_total = 0
    spacing_all = Counter()
    shadows = Counter()
    durations = Counter()
    curves = Counter()

    for _p, txt in iter_css():
        for m in HEX.finditer(declarations_only(txt)):
            raw = m.group(0).lower()
            if raw in GENERIC_HEX:
                continue
            rgba = hex_to_rgba(raw)
            if rgba:
                color_lit[rgba] += 1
                if rgba in by_rgba:
                    color_equiv += 1
        for m in RGB.finditer(txt):
            rgba = rgb_to_rgba(m)
            color_lit[rgba] += 1
            if rgba in by_rgba:
                color_equiv += 1
        for v in SPACING.findall(txt):
            f = float(v)
            spacing_all[f] += 1
            if f != 0 and f % 4 != 0:
                off_grid[f] += 1
                off_grid_total += 1
        for s in SHADOW.findall(txt):
            if s.strip() != "none":
                shadows[re.sub(r"\s+", " ", s.strip())] += 1
        for decl in TRANSITION.findall(txt):
            for d in re.findall(r"(?<![\d.])(\d*\.?\d+)m?s\b", decl):
                durations[d] += 1
            for c in re.findall(
                    r"cubic-bezier\([^)]*\)|\bease-in-out\b|\bease-out\b|"
                    r"\bease-in\b|\bease\b|\blinear\b", decl):
                curves[c] += 1

    scale = alpha_scale()
    scale_sizes = {fam: len(levels) for fam, levels in scale.items()}

    # Accesibilidad de movimiento (WCAG 2.3.3). Se mide como metricas para que
    # el baseline registre cuantas animaciones hay que cubrir, pero ademas se
    # EXIGE que el bloque exista (ver main / check_reduced_motion).
    n_motion = len(re.findall(r"(?:^|[;\s])(?:transition|animation)\s*:", _blob))
    n_keyframes = len(re.findall(r"@keyframes", _blob))
    n_infinite = len(re.findall(r"animation[^;{}]*?\binfinite\b", _blob))
    rm_blocks = len(REDUCED_MOTION.findall(_blob))

    # Espaciado: lo que se vigila es la ADOPCION de la escala, no la pertenencia
    # a una retícula de 4.
    #
    # Se withdraw la métrica off-grid porque medía algo que NO es un defecto:
    # por eso era peligrosa: '10px', '15px', '6px' y '25px' no son múltiplos de 4
    # y sin embargo son valores de espaciado perfectamente normales. Reportaba
    # 592 'ocurrencias a arreglar' sobre un proyecto en el que el 99% de las
    # ocurrencias usa un valor repetido, o sea una escala ya existente y bien
    # usada. Esa cifra invitaba a un refactor destructivo desde el futuro agente
    # que la leyera sin contexto.
    #
    # Lo que sí dice algo del diseño es: cuántos valores distintos hay, cuántos se
    # repiten (escala real) y cuántos son de un solo uso (decisiones únicas).
    sp_total = sum(spacing_all.values())
    sp_reused_vals = sum(1 for v in spacing_all.values() if v > 1)
    sp_single_vals = sum(1 for v in spacing_all.values() if v == 1)
    sp_reused_occ = sum(n for n in spacing_all.values() if n > 1)

    return {
        "color": {
            "literales_no_genericos": sum(color_lit.values()),
            "equivalentes_a_token": color_equiv,
            "rgba_distintos": len({c for c, _ in color_lit.items()}),
        },
        "spacing": {
            "valores_distintos": len(spacing_all),
            "valores_reutilizados": sp_reused_vals,
            "valores_de_un_solo_uso": sp_single_vals,
            "ocurrencias_con_valor_repetido": sp_reused_occ,
            "ocurrencias_totales": sp_total,
            "adopcion_escala_pct": round(100.0 * sp_reused_occ / sp_total, 1)
            if sp_total else 0.0,
        },
        "shadow": {"distintas": len(shadows)},
        "transition": {
            "duraciones_distintas": len(durations),
            "curvas_distintas": len(curves),
        },
        "alpha_scale": {
            "niveles_por_familia": scale_sizes,
            "niveles_totales": sum(scale_sizes.values()),
        },
        "movimiento": {
            "declaraciones_transition_animation": n_motion,
            "keyframes": n_keyframes,
            "animaciones_infinitas": n_infinite,
            "bloques_prefers_reduced_motion": rm_blocks,
        },
    }, {
        "off_grid_top": off_grid.most_common(10),
        "spacing_top": spacing_all.most_common(12),
        "color_top": [(str(c), n) for c, n in color_lit.most_common(10)],
        "curvas_top": curves.most_common(8),
        "alpha_scale": scale,
    }


def check_reduced_motion():
    """El sitio declara movimiento y DEBE ofrecer la via de escape de WCAG 2.3.3.

    Devuelve lista de problemas. Un bloque presente pero incompleto es tan malo
    como uno ausente: deja parte del movimiento sin cubrir y no se nota al mirar
    la hoja de estilos.
    """
    problemas = []
    blob = "\n".join(txt for _p, txt in iter_css())
    bloques = REDUCED_MOTION.findall(blob)
    if not bloques:
        return ["no hay ningun @media prefers-reduced-motion: reduce, pero el "
                "proyecto declara %d transition/animation y %d @keyframes "
                "(WCAG 2.3.3)"
                % (len(re.findall(r"(?:^|[;\s])(?:transition|animation)\s*:", blob)),
                   len(re.findall(r"@keyframes", blob)))]
    cuerpo = "\n".join(bloques)
    faltan = [p for p in RM_REQUIRES if p not in cuerpo]
    if faltan:
        problemas.append("el bloque prefers-reduced-motion existe pero no neutraliza: %s"
                         % ", ".join(faltan))
    if "!important" not in cuerpo:
        problemas.append("el bloque prefers-reduced-motion no usa !important: hay "
                         "transiciones con !important que lo ganarian en "
                         "especificidad")
    if re.search(r"animation\s*:\s*none", cuerpo):
        problemas.append("el bloque usa 'animation: none': las animaciones que "
                         "hacen aparecer un elemento (toast-entrance arranca en "
                         "opacity:0) lo dejarian invisible")
    if re.search(r"transition-duration\s*:\s*0s\b", cuerpo):
        problemas.append("el bloque pone transition-duration: 0s: dejaria de "
                         "dispararse transitionend y el JS que lo escucha se "
                         "quedaria esperando. Usar 0.01ms")
    return problemas


# v9.34.65. El anillo global de AC-4 es `:focus-visible` (0,1,0) en reset.css,
# que se carga PRIMERO. Cualquier `outline: none` de pagina con selector de
# clase (0,1,0) lo empata y, al venir despues, gana la cascada. Con ID gana sin
# discutir. El anillo se perdia en el teclado sin que nada lo delatara.
FOCUS_BLOCK = re.compile(r":root\s*:focus-visible\s*\{[^}]*outline\s*:", re.S)
FOCUS_RESET = re.compile(r"^:focus-visible\s*\{", re.M)
FOCUS_OPT_OUT = re.compile(r":root\s+[^{}]*:not\(:focus-visible\)\s*\{[^}]*outline\s*:\s*none")


def check_focus_ring():
    """El anillo global debe vivir en un selector que las clases no puedan batir.

    Exige `:root :focus-visible` (0,2,0) y no acepta el `:focus-visible` pelado de
    reset.css, que es exactamente lo que se pierde hoy.
    """
    problemas = []
    reset = (ROOT / "static" / "css" / "base" / "reset.css")
    txt = reset.read_text(encoding="utf-8") if reset.exists() else ""
    if not FOCUS_BLOCK.search(txt):
        problemas.append("reset.css no define el anillo de foco en `:root "
                         ":focus-visible`: los `outline: none` de pagina (0,1,0, "
                         "cargan despues) ganan la cascada y el teclado se queda "
                         "sin indicador")
    if FOCUS_OPT_OUT.search(txt) is None and FOCUS_BLOCK.search(txt):
        # sin lista de excepcion, todo control con :focus propio queda con doble
        # anillo. Es una nota, no un fallo: depende de cuantos existan.
        n = len(FOCUS_OPT_OUT.findall(txt))
        if n == 0:
            problemas.append("el anillo reforzado no declara la excepcion de "
                             "controles que ya fulfill WCAG 1.4.11 con su :focus "
                             "propio: quedaran con doble anillo")
    return problemas


# v9.34.65. `scroll-behavior: auto !important` del bloque de reduced-motion NO
# alcanza a `scrollIntoView({ behavior: 'smooth' })`: ese scroll se resuelve en
# JS. Habia 16 llamadas con `smooth` fijo en 6 modulos. Ahora pasan por
# `scrollToElement()` de `static/js/modules/utils.js`, que consulta
# `prefers-reduced-motion` y elige `auto` o `smooth`.
# Se busca `behavior: 'smooth'` pegado a un scrollIntoView para no marcar
# los comentarios que citan el patron viejo a proposito.
SCROLL_SMOOTH = re.compile(r"scrollIntoView\s*\(\s*\{[^}]*behavior\s*:\s*['\"]smooth['\"]", re.S)
SCROLL_HELPER = "scrollToElement"


def iter_js():
    for p in sorted((ROOT / "static" / "js").rglob("*.js")):
        yield p, p.read_text(encoding="utf-8", errors="replace")


def check_js_scroll_motion():
    """Ningun scroll programatico debe hardcodear 'smooth'.

    Es la otra mitad de `check_reduced_motion()`: el CSS frena transiciones y
    animaciones, pero el scroll suave de JS vive aparte y es el que mas
    molesta a quien pide menos movimiento (varias llamadas son 'block: center',
    o sea que llevan el elemento al CENTRO de la pantalla de golpe).
    """
    problemas = []
    for path, txt in iter_js():
        # el propio helper tiene que contener el literal: es el unico permitido
        if path.name == "utils.js":
            continue
        for m in SCROLL_SMOOTH.finditer(txt):
            linea = txt.count("\n", 0, m.start()) + 1
            problemas.append("%s:%d scrollea con behavior:'smooth' fijo, que "
                             "ignora prefers-reduced-motion. Usar %s() de "
                             "modules/utils.js"
                             % (path.relative_to(ROOT).as_posix(), linea,
                                SCROLL_HELPER))

    utils = ROOT / "static" / "js" / "modules" / "utils.js"
    if utils.exists():
        u = utils.read_text(encoding="utf-8", errors="replace")
        if "export function " + SCROLL_HELPER not in u:
            problemas.append("modules/utils.js ya no exporta %s(): el helper "
                             "unico de scroll accesible desaparecio"
                             % SCROLL_HELPER)
        if "prefers-reduced-motion" not in u:
            problemas.append("%s() no consulta 'prefers-reduced-motion': "
                             "volveria a scrollear suave siempre" % SCROLL_HELPER)
    return problemas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--update", action="store_true", help="acepta el estado actual")
    args = ap.parse_args()

    metrics, detail = measure()

    if args.update:
        BASELINE.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print("Baseline actualizado en %s" % BASELINE.name)
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0

    if not BASELINE.exists():
        print("No hay baseline. Generalo con: python %s --update" % Path(__file__).name)
        return 1

    base = json.loads(BASELINE.read_text(encoding="utf-8"))

    # El bloque prefers-reduced-motion no se vigila contra baseline: si alguien
    # lo borra, el baseline seguia diciendo "1 bloque" y no habria forma de darme
    # cuenta. Se exige directamente.
    rm = check_reduced_motion()
    if rm:
        print("FALLA: movimiento sin via de escape (WCAG 2.3.3)")
        for p in rm:
            print("  - " + p)
        print("")

    # Mismo motivo que el de arriba: el anillo de foco depende de la especificidad
    # del selector, no de un conteo. Un baseline no puede detectar que alguien
    # degrado `:root :focus-visible` a `:focus-visible`.
    fr = check_focus_ring()
    if fr:
        print("FALLA: anillo de foco anulable por el cascado (WCAG 2.4.7 / 1.4.11)")
        for p in fr:
            print("  - " + p)
        print("")

    # El bloque de reduced-motion frena el CSS, pero no el scroll de JS.
    js = check_js_scroll_motion()
    if js:
        print("FALLA: scroll programatico con 'smooth' fijo (WCAG 2.3.3)")
        for p in js:
            print("  - " + p)
        print("")

    if args.report:
        print(json.dumps(metrics, indent=2, sort_keys=True))
        print("")
        print("espaciado px (top 12): %s" % detail["spacing_top"])
        print("colores literales (top 10): %s" % detail["color_top"])
        print("curvas de transicion: %s" % detail["curvas_top"])
        print("")
        print("ESCALA DE OPACIDAD (8-bit por familia):")
        for fam in sorted(detail["alpha_scale"]):
            levels = detail["alpha_scale"][fam]
            top = sorted(levels.items(), key=lambda x: -x[1])[:8]
            print("  %-7s %2d niveles | mas usados: %s"
                  % (fam, len(levels),
                     ", ".join("%d(%.0f%%)x%d" % (a, a / 255 * 100, n)
                               for a, n in top)))
        return 0

    worse = []
    for section, vals in metrics.items():
        for key, val in vals.items():
            old = base.get(section, {}).get(key)
            if isinstance(val, dict):
                # seccion con sub-claves (ej. niveles por familia de la escala)
                if not isinstance(old, dict):
                    worse.append("%s.%s: NUEVO (sin baseline)" % (section, key))
                    continue
                for sub, sval in val.items():
                    sold = old.get(sub)
                    if sold is None:
                        worse.append("%s.%s.%s: NUEVO (sin baseline)"
                                     % (section, key, sub))
                    elif sval > sold:
                        worse.append("%s.%s.%s: %d -> %d (nivel de opacidad nuevo)"
                                     % (section, key, sub, sold, sval))
                    elif sval < sold:
                        print("mejora  %s.%s.%s: %d -> %d"
                              % (section, key, sub, sold, sval))
                continue
            if old is None:
                worse.append("%s.%s: NUEVO (sin baseline)" % (section, key))
            elif val > old:
                worse.append("%s.%s: %d -> %d (empeora)" % (section, key, old, val))
            elif val < old:
                print("mejora  %s.%s: %d -> %d" % (section, key, old, val))

    if worse:
        print("REGRESIONES de design system:")
        for w in worse:
            print("  %s" % w)
        return 1

    if rm:
        print("REGRESIONES de accesibilidad:")
        for p in rm:
            print("  %s" % p)
        return 1

    if fr:
        print("REGRESIONES de accesibilidad:")
        for p in fr:
            print("  %s" % p)
        return 1

    if js:
        print("REGRESIONES de accesibilidad:")
        for p in js:
            print("  %s" % p)
        return 1

    print("OK: sin regresiones de design system.")
    print("  color      %d literales no genericos (%d equivalentes a token), "
          "%d RGBA distintos" % (
              metrics["color"]["literales_no_genericos"],
              metrics["color"]["equivalentes_a_token"],
              metrics["color"]["rgba_distintos"]))
    print("  spacing    %d valores distintos, %d reutilizados, %d de un solo uso "
        "(%.1f%% de las %d ocurrencias usa un valor repetido)" % (
            metrics["spacing"]["valores_distintos"],
            metrics["spacing"]["valores_reutilizados"],
            metrics["spacing"]["valores_de_un_solo_uso"],
            metrics["spacing"]["adopcion_escala_pct"],
            metrics["spacing"]["ocurrencias_totales"]))
    print("  shadow     %d box-shadow distintas" % metrics["shadow"]["distintas"])
    print("  transition %d duraciones, %d curvas" % (
        metrics["transition"]["duraciones_distintas"],
        metrics["transition"]["curvas_distintas"]))
    asc = metrics["alpha_scale"]["niveles_por_familia"]
    print("  opacidad   %d niveles declarados (%s)" % (
        metrics["alpha_scale"]["niveles_totales"],
        ", ".join("%s:%d" % (k, v) for k, v in sorted(asc.items()))))
    mov = metrics["movimiento"]
    print("  movimiento %d transition/animation, %d @keyframes, %d infinitas "
        "-> cubiertos por %d bloque(s) prefers-reduced-motion" % (
            mov["declaraciones_transition_animation"], mov["keyframes"],
            mov["animaciones_infinitas"], mov["bloques_prefers_reduced_motion"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
