# -*- coding: utf-8 -*-
"""
generar_carnet.py
-------------------------------------------------------------
Compone los datos capturados en el formulario de AppCarnetX
sobre TU plantilla PDF real (la que subiste: 3 carnets por
hoja, listos para imprimir y recortar). Estampa cada campo,
un código QR y un código de barras (ambos con el DNI) en las
3 tarjetas de la hoja.

INSTALACIÓN (una sola vez, en tu computadora):
    pip install -r requirements.txt

Las coordenadas de abajo ya están calculadas automáticamente a
partir de tus plantillas reales (plantilla_mamm.pdf y
plantilla_perubirf.pdf), leyendo la posición exacta de cada
etiqueta ("Código:", "Apellidos:", etc.) en las 3 tarjetas de
la hoja. Si en algún momento cambias el diseño del PDF, vuelve
a correr:
    python herramientas/ver_coordenadas.py plantillas/plantilla_mamm.pdf
para reubicar los campos.
-------------------------------------------------------------
"""

import os
import io
from datetime import datetime

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

try:
    import qrcode
    QRCODE_DISPONIBLE = True
except ImportError:
    QRCODE_DISPONIBLE = False

try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_DISPONIBLE = True
except ImportError:
    BARCODE_DISPONIBLE = False


# =================================================================
# 1) COLORES DE MARCA (RGB 0-1, para reportlab)
# =================================================================

COLOR_MAMM = (0xB0 / 255, 0x19 / 255, 0x02 / 255)  # #B01902
COLOR_BIRF = (0x00 / 255, 0x07 / 255, 0x4D / 255)  # #00074D


# =================================================================
# 2) COORDENADAS REALES (en puntos PDF, origen abajo-izquierda)
#    Calculadas a partir de tus plantillas. Cada hoja tiene 3
#    tarjetas (slots) idénticas; se llenan las 3 con el mismo
#    alumno para que salgan listas para recortar.
# =================================================================

def _slots_texto():
    """Coordenadas (x, y) de cada campo de texto, por tarjeta (0,1,2)."""
    return [
        {  # tarjeta 1 (arriba)
            "dni":      (281.1, 762.7),
            "apellido": (286.9, 747.2),
            "nombre":   (287.4, 731.7),
            "nivel":    (275.6, 716.1),
            "grado":    (279.1, 700.6),
            "seccion":  (365.5, 696.2),
            "turno":    (278.4, 685.1),
        },
        {  # tarjeta 2 (medio)
            "dni":      (280.7, 635.8),
            "apellido": (286.6, 620.3),
            "nombre":   (287.1, 604.7),
            "nivel":    (275.3, 589.2),
            "grado":    (278.7, 573.7),
            "seccion":  (365.2, 569.2),
            "turno":    (278.0, 558.2),
        },
        {  # tarjeta 3 (abajo)
            "dni":      (281.1, 508.9),
            "apellido": (286.9, 493.3),
            "nombre":   (287.4, 477.8),
            "nivel":    (275.6, 462.3),
            "grado":    (279.1, 446.8),
            "seccion":  (365.5, 442.3),
            "turno":    (278.4, 431.3),
        },
    ]


# QR: se dibuja en el mismo lugar donde va el logo "marca de agua"
# de cada tarjeta (a la derecha). Barra: en la franja libre justo
# debajo del turno, encima de la barra de color "CARNÉ ESCOLAR".
def _slots_qr_barcode(qr_bboxes):
    slots = []
    bar_tops = [670.75, 543.85, 416.95]     # borde superior de cada barra roja/azul
    turno_y = [685.1, 558.2, 431.3]         # línea base del campo "Turno" en cada tarjeta
    for i in range(3):
        x0, y0, x1, y1 = qr_bboxes[i]
        slots.append({
            "qr": {"xy": (x0, y0), "size": (x1 - x0, y1 - y0)},
            "barcode": {
                "xy": (254.6, bar_tops[i] + 1),
                "size": (147, (turno_y[i] - 2) - (bar_tops[i] + 1)),
            },
        })
    return slots


COORDENADAS = {
    "mamm": {
        "plantilla": "plantillas/plantilla_mamm.pdf",
        "color_texto": COLOR_MAMM,
        "font_size": {"apellido": 10, "nombre": 10, "dni": 9, "nivel": 9, "grado": 9, "seccion": 9, "turno": 9},
        "max_width": 90,
        "slots_texto": _slots_texto(),
        "slots_extra": _slots_qr_barcode([
            (373.5, 727.8, 402.0, 764.6),
            (373.1, 600.9, 401.7, 637.7),
            (373.5, 474.0, 402.0, 510.7),
        ]),
    },
    "birf": {
        "plantilla": "plantillas/plantilla_birf.pdf",
        "color_texto": COLOR_BIRF,
        "font_size": {"apellido": 10, "nombre": 10, "dni": 9, "nivel": 9, "grado": 9, "seccion": 9, "turno": 9},
        "max_width": 90,
        "slots_texto": _slots_texto(),
        "slots_extra": _slots_qr_barcode([
            (372.7, 729.6, 402.7, 764.9),
            (372.7, 602.7, 402.7, 638.0),
            (372.7, 475.8, 402.7, 511.1),
        ]),
    },
}

CARPETA_SALIDA = "salidas"
FUENTE = "Helvetica-Bold"  # fuente base de PDF; soporta tildes y Ñ


# =================================================================
# 3) UTILIDADES
# =================================================================

def _ajustar_tamano(c, texto, fuente, tamano_inicial, max_width):
    tamano = tamano_inicial
    while tamano > 6:
        if c.stringWidth(texto, fuente, tamano) <= max_width:
            return tamano
        tamano -= 0.5
    return 6


def _generar_qr_imagereader(dni):
    if not QRCODE_DISPONIBLE:
        return None
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(dni)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _generar_barcode_imagereader(dni):
    """Código de barras Code128 con el DNI, como ImageReader para reportlab."""
    if not BARCODE_DISPONIBLE:
        return None
    writer = ImageWriter()
    writer.set_options({
        "write_text": False,   # sin el número debajo, ya lo mostramos como texto aparte
        "quiet_zone": 1,
        "module_height": 10,
    })
    code = barcode.get("code128", dni, writer=writer)
    buf = io.BytesIO()
    code.write(buf)
    buf.seek(0)
    return ImageReader(buf)


# =================================================================
# 4) COMPOSICIÓN SOBRE EL PDF (llena las 3 tarjetas de la hoja)
# =================================================================

def generar_carnet(datos: dict) -> str:
    """
    datos debe tener las claves:
        ie        -> "mamm" o "birf"
        dni       -> str, 8 dígitos
        apellido  -> str (mayúsculas)
        nombre    -> str (mayúsculas)
        nivel     -> "PRIMARIA" o "SECUNDARIA"
        grado     -> "PRIMERO".."QUINTO"
        seccion   -> "A".."Z"
        turno     -> "MAÑANA" o "TARDE"

    Devuelve la ruta del PDF final (con las 3 tarjetas llenas).
    """
    ie = datos["ie"]
    if ie not in COORDENADAS:
        raise ValueError(f"I.E. desconocida: {ie}")

    cfg = COORDENADAS[ie]
    ruta_plantilla = cfg["plantilla"]

    if not os.path.exists(ruta_plantilla):
        raise FileNotFoundError(
            f"No se encontró la plantilla: {ruta_plantilla}."
        )

    reader = PdfReader(ruta_plantilla)
    pagina = reader.pages[0]
    ancho = float(pagina.mediabox.width)
    alto = float(pagina.mediabox.height)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(ancho, alto))

    campos_texto = {
        "apellido": datos["apellido"],
        "nombre": datos["nombre"],
        "dni": datos["dni"],
        "nivel": datos["nivel"],
        "grado": datos["grado"],
        "seccion": datos["seccion"],
        "turno": datos["turno"],
    }

    qr_img = _generar_qr_imagereader(datos["dni"])
    barcode_img = _generar_barcode_imagereader(datos["dni"])

    for i in range(3):  # las 3 tarjetas de la hoja
        posiciones = cfg["slots_texto"][i]
        extra = cfg["slots_extra"][i]

        for clave, texto in campos_texto.items():
            xy = posiciones[clave]
            tam_base = cfg["font_size"][clave]
            tamano = _ajustar_tamano(c, texto, FUENTE, tam_base, cfg["max_width"])
            c.setFont(FUENTE, tamano)
            c.setFillColorRGB(*cfg["color_texto"])
            c.drawString(xy[0], xy[1], texto)

        # QR (reemplaza el logo "marca de agua" de cada tarjeta)
        if qr_img is not None:
            qxy = extra["qr"]["xy"]
            qsz = extra["qr"]["size"]
            c.drawImage(qr_img, qxy[0], qxy[1], width=qsz[0], height=qsz[1], mask="auto")

        # Código de barras (franja libre bajo "Turno")
        if barcode_img is not None:
            bxy = extra["barcode"]["xy"]
            bsz = extra["barcode"]["size"]
            c.drawImage(barcode_img, bxy[0], bxy[1], width=bsz[0], height=bsz[1], mask="auto")

    c.save()
    buf.seek(0)

    overlay_reader = PdfReader(buf)
    writer = PdfWriter()
    pagina.merge_page(overlay_reader.pages[0])
    writer.add_page(pagina)

    for i in range(1, len(reader.pages)):
        writer.add_page(reader.pages[i])

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    marca_tiempo = datetime.now().strftime("%Y%m%d%H%M%S")
    nombre_archivo = f'carnet_{datos["dni"]}_{marca_tiempo}.pdf'
    ruta_salida = os.path.join(CARPETA_SALIDA, nombre_archivo)

    with open(ruta_salida, "wb") as f:
        writer.write(f)

    return ruta_salida


# =================================================================
# 5) EJEMPLO DE USO DIRECTO (sin backend)
# =================================================================

def main():
    datos_formulario = {
        "ie": "mamm",
        "dni": "12345678",
        "apellido": "PEREZ GOMEZ",
        "nombre": "JUAN CARLOS",
        "nivel": "SECUNDARIA",
        "grado": "TERCERO",
        "seccion": "B",
        "turno": "MAÑANA",
    }
    ruta = generar_carnet(datos_formulario)
    print(f"Carnet generado correctamente en: {ruta}")


if __name__ == "__main__":
    main()
