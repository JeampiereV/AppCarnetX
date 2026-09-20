## Estructura del proyecto

```
carnetx2/
├── app.py                       -> backend Flask (rutas, validación, correo)
├── generar_carnet.py            -> compone el carnet sobre la plantilla (Pillow)
├── requirements.txt
├── templates/
│   └── index.html               -> solo estructura HTML
├── static/
│   ├── css/style.css            -> todos los estilos
│   ├── js/app.js                -> toda la lógica de la interfaz + Formspree
│   ├── img/
│   │   ├── mamm_logo.png        -> escudo I.E. Manuel A. Mesones Muro
│   │   └── birf_logo.png        -> escudo Colegio Perú BIRF
│   └── templates/
│       ├── plantilla_mamm.png   -> plantilla real (1414x2000 px)
│       └── plantilla_birf.png   -> plantilla real (1414x2000 px)
├── fonts/
│   └── DejaVuSans-Bold.ttf      -> fuente usada para escribir sobre el carnet
├── herramientas/
│   └── ver_coordenadas_png.py   -> dibuja una cuadrícula sobre una plantilla PNG
│                                   para recalibrar coordenadas si hace falta
└── salidas/                     -> aquí se guardan los PDFs generados
```

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
