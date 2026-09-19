# -*- coding: utf-8 -*-
"""
app.py
-------------------------------------------------------------
Backend de AppCarnetX.

- Sirve la interfaz (templates/index.html)
- Recibe los datos del formulario en POST /generar
- Valida todo en el servidor (nunca confíes solo en el navegador)
- Aplica la regla "1 carnet cada 30 días" por DNI
- Llama a generar_carnet.py para estampar los datos + QR + código
  de barras sobre la plantilla PDF real, y devuelve el PDF final.
- Envía una notificación por correo a xaberito2011@gmail.com con
  cada solicitud (datos + mensaje/razón).

EJECUTAR:
    pip install -r requirements.txt
    python app.py
Luego abre: http://localhost:5000

CONFIGURAR EL ENVÍO DE CORREO (ver sección "EMAIL" más abajo):
    Necesitas una cuenta de Gmail con una "Contraseña de aplicación"
    (no tu contraseña normal). Se configuran 2 variables de entorno
    antes de ejecutar app.py:

        Windows (PowerShell):
            $env:SMTP_USER="tu_correo@gmail.com"
            $env:SMTP_PASS="tu_contraseña_de_aplicación"
        Mac/Linux:
            export SMTP_USER="tu_correo@gmail.com"
            export SMTP_PASS="tu_contraseña_de_aplicación"

    Si no configuras estas variables, el sistema sigue funcionando
    normalmente (genera el carnet igual), solo que no podrá enviar
    el correo y lo avisará en la consola.
"""

import os
import json
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, send_file

from generar_carnet import generar_carnet, COORDENADAS

app = Flask(__name__)

REGISTRO_PATH = "registro_generaciones.json"
DIAS_LIMITE = 30
IES_VALIDAS = set(COORDENADAS.keys())
SECCIONES_VALIDAS = set(chr(c) for c in range(ord("A"), ord("Z") + 1))
NIVELES_VALIDOS = {"PRIMARIA", "SECUNDARIA"}
GRADOS_VALIDOS = {"PRIMERO", "SEGUNDO", "TERCERO", "CUARTO", "QUINTO"}
TURNOS_VALIDOS = {"MAÑANA", "TARDE"}

# ---------------------------------------------------------------
# EMAIL: a dónde se notifican las solicitudes
# ---------------------------------------------------------------
DESTINATARIO_NOTIFICACIONES = "xaberito2011@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")  # tu correo Gmail
SMTP_PASS = os.environ.get("SMTP_PASS")  # tu contraseña de aplicación


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
# Notificación por correo
# ---------------------------------------------------------------

def _enviar_notificacion_email(datos):
    """Envía un correo con el resumen de la solicitud. Si no hay
    credenciales configuradas, solo lo avisa por consola y sigue."""
    if not SMTP_USER or not SMTP_PASS:
        print("[AVISO] SMTP_USER / SMTP_PASS no configurados: no se envió el correo.")
        return

    cuerpo = (
        f"Nueva solicitud de carnet generada en AppCarnetX\n\n"
        f"I.E.: {datos.get('ie')}\n"
        f"DNI: {datos.get('dni')}\n"
        f"Apellido: {datos.get('apellido')}\n"
        f"Nombre: {datos.get('nombre')}\n"
        f"Nivel: {datos.get('nivel')}\n"
        f"Grado: {datos.get('grado')}\n"
        f"Sección: {datos.get('seccion')}\n"
        f"Turno: {datos.get('turno')}\n\n"
        f"Mensaje / razón:\n{datos.get('razon')}\n"
    )

    msg = MIMEText(cuerpo, "plain", "utf-8")
    msg["Subject"] = f"AppCarnetX - Nueva solicitud ({datos.get('dni')})"
    msg["From"] = SMTP_USER
    msg["To"] = DESTINATARIO_NOTIFICACIONES

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [DESTINATARIO_NOTIFICACIONES], msg.as_string())
    except Exception as e:
        # Un fallo al enviar el correo NUNCA debe impedir que el
        # usuario reciba su carnet ya generado.
        print(f"[AVISO] No se pudo enviar el correo de notificación: {e}")


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

    if not re.fullmatch(r"[A-ZÁÉÍÓÚÑ ]+", datos.get("apellido", "")):
        errores.append("El apellido solo puede contener letras.")

    if not re.fullmatch(r"[A-ZÁÉÍÓÚÑ ]+", datos.get("nombre", "")):
        errores.append("El nombre solo puede contener letras.")

    if datos.get("nivel") not in NIVELES_VALIDOS:
        errores.append("Nivel inválido.")

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
    datos["nivel"] = datos.get("nivel", "").strip().upper()
    datos["grado"] = datos.get("grado", "").strip().upper()
    datos["turno"] = datos.get("turno", "").strip().upper()

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
    _enviar_notificacion_email(datos)

    return send_file(
        ruta_pdf,
        as_attachment=True,
        download_name=os.path.basename(ruta_pdf),
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
