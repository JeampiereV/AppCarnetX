import io
import os
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

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
# Rutas de plantillas / fuente
# =================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PLANTILLAS = {
    "mamm": os.path.join(BASE_DIR, "static", "templates", "plantilla_mamm.png"),
    "birf": os.path.join(BASE_DIR, "static", "templates", "plantilla_birf.png"),
}

FUENTE_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf")
CARPETA_SALIDA = os.path.join(BASE_DIR, "salidas")

# Grados
GRADOS_TEXTO = {
    "1": "PRIMERO",
    "2": "SEGUNDO",
    "3": "TERCERO",
    "4": "CUARTO",
    "5": "QUINTO",
}

NIVEL_TEXTO = "SECUNDARIA"


# =================================================================
# Coordenadas (en píxeles) de cada una de las 3 tarjetas de la hoja
# Orden de "textos": codigo, apellidos, nombres, nivel, grado, turno, seccion
# =================================================================

COORDS = [
    (605, 194), (605, 231), (605, 269), (605, 303), (605, 343), (605, 376), (780, 350),
    (605, 495), (605, 533), (605, 569), (605, 609), (605, 647), (605, 679), (780, 654),
    (605, 798), (605, 834), (605, 875), (605, 909), (605, 943), (605, 978), (780, 950),
]

QR_COORDS = [(460, 231), (460, 530), (460, 832)]
BARCODE_COORDS = [(757, 364), (757, 667), (757, 970)]

TAMANO_FUENTE = 12
COLOR_TEXTO = "black"

# Las plantillas miden 1414x2000 px. A 100 dpi (valor típico usado
# a la ligera) la hoja saldría de ~14x20 pulgadas, demasiado grande
# para imprimir en A4. Con ~171 dpi la hoja sale en tamaño A4 real
# (21 x 29.7 cm), que es lo que necesitas para imprimir y cortar.
RESOLUCION_PDF = 171.0


# =================================================================
# Utilidades: QR y código de barras
# =================================================================

def _generar_qr_con_borde(dni, size=130, borde=1, color_borde="gray"):
    """QR del DNI, con un pequeño marco, listo para pegar en la plantilla."""
    if not QRCODE_DISPONIBLE:
        return None
    qr_img = qrcode.make(dni).resize((size, size))
    qr_con_borde = Image.new("RGB", (size + borde * 2, size + borde * 2), color_borde)
    qr_con_borde.paste(qr_img, (borde, borde))
    return qr_con_borde


def _generar_barcode(dni, size=(200, 35)):
    """Código de barras Code128 del DNI, como imagen PIL lista para pegar."""
    if not BARCODE_DISPONIBLE:
        return None
    barcode_obj = barcode.get("code128", dni, writer=ImageWriter())
    barcode_img = barcode_obj.render(writer_options={"module_height": 25, "font_size": 8})
    return barcode_img.resize(size)


# =================================================================
# Composición principal
# =================================================================

def generar_carnet(datos: dict) -> str:
    """
    datos debe tener las claves:
        ie        -> "mamm" o "birf"
        dni       -> str, 8 dígitos
        apellido  -> str (en mayúsculas)
        nombre    -> str (en mayúsculas)
        grado     -> str "1" a "5" (se traduce a PRIMERO..QUINTO)
        seccion   -> str ("A" a "Z")
        turno     -> "MAÑANA" o "TARDE"

    Devuelve la ruta del archivo PDF final generado (con las 3
    tarjetas de la hoja llenas, listas para imprimir y cortar).
    """
    ie = datos["ie"]
    if ie not in PLANTILLAS:
        raise ValueError(f"I.E. desconocida: {ie}")

    ruta_plantilla = PLANTILLAS[ie]
    if not os.path.exists(ruta_plantilla):
        raise FileNotFoundError(
            f"No se encontró la plantilla: {ruta_plantilla}. "
            f"Colócala en static/templates/ con ese nombre exacto."
        )

    plantilla = Image.open(ruta_plantilla).convert("RGB")
    draw = ImageDraw.Draw(plantilla)
    font = ImageFont.truetype(FUENTE_PATH, TAMANO_FUENTE)

    codigo = datos["dni"]
    apellidos = datos["apellido"]
    nombres = datos["nombre"]
    nivel = NIVEL_TEXTO
    grado = GRADOS_TEXTO.get(str(datos["grado"]), str(datos["grado"]))
    turno = datos["turno"]
    seccion = datos["seccion"]

    # las 3 tarjetas de la hoja se llenan con los mismos datos
    textos = [codigo, apellidos, nombres, nivel, grado, turno, seccion] * 3

    for (x, y), texto in zip(COORDS, textos):
        draw.text((x, y), texto, font=font, fill=COLOR_TEXTO)

    qr_img = _generar_qr_con_borde(codigo)
    if qr_img is not None:
        for x, y in QR_COORDS:
            plantilla.paste(qr_img, (x, y))
    else:
        print("[AppCarnetX] Aviso: falta 'pip install qrcode[pil]'. Se omitió el QR.")

    barcode_img = _generar_barcode(codigo)
    if barcode_img is not None:
        for x, y in BARCODE_COORDS:
            plantilla.paste(barcode_img, (x, y))
    else:
        print("[AppCarnetX] Aviso: falta 'pip install python-barcode[images]'. Se omitió el código de barras.")

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    marca_tiempo = datetime.now().strftime("%Y%m%d%H%M%S")
    nombre_archivo = f"carnet_{codigo}_{marca_tiempo}.pdf"
    ruta_salida = os.path.join(CARPETA_SALIDA, nombre_archivo)

    plantilla.save(ruta_salida, format="PDF", resolution=RESOLUCION_PDF)

    return ruta_salida


# =================================================================
# Ejemplo de uso directo (sin backend)
# =================================================================

def main():
    datos_formulario = {
        "ie": "mamm",
        "dni": "12345678",
        "apellido": "PEREZ GOMEZ",
        "nombre": "JUAN CARLOS",
        "grado": "3",
        "seccion": "B",
        "turno": "MAÑANA",
    }
    ruta = generar_carnet(datos_formulario)
    print(f"Carnet generado correctamente en: {ruta}")


if __name__ == "__main__":
    main()
