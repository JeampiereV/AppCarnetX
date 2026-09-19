# -*- coding: utf-8 -*-
"""
ver_coordenadas.py
-------------------------------------------------------------
Herramienta de ayuda: dibuja una cuadrícula numerada (cada 50pt)
sobre tu plantilla PDF y la exporta como imagen PNG, para que
puedas leer a simple vista en qué coordenada (x, y) va cada campo
del carnet (apellido, nombre, DNI, grado, sección, turno, QR).

IMPORTANTE sobre el sistema de coordenadas:
  - El origen (0, 0) está en la ESQUINA INFERIOR IZQUIERDA de la hoja.
  - "x" crece hacia la derecha.
  - "y" crece hacia ARRIBA (al revés de una imagen normal).
  - Las unidades son "puntos PDF" (72 puntos = 1 pulgada).

USO:
    python ver_coordenadas.py plantillas/plantilla_mamm.pdf

Esto genera:
    plantillas/plantilla_mamm_grid.pdf   (la plantilla con la cuadrícula roja)
    plantillas/plantilla_mamm_grid-1.png (la misma vista, en imagen)

Abre el PNG, ubica visualmente dónde debe ir cada dato y anota las
coordenadas (x, y) más cercanas. Luego pon esos valores en
generar_carnet.py, dentro del diccionario COORDENADAS.
"""

import sys
import os
import subprocess
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter


def generar_grid(ruta_pdf, paso=50):
    if not os.path.exists(ruta_pdf):
        print(f"No se encontró el archivo: {ruta_pdf}")
        return

    reader = PdfReader(ruta_pdf)
    pagina = reader.pages[0]
    ancho = float(pagina.mediabox.width)
    alto = float(pagina.mediabox.height)

    base, _ = os.path.splitext(ruta_pdf)
    overlay_tmp = base + "_overlay_tmp.pdf"
    salida_pdf = base + "_grid.pdf"

    # 1) Dibujar la cuadrícula en un PDF transparente del mismo tamaño
    c = canvas.Canvas(overlay_tmp, pagesize=(ancho, alto))
    c.setStrokeColorRGB(1, 0, 0)
    c.setFillColorRGB(1, 0, 0)
    c.setFont("Helvetica-Bold", 6)
    c.setLineWidth(0.4)

    x = 0
    while x <= ancho:
        c.line(x, 0, x, alto)
        c.drawString(x + 2, alto - 9, str(int(x)))
        x += paso

    y = 0
    while y <= alto:
        c.line(0, y, ancho, y)
        c.drawString(2, y + 2, str(int(y)))
        y += paso

    c.save()

    # 2) Fusionar la cuadrícula sobre la plantilla real
    overlay_reader = PdfReader(overlay_tmp)
    writer = PdfWriter()
    pagina.merge_page(overlay_reader.pages[0])
    writer.add_page(pagina)

    with open(salida_pdf, "wb") as f:
        writer.write(f)
    os.remove(overlay_tmp)

    # 3) Convertir a PNG para verlo fácilmente (usa poppler / pdftoppm)
    prefijo = base + "_grid"
    try:
        subprocess.run(
            ["pdftoppm", "-png", "-r", "150", salida_pdf, prefijo],
            check=True
        )
        print(f"Cuadrícula generada:\n  - {salida_pdf}\n  - {prefijo}-1.png")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"Cuadrícula generada en PDF: {salida_pdf}")
        print("(No se pudo convertir a PNG automáticamente; ábrelo con cualquier lector de PDF.)")

    print(f"\nTamaño de la hoja: {ancho:.0f} x {alto:.0f} puntos")
    print("Recuerda: el eje Y crece hacia ARRIBA, empezando en la esquina inferior izquierda.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python ver_coordenadas.py ruta_a_tu_plantilla.pdf")
    else:
        generar_grid(sys.argv[1])
