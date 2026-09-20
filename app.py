import os
import json
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, send_file

from generar_carnet import generar_carnet, PLANTILLAS, GRADOS_TEXTO

app = Flask(__name__)

REGISTRO_PATH = "registro_generaciones.json"
DIAS_LIMITE = 30
IES_VALIDAS = set(PLANTILLAS.keys())
SECCIONES_VALIDAS = set(chr(c) for c in range(ord("A"), ord("Z") + 1))
GRADOS_VALIDOS = set(GRADOS_TEXTO.keys())  # {"1","2","3","4","5"}
TURNOS_VALIDOS = {"MAÑANA", "TARDE"}

# Solo letras (con tildes/Ñ) y espacios; nada de números ni símbolos.
PATRON_SOLO_LETRAS = re.compile(r"^[A-ZÁÉÍÓÚÑÜ ]+$")

# ---------------------------------------------------------------
# Correo de notificación
# ---------------------------------------------------------------
CORREO_DESTINO = "xaberito2011@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

IE_NOMBRES = {
    "mamm": "I.E. Manuel Antonio Mesones Muro",
    "birf": "I.E. Perú BIRF",
}


def _enviar_correo_notificacion(datos):
    """Envía un correo con los datos del carnet generado. Nunca
    interrumpe la generación del carnet si algo falla."""
    if not SMTP_USER or not SMTP_PASS:
        print("[AppCarnetX] SMTP_USER / SMTP_PASS no configurados: "
              "se omite el envío de correo.")
        return

    cuerpo = (
        f"Se generó un nuevo carnet en AppCarnetX.\n\n"
        f"Institución: {IE_NOMBRES.get(datos['ie'], datos['ie'])}\n"
        f"DNI: {datos['dni']}\n"
        f"Apellidos: {datos['apellido']}\n"
        f"Nombres: {datos['nombre']}\n"
        f"Grado: {GRADOS_TEXTO.get(datos['grado'], datos['grado'])}\n"
        f"Sección: {datos['seccion']}\n"
        f"Turno: {datos['turno']}\n\n"
        f"Mensaje / razón indicada por la persona:\n{datos.get('razon', '')}\n\n"
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    msg = MIMEText(cuerpo, _charset="utf-8")
    msg["Subject"] = f"AppCarnetX - Nuevo carnet generado ({datos['dni']})"
    msg["From"] = SMTP_USER
    msg["To"] = CORREO_DESTINO

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [CORREO_DESTINO], msg.as_string())
    except Exception as e:
        # No se debe romper la generación del carnet por un error de correo.
        print(f"[AppCarnetX] No se pudo enviar el correo de notificación: {e}")


# ---------------------------------------------------------------
# Registro simple de generaciones (para la regla de 30 días)
# ---------------------------------------------------------------

def _cargar_registro():
    if os.path.exists(REGISTRO_PATH):
        with open(REGISTRO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _guardar_registro(registro):
    with open(REGISTRO_PATH, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)


def _puede_generar(dni):
    registro = _cargar_registro()
    ultima = registro.get(dni)
    if not ultima:
        return True, None
    fecha_ultima = datetime.fromisoformat(ultima)
    limite = fecha_ultima + timedelta(days=DIAS_LIMITE)
    if datetime.now() < limite:
        dias_restantes = (limite - datetime.now()).days + 1
        return False, dias_restantes
    return True, None


def _registrar_generacion(dni):
    registro = _cargar_registro()
    registro[dni] = datetime.now().isoformat()
    _guardar_registro(registro)


# ---------------------------------------------------------------
# Validación de los datos que llegan del formulario
# ---------------------------------------------------------------

def _validar(datos):
    errores = []

    if datos.get("ie") not in IES_VALIDAS:
        errores.append("Institución educativa inválida.")

    dni = datos.get("dni", "")
    if not re.fullmatch(r"\d{8}", dni):
        errores.append("El DNI debe tener exactamente 8 dígitos numéricos.")

    apellido = datos.get("apellido", "").strip()
    if not apellido:
        errores.append("El apellido es obligatorio.")
    elif not PATRON_SOLO_LETRAS.match(apellido):
        errores.append("El apellido solo puede contener letras.")

    nombre = datos.get("nombre", "").strip()
    if not nombre:
        errores.append("El nombre es obligatorio.")
    elif not PATRON_SOLO_LETRAS.match(nombre):
        errores.append("El nombre solo puede contener letras.")

    if datos.get("grado") not in GRADOS_VALIDOS:
        errores.append("Grado inválido.")

    if datos.get("seccion") not in SECCIONES_VALIDAS:
        errores.append("Sección inválida.")

    if datos.get("turno") not in TURNOS_VALIDOS:
        errores.append("Turno inválido.")

    if not datos.get("razon", "").strip():
        errores.append("Debes indicar un mensaje o razón.")

    return errores


# ---------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generar", methods=["POST"])
def generar():
    datos = request.get_json(force=True, silent=True) or {}

    # normalizar
    datos["apellido"] = datos.get("apellido", "").strip().upper()
    datos["nombre"] = datos.get("nombre", "").strip().upper()
    datos["dni"] = datos.get("dni", "").strip()
    datos["seccion"] = datos.get("seccion", "").strip().upper()
    datos["grado"] = str(datos.get("grado", "")).strip()

    errores = _validar(datos)
    if errores:
        return jsonify({"ok": False, "errores": errores}), 400

    puede, dias_restantes = _puede_generar(datos["dni"])
    if not puede:
        return jsonify({
            "ok": False,
            "errores": [f"Este DNI ya generó un carnet. Podrá generar otro en {dias_restantes} día(s)."]
        }), 429

    try:
        ruta_pdf = generar_carnet(datos)
    except FileNotFoundError as e:
        return jsonify({"ok": False, "errores": [str(e)]}), 500
    except Exception as e:
        return jsonify({"ok": False, "errores": [f"Error al generar el carnet: {e}"]}), 500

    _registrar_generacion(datos["dni"])
    _enviar_correo_notificacion(datos)

    return send_file(
        ruta_pdf,
        as_attachment=True,
        download_name=os.path.basename(ruta_pdf),
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run()
