# AppCarnetX — Guía rápida

Sistema completo: el usuario llena el formulario en la web y el
servidor estampa sus datos (QR + código de barras con su DNI)
directamente sobre tu plantilla PDF real, y le entrega el PDF con
las 3 tarjetas de la hoja ya llenas, listas para imprimir y cortar.

Tus 2 plantillas reales y los 2 logos (ya sin fondo) están
incluidos y las coordenadas ya están calculadas a partir de ellos.
No necesitas medir nada para empezar.

## 1. Instalar

```
pip install -r requirements.txt
```

(Si tu sistema lo pide, agrega `--break-system-packages` al final.)

## 2. Ejecutar

```
python app.py
```

Abre `http://localhost:5000` en tu navegador.

## 3. Configurar el envío de correo (opcional pero recomendado)

Cada solicitud se notifica a **xaberito2011@gmail.com**. Para que el
envío funcione de verdad necesitas una cuenta Gmail con una
"contraseña de aplicación" (no tu contraseña normal):

1. Entra a tu cuenta de Google → Seguridad → Verificación en 2 pasos
   (actívala si no la tienes) → "Contraseñas de aplicaciones".
2. Genera una contraseña de aplicación y cópiala.
3. Antes de correr `app.py`, define estas variables de entorno:

```
# Mac/Linux
export SMTP_USER="tu_correo@gmail.com"
export SMTP_PASS="la_contraseña_de_aplicación"

# Windows (PowerShell)
$env:SMTP_USER="tu_correo@gmail.com"
$env:SMTP_PASS="la_contraseña_de_aplicación"
```

Si no configuras esto, el sistema sigue funcionando igual (el
carnet se genera normalmente), solo que no se enviará el correo y
lo vas a ver avisado en la consola.

## Campos del formulario

- Institución Educativa (I.E. Manuel Antonio Mesones Muro / Perú BIRF)
- DNI (8 dígitos)
- Apellido y Nombre (solo letras, mayúsculas automáticas)
- **Nivel** (Primaria / Secundaria) — lo agregué porque tu plantilla
  PDF real tiene ese campo ("Nivel:") y no estaba contemplado antes.
- Grado (Primero a Quinto, en palabras, como en tu plantilla)
- Sección (A-Z)
- Turno (Mañana / Tarde)

## Sobre el QR y el código de barras

Ambos se generan a partir del DNI:
- El **QR** se coloca en el mismo lugar donde tu plantilla ya tenía
  el logo decorativo ("marca de agua") de cada tarjeta.
- El **código de barras** (Code128) se coloca en la franja libre
  justo debajo del campo "Turno".

Si alguna vez agrandas esa zona en tu diseño y quieres un código de
barras más grande (más fácil de escanear), edita el diccionario
`COORDENADAS` en `generar_carnet.py` — ahí está todo comentado.

## Si cambias de plantilla

Si rediseñas el PDF (mueves textos, cambias tamaños, etc.), vuelve a
correr:

```
python herramientas/ver_coordenadas.py plantillas/plantilla_mamm.pdf
```

Esto te genera una imagen con una cuadrícula roja numerada para leer
las nuevas coordenadas, que luego copias en `generar_carnet.py`.

## Notas

- La regla de "1 carnet cada 30 días por DNI" se aplica en el
  servidor, guardando la fecha de la última generación en
  `registro_generaciones.json`.
- El diseño de la interfaz se adapta solo a celular o PC (CSS
  responsive), no hace falta configurar nada aparte.
- Para usar esto en internet (no solo en tu computadora), necesitas
  subir esta carpeta a un servicio de hosting con Python (Render,
  Railway, PythonAnywhere, un VPS, etc.).
