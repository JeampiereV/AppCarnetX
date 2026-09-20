# -*- coding: utf-8 -*-
import sys
import os
from PIL import Image, ImageDraw, ImageFont

PASO = 50


def generar_grid(ruta_png):
    im = Image.open(ruta_png).convert("RGB")
    draw = ImageDraw.Draw(im)
    w, h = im.size

    try:
        font = ImageFont.truetype(
            os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans-Bold.ttf"), 16
        )
    except Exception:
        font = ImageFont.load_default()

    for x in range(0, w, PASO):
        draw.line([(x, 0), (x, h)], fill=(255, 0, 0), width=1)
        draw.text((x + 2, 2), str(x), fill=(255, 0, 0), font=font)

    for y in range(0, h, PASO):
        draw.line([(0, y), (w, y)], fill=(0, 120, 255), width=1)
        draw.text((2, y + 2), str(y), fill=(0, 120, 255), font=font)

    base, ext = os.path.splitext(ruta_png)
    salida = f"{base}_grid.png"
    im.save(salida)
    print(f"Cuadrícula generada: {salida}")
    print(f"Tamaño de la imagen: {w} x {h} px")
    print("Recuerda: el eje Y crece hacia ABAJO (origen arriba a la izquierda).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python herramientas/ver_coordenadas_png.py <ruta_a_la_plantilla.png>")
        sys.exit(1)
    generar_grid(sys.argv[1])
