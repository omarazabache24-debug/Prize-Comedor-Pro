# Sistema Comedor PRIZE - versión mejorada

Incluye mejoras visuales del login y panel interno según la imagen enviada:

- Login moderno con logo PRIZE, panel formal, usuarios demo y onda inferior.
- Dashboard interno con cabecera, menú lateral, pestañas rápidas, panel derecho y tarjetas KPI.
- Logo cargado desde `static/logo.png` con parámetro anti-cache `?v=12`.
- Funciones existentes conservadas: consumos, entregas por DNI, carga masiva Excel, trabajadores, cierre de día y reporte por correo.

## Render
Build Command:
```bash
pip install -r requirements.txt
```
Start Command:
```bash
gunicorn app:app
```

## Usuarios iniciales
- admin / admin123
- rrhh / rrhh123
- comedor / comedor123

## Importante si Render sigue mostrando la pantalla antigua
En Render ejecutar: **Manual Deploy → Clear build cache & deploy**.
También presionar `Ctrl + F5` en el navegador.
