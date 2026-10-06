"""Verificacion objetiva de las capturas: dimensiones, peso y variedad de pixeles."""

import sys
from pathlib import Path

from PIL import Image

RUTA_IMG = Path(__file__).resolve().parents[1] / "assets" / "img"

UMBRAL_MINIMO_KB = 20


def analizar(archivo):
    with Image.open(archivo) as imagen:
        imagen = imagen.convert("RGB")
        ancho, alto = imagen.size
        muestra = imagen.resize((320, max(1, round(320 * alto / ancho))))
        pixeles = list(muestra.get_flattened_data())
        total = len(pixeles)
        unicos = len(set(pixeles))
        varianza = round(sum((r - 128) ** 2 + (g - 128) ** 2 + (b - 128) ** 2
                             for r, g, b in pixeles) / total, 1)
    return {
        "archivo": archivo.name,
        "px": f"{ancho}x{alto}",
        "kb": round(archivo.stat().st_size / 1024),
        "colores_unicos": unicos,
        "varianza": varianza,
    }


def main():
    archivos = sorted(RUTA_IMG.glob("*.png"))
    if not archivos:
        print("No hay capturas generadas.")
        return 1

    print(f"{'archivo':42} {'px':12} {'KB':>7} {'colores':>9} {'varianza':>10}  estado")
    print("-" * 92)
    sospechoso = 0
    for archivo in archivos:
        info = analizar(archivo)
        problemas = []
        if info["kb"] < UMBRAL_MINIMO_KB:
            problemas.append("liviana")
        if info["colores_unicos"] < 25:
            problemas.append("poco contenido")
        if info["varianza"] < 120:
            problemas.append("casi uniforme")
        estado = "OK" if not problemas else "REVISAR: " + ", ".join(problemas)
        sospechoso += bool(problemas)
        print(f"{info['archivo']:42} {info['px']:12} {info['kb']:>7} "
              f"{info['colores_unicos']:>9} {info['varianza']:>10}  {estado}")

    print()
    print(f"Total: {len(archivos)} capturas | a revisar: {sospechoso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())